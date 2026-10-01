"""冻结包路径（`sys.frozen`）的回归测试。

`generate_nex` 在普通解释器下走 subprocess，只有在 PyInstaller 产出的 .app 里
`sys.executable` 指向应用自身、无法 `python -m figtreekit`，才改走
`_run_figtreekit_inprocess()` 在当前进程内 runpy 执行 figtreekit CLI。

也就是说：**这条路径的回归只会在打包之后才暴露**，表现为"打好的 .app 双击没
反应"，而打包一次要几分钟、定位极难。0.1.2 的 CHANGELOG 里已经出现过一次同类
事故（hiddenimports 没收全，冻结包 ModuleNotFoundError）。所以这里直接对
`_run_figtreekit_inprocess` 做单元测试，并重点锁两个会让整个应用永久卡死的点：

  * `sys.argv` 是进程级全局状态，必须在**任何**退出路径（含异常与超时）上还原；
  * `_inprocess_lock` 必须释放。一旦泄漏，第二次生成请求会永久阻塞。
"""

from __future__ import annotations

import runpy
import sys
import time

import pytest

from figtreekit_studio.core import generator
from figtreekit_studio.core.params import ParamSpec


@pytest.fixture
def frozen(monkeypatch):
    """让代码走冻结分支。"""
    monkeypatch.setattr(sys, "frozen", True, raising=False)


@pytest.fixture(autouse=True)
def _clean_inprocess_lock():
    """每个用例前后强制清掉进程级 `_inprocess_lock`。

    这不是可有可无的卫生问题。`_run_figtreekit_inprocess` 用的是**阻塞式**
    `acquire()`，所以一旦某个用例泄漏了锁，后续每一个调用它的用例都会永久
    阻塞 —— 在 CI 上表现为整个 job 挂到 `timeout-minutes` 才红，日志里没有任何
    可读线索（实测过：注入锁泄漏后套件直接挂死，而不是给出失败）。

    先清场，就能把「锁没释放」变成一条普通的断言失败。
    """
    if generator._inprocess_lock.locked():
        generator._inprocess_lock.release()
    yield
    if generator._inprocess_lock.locked():
        generator._inprocess_lock.release()


class TestInProcessRunner:
    def test_success_returns_zero(self, monkeypatch, frozen):
        seen = {}

        def _fake_run_module(name, run_name=None):
            seen["name"] = name
            seen["argv"] = list(sys.argv)
            print("hello from figtreekit")

        monkeypatch.setattr(runpy, "run_module", _fake_run_module)
        code, log, timed_out = generator._run_figtreekit_inprocess(["a.tre", "-o", "b.nex"])
        assert (code, timed_out) == (0, False)
        assert seen["name"] == "figtreekit"
        assert "hello from figtreekit" in log

    def test_argv_is_injected_and_restored(self, monkeypatch, frozen):
        before = list(sys.argv)
        monkeypatch.setattr(runpy, "run_module", lambda *a, **k: None)
        generator._run_figtreekit_inprocess(["x.tre", 3, True])
        assert sys.argv == before, "sys.argv 未还原：会污染后续所有参数解析"

    def test_argv_restored_even_when_run_raises(self, monkeypatch, frozen):
        before = list(sys.argv)

        def _boom(*a, **k):
            raise RuntimeError("figtreekit 内部炸了")

        monkeypatch.setattr(runpy, "run_module", _boom)
        code, log, _ = generator._run_figtreekit_inprocess(["x.tre"])
        assert code == 1
        assert "figtreekit 内部炸了" in log
        assert sys.argv == before, "异常路径未还原 sys.argv"

    def test_stdout_is_captured_not_printed(self, monkeypatch, frozen, capsys):
        monkeypatch.setattr(
            runpy, "run_module",
            lambda *a, **k: print("这段不应泄漏到控制台"),
        )
        _, log, _ = generator._run_figtreekit_inprocess(["x.tre"])
        assert "这段不应泄漏到控制台" in log
        assert "这段不应泄漏到控制台" not in capsys.readouterr().out

    @pytest.mark.parametrize(
        ("exit_code", "expected"),
        [(0, 0), (2, 2), (None, 0), ("错误信息", 1)],
    )
    def test_system_exit_code_conversion(self, monkeypatch, frozen, exit_code, expected):
        """SystemExit.code 可能是 int / None / str，三者都要映射正确。"""

        def _exit(*a, **k):
            raise SystemExit(exit_code)

        monkeypatch.setattr(runpy, "run_module", _exit)
        code, _, _ = generator._run_figtreekit_inprocess(["x.tre"])
        assert code == expected

    def test_falls_back_to_cli_main_when_package_main_missing(self, monkeypatch, frozen):
        """冻结包可能未收录包级 __main__，此时必须回退到 figtreekit._cli.main。"""
        called = {}

        def _no_main(*a, **k):
            raise ImportError("No module named figtreekit.__main__")

        monkeypatch.setattr(runpy, "run_module", _no_main)
        import figtreekit._cli as ftk_cli
        monkeypatch.setattr(ftk_cli, "main", lambda *a, **k: called.setdefault("hit", True))

        code, _, _ = generator._run_figtreekit_inprocess(["x.tre"])
        assert called.get("hit") is True, "未回退到 figtreekit._cli.main"
        assert code == 0

    def test_timeout_is_reported(self, monkeypatch, frozen):
        monkeypatch.setattr(runpy, "run_module", lambda *a, **k: time.sleep(5))
        code, log, timed_out = generator._run_figtreekit_inprocess(["x.tre"], timeout=1)
        assert timed_out is True
        assert code == 1
        assert "超时" in log

    def test_lock_is_released_on_success(self, monkeypatch, frozen):
        monkeypatch.setattr(runpy, "run_module", lambda *a, **k: None)
        generator._run_figtreekit_inprocess(["x.tre"])
        acquired = generator._inprocess_lock.acquire(blocking=False)
        assert acquired, "锁未释放：第二次生成请求会永久阻塞"
        generator._inprocess_lock.release()

    def test_lock_is_released_on_timeout(self, monkeypatch, frozen):
        """最危险的一种泄漏：超时后若不释放，.app 之后每次生成都卡死。"""
        monkeypatch.setattr(runpy, "run_module", lambda *a, **k: time.sleep(5))
        generator._run_figtreekit_inprocess(["x.tre"], timeout=1)
        acquired = generator._inprocess_lock.acquire(blocking=False)
        assert acquired, "超时后锁未释放"
        generator._inprocess_lock.release()

    def test_lock_is_released_on_exception(self, monkeypatch, frozen):
        def _boom(*a, **k):
            raise RuntimeError("boom")

        monkeypatch.setattr(runpy, "run_module", _boom)
        generator._run_figtreekit_inprocess(["x.tre"])
        acquired = generator._inprocess_lock.acquire(blocking=False)
        assert acquired, "异常后锁未释放"
        generator._inprocess_lock.release()


