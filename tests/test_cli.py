"""cli.py（控制台入口）的回归测试。

此前覆盖率 14%。重点锁两件事：

1. `--allow-remote-bind` 在**每一条**代码路径上都真正透传到 serve()/run_desktop()。
   曾有一处 `--browser` 分支漏传，用户显式给了 `--host 0.0.0.0 --allow-remote-bind`
   仍被拒绝，而报错信息恰恰在叫用户补上这个他已经补了的参数 —— 一个自相矛盾
   且无法自查的失败。
2. 三种模式（桌面 / 浏览器 / 无窗口）与旧参数别名 `--no-browser` 的分派与
   端口默认值。
"""

from __future__ import annotations

import pytest

from figtreekit_studio import cli


class _ImmediateThread:
    """让 CLI 内部的 daemon 线程同步执行，避免测试里真的开浏览器。"""

    def __init__(self, target=None, daemon=None, **kwargs):
        self.target = target

    def start(self):
        if self.target:
            self.target()


@pytest.fixture
def harness(monkeypatch):
    """拦截所有出口，记录参数。"""
    calls = {"serve": [], "desktop": [], "browser": []}

    import figtreekit_studio.server as srv
    import figtreekit_studio.desktop as desk

    monkeypatch.setattr(srv, "serve",
                        lambda **kw: calls["serve"].append(kw))
    monkeypatch.setattr(desk, "run_desktop",
                        lambda **kw: calls["desktop"].append(kw) or True)
    monkeypatch.setattr(cli.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(cli.time, "sleep", lambda _s: None)
    monkeypatch.setattr(cli.webbrowser, "open",
                        lambda url: calls["browser"].append(url))
    return calls


class TestAllowRemoteIsAlwaysForwarded:
    """回归重点：--allow-remote-bind 在每条路径上都必须生效。"""

    def test_headless_forwards_allow_remote(self, harness):
        cli.main(["--no-window", "--host", "0.0.0.0", "--allow-remote-bind"])
        assert harness["serve"] == [
            {"host": "0.0.0.0", "port": 8777, "allow_remote": True}
        ]

    def test_browser_forwards_allow_remote(self, harness):
        """这条曾因漏传而失效：用户给了开关仍被 serve 拒绝。"""
        cli.main(["--browser", "--host", "0.0.0.0", "--allow-remote-bind"])
        assert harness["serve"] == [
            {"host": "0.0.0.0", "port": 8777, "allow_remote": True}
        ]

    def test_desktop_forwards_allow_remote(self, harness):
        cli.main(["--host", "0.0.0.0", "--allow-remote-bind"])
        assert harness["desktop"] == [
            {"host": "0.0.0.0", "allow_remote_bind": True, "port": None}
        ]

    def test_browser_forwards_allow_remote_false_when_not_requested(self, harness):
        cli.main(["--browser", "--host", "0.0.0.0"])
        assert harness["serve"][0]["allow_remote"] is False


class TestModeDispatch:
    def test_default_is_desktop(self, harness):
        cli.main([])
        assert len(harness["desktop"]) == 1
        assert harness["serve"] == []

    def test_no_window_does_not_open_desktop(self, harness):
        cli.main(["--no-window"])
        assert harness["desktop"] == []
        assert len(harness["serve"]) == 1

    def test_legacy_no_browser_is_alias_for_no_window(self, harness):
        """`--no-browser` 是兼容旧参数，行为必须与 `--no-window` 一致。"""
        cli.main(["--no-browser"])
        assert harness["desktop"] == []
        assert len(harness["serve"]) == 1

    def test_browser_does_not_open_desktop(self, harness):
        cli.main(["--browser"])
        assert harness["desktop"] == []
        assert len(harness["serve"]) == 1

    def test_browser_opens_the_same_url_it_serves(self, harness):
        cli.main(["--browser", "--host", "127.0.0.1", "--port", "9123"])
        assert harness["browser"] == ["http://127.0.0.1:9123"]
        assert harness["serve"][0]["port"] == 9123

    def test_explicit_port_is_used_in_headless_mode(self, harness):
        cli.main(["--no-window", "--port", "9001"])
        assert harness["serve"][0]["port"] == 9001

    def test_default_port_is_8777_outside_desktop_mode(self, harness):
        cli.main(["--no-window"])
        assert harness["serve"][0]["port"] == 8777

    def test_desktop_port_defaults_to_none_so_it_can_autopick(self, harness):
        """桌面模式默认 None 端口，由 free_port() 选；不能落到 8777。"""
        cli.main([])
        assert harness["desktop"][0]["port"] is None


class TestDesktopFallback:
    def test_falls_back_to_browser_when_pywebview_missing(self, monkeypatch, harness):
        import figtreekit_studio.desktop as desk
        # 仍然记录参数，只把返回值改成 False（pywebview 不可用）
        monkeypatch.setattr(desk, "run_desktop",
                            lambda **kw: harness["desktop"].append(kw) or False)
        cli.main(["--host", "127.0.0.1", "--port", "9002"])
        assert harness["desktop"] == [{"host": "127.0.0.1", "allow_remote_bind": False,
                                      "port": 9002}]
        assert harness["serve"] == [{"host": "127.0.0.1", "port": 9002,
                                     "allow_remote": False}]
        assert harness["browser"] == ["http://127.0.0.1:9002"]


class TestSmokeTestDispatch:
    @pytest.mark.parametrize("code", [0, 2, 3])
    def test_smoke_test_exits_with_the_returned_code(self, monkeypatch, harness, code):
        monkeypatch.setattr(cli, "_smoke_test", lambda: code)
        with pytest.raises(SystemExit) as exc:
            cli.main(["--smoke-test"])
        assert exc.value.code == code

    def test_smoke_test_short_circuits_every_other_mode(self, monkeypatch, harness):
        """--smoke-test 必须先于模式分派，否则会在 CI 里真的开窗口。"""
        monkeypatch.setattr(cli, "_smoke_test", lambda: 0)
        with pytest.raises(SystemExit):
            cli.main(["--smoke-test"])
        assert harness["serve"] == []
        assert harness["desktop"] == []
        assert harness["browser"] == []
