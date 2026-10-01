"""desktop.py（pywebview 原生窗口层）的回归测试。

此前该模块覆盖率 0%，而它正是应用的默认入口。这里只覆盖真正有后果的分支，
不追求行覆盖率数字：

  * `run_desktop` **不能吞掉**非回环绑定的拒绝。`resolve_bind_host` 在
    `--host 0.0.0.0` 且未显式 opt-in 时会 raise；`run_desktop` 在 try 块
    之前调用它，所以这个 ValueError 必须一路冒泡给调用方。若哪天有人为了
    "更健壮"而在 run_desktop 外层加一个宽 except，原本拦住全网卡监听的
    防线就会静默失效 —— 那是本项目历史上有过的真实缺陷。
  * `finally` 中的 `server.shutdown()/server_close()` 必须在
    `webview.start()` 抛异常时也执行，否则每次启动失败都会泄漏一个线程。
  * pywebview 不可用时返回 False，让调用方能回退到浏览器模式。
"""

from __future__ import annotations

import socket
import sys
import types

import pytest

from figtreekit_studio import desktop


class _FakeWindow:
    def __init__(self, result):
        self._result = result
        self.dialog_args = None

    def create_file_dialog(self, kind):
        self.dialog_args = kind
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


def _install_fake_webview(monkeypatch, *, window=None, windows=None,
                         start_result=None, start_error=None):
    """注入一个假的 webview 模块。desktop.py 的 import 都在函数内部，故可替换。"""
    mod = types.ModuleType("webview")
    mod.FOLDER_DIALOG = 2
    mod.active_window = lambda: window
    mod.windows = windows if windows is not None else ([window] if window else [])
    if start_error is not None:
        def _start():
            raise start_error
        mod.start = _start
    else:
        mod.start = lambda: start_result
    mod.create_window = lambda *a, **k: window
    monkeypatch.setitem(sys.modules, "webview", mod)
    return mod


class _FakeServer:
    def __init__(self):
        self.events = []

    def serve_forever(self):  # 会在守护线程里被调用
        self.events.append("serve_forever")

    def shutdown(self):
        self.events.append("shutdown")

    def server_close(self):
        self.events.append("server_close")


@pytest.fixture
def fake_server(monkeypatch):
    """替换 create_server，避免测试真的监听端口。"""
    server = _FakeServer()
    import figtreekit_studio.server as srv
    monkeypatch.setattr(srv, "create_server", lambda *a, **k: server)
    return server


class TestFreePort:
    def test_returns_a_bindable_port(self):
        port = desktop.free_port()
        assert 1 <= port <= 65535
        # 该端口此刻应可绑定（free_port 关闭了 socket，故此断言不应 flaky）
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", port))

    def test_two_calls_differ(self):
        assert desktop.free_port() != desktop.free_port()


class TestSelectFolder:
    def test_returns_first_of_list(self, monkeypatch):
        _install_fake_webview(monkeypatch, window=_FakeWindow(["/tmp/picked"]))
        assert desktop._StudioApi().select_folder() == "/tmp/picked"

    def test_returns_plain_string(self, monkeypatch):
        _install_fake_webview(monkeypatch, window=_FakeWindow("/tmp/one"))
        assert desktop._StudioApi().select_folder() == "/tmp/one"

    def test_empty_list_yields_empty_string(self, monkeypatch):
        _install_fake_webview(monkeypatch, window=_FakeWindow([]))
        assert desktop._StudioApi().select_folder() == ""

    def test_none_yields_empty_string(self, monkeypatch):
        _install_fake_webview(monkeypatch, window=_FakeWindow(None))
        assert desktop._StudioApi().select_folder() == ""

    def test_no_window_yields_empty_string(self, monkeypatch):
        _install_fake_webview(monkeypatch, window=None, windows=[])
        assert desktop._StudioApi().select_folder() == ""

    def test_dialog_exception_is_swallowed(self, monkeypatch):
        """对话框失败不得把异常抛给前端 JS —— 前端拿不到返回值。"""
        _install_fake_webview(monkeypatch, window=_FakeWindow(RuntimeError("boom")))
        assert desktop._StudioApi().select_folder() == ""

    def test_falls_back_to_windows_list(self, monkeypatch):
        """active_window() 为 None 时应退到 windows[0]。"""
        win = _FakeWindow(["/tmp/fallback"])
        mod = _install_fake_webview(monkeypatch, window=win)
        mod.active_window = lambda: None
        assert desktop._StudioApi().select_folder() == "/tmp/fallback"

    def test_passes_folder_dialog_kind(self, monkeypatch):
        win = _FakeWindow(["/tmp/x"])
        _install_fake_webview(monkeypatch, window=win)
        desktop._StudioApi().select_folder()
        assert win.dialog_args == 2  # webview.FOLDER_DIALOG


class TestRunDesktop:
    def test_returns_false_when_pywebview_missing(self, monkeypatch, fake_server):
        """前端可回退到浏览器模式的关键契约。"""
        monkeypatch.setitem(sys.modules, "webview", None)
        assert desktop.run_desktop() is False

    def test_normal_exit_returns_true_and_closes_server(self, monkeypatch, fake_server):
        _install_fake_webview(monkeypatch, window=_FakeWindow(None))
        assert desktop.run_desktop() is True
        assert "shutdown" in fake_server.events
        assert "server_close" in fake_server.events

    def test_start_failure_returns_false_but_still_closes_server(
        self, monkeypatch, fake_server
    ):
        """webview.start() 抛异常时必须回退，且 finally 仍要释放服务。"""
        _install_fake_webview(monkeypatch, window=_FakeWindow(None),
                              start_error=RuntimeError("no display"))
        assert desktop.run_desktop() is False
        assert "shutdown" in fake_server.events, "服务未关闭：会泄漏线程与端口"
        assert "server_close" in fake_server.events

    @pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.10"])
    def test_refuses_non_loopback_without_opt_in(self, monkeypatch, fake_server, host):
        """关键防线：绝不能因为想"更健壮"而吞掉这个拒绝。"""
        _install_fake_webview(monkeypatch, window=_FakeWindow(None))
        with pytest.raises(ValueError) as exc:
            desktop.run_desktop(host=host, allow_remote_bind=False)
        assert "--allow-remote-bind" in str(exc.value) or "authentication" in str(exc.value)
        assert fake_server.events == [], "拒绝之后不应启动任何服务"

    def test_non_loopback_allowed_when_deliberate(self, monkeypatch, fake_server):
        _install_fake_webview(monkeypatch, window=_FakeWindow(None))
        assert desktop.run_desktop(host="0.0.0.0", allow_remote_bind=True) is True

    def test_explicit_port_is_respected(self, monkeypatch, fake_server):
        seen = {}

        import figtreekit_studio.server as srv
        monkeypatch.setattr(
            srv, "create_server",
            lambda h, p, **k: (seen.update(host=h, port=p), fake_server)[1],
        )
        _install_fake_webview(monkeypatch, window=_FakeWindow(None))
        desktop.run_desktop(port=45999)
        assert seen["port"] == 45999