class TestGenerateNexInFrozenMode:
    """generate_nex 的冻结分支：结果判定与产物落盘。"""

    def _params(self, tmp_path):
        return ParamSpec(
            tree_text="((A:0.1,B:0.2):0.3,(C:0.4,D:0.5):0.6);",
            layout="rectilinear", tip_labels="show",
            work_dir=str(tmp_path),
        )

    def test_success_writes_nex(self, monkeypatch, frozen, tmp_path):
        def _run(args, timeout=0):
            # 模拟 figtreekit 写出 .nex
            out = args[args.index("-o") + 1]
            with open(out, "w", encoding="utf-8") as f:
                f.write("#NEXUS\n")
            return 0, "ok", False

        monkeypatch.setattr(generator, "_run_figtreekit_inprocess", _run)
        r = generator.generate_nex(self._params(tmp_path))
        assert r.ok, r.error
        assert r.nex_path.endswith("output.nex")

    def test_timeout_becomes_figtreekit_timeout(self, monkeypatch, frozen, tmp_path):
        monkeypatch.setattr(
            generator, "_run_figtreekit_inprocess",
            lambda args, timeout=0: (1, "figtreekit 执行超时（>120s）", True),
        )
        r = generator.generate_nex(self._params(tmp_path))
        assert r.ok is False
        assert r.error_key == "figtreekit_timeout"

    def test_nonzero_exit_becomes_figtreekit_failed(self, monkeypatch, frozen, tmp_path):
        monkeypatch.setattr(
            generator, "_run_figtreekit_inprocess",
            lambda args, timeout=0: (3, "参数错误", False),
        )
        r = generator.generate_nex(self._params(tmp_path))
        assert r.ok is False
        assert r.error_key == "figtreekit_failed"
        assert "参数错误" in r.error

    def test_zero_exit_without_nex_file_is_still_a_failure(
        self, monkeypatch, frozen, tmp_path
    ):
        """rc=0 但没产出 .nex 也必须判失败——否则下游渲染会拿到空路径。"""
        monkeypatch.setattr(
            generator, "_run_figtreekit_inprocess", lambda args, timeout=0: (0, "", False)
        )
        r = generator.generate_nex(self._params(tmp_path))
        assert r.ok is False
        assert r.error_key == "figtreekit_failed"

    def test_frozen_path_does_not_shell_out_to_sys_executable(
        self, monkeypatch, frozen, tmp_path
    ):
        """冻结应用里 sys.executable 是应用自身，绝不能再拿它当解释器。"""
        import subprocess as sp

        def _forbid(*a, **k):
            raise AssertionError("冻结模式下不应调用 subprocess")

        monkeypatch.setattr(sp, "run", _forbid)
        monkeypatch.setattr(generator, "_run_figtreekit_inprocess",
                            lambda args, timeout=0: (1, "", False))
        r = generator.generate_nex(self._params(tmp_path))
        assert r.ok is False
