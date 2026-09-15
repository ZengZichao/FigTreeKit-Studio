"""
generator — 参数 → figtreekit CLI → .nex

把 UI 参数映射为 figtreekit 调用：写树到临时文件 → 运行
``python -m figtreekit <tree> -o <out>.nex [选项]`` → 返回 .nex 路径或错误。

- 树文件内容由前端读入 ``tree_text`` 后提交，服务端不读取本地路径，
  ``tree_file`` 仅作为来源元数据。
- 冻结打包（PyInstaller/py2app）时 sys.executable 不再是 Python 解释器，
  此时改为在进程内运行 figtreekit CLI（runpy + argv 注入），逻辑与 CLI 一致。
"""

from __future__ import annotations

import contextlib
import io
import os
import runpy
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from typing import Any

from figtreekit_studio.core.params import ParamSpec, to_cli_args

# 冻结模式进程内执行串行化锁：防止并发生成请求互相覆盖 sys.argv / stdout
_inprocess_lock = threading.Lock()


@dataclass
class GenResult:
    """generate_nex 返回值。"""
    ok: bool
    nex_path: str = ""
    tree_path: str = ""
    work_dir: str = ""
    cli_args: list[str] | None = None
    error: str = ""
    error_key: str = ""     # 前端 i18n 错误码（见 app.js I18N.err.*）
    error_detail: str = ""  # 可选技术细节（stderr 尾部等）
    log: str = ""


# 参数以 list 方式传递给 subprocess.run / runpy，不经过 shell 解析，故无需转义/白名单。


def _run_figtreekit_inprocess(args: list[str], timeout: int = 0) -> tuple[int, str, bool]:
    """
    冻结打包（PyInstaller/py2app）时在进程内运行 figtreekit CLI。

    sys.executable 在冻结应用里指向应用自身而非 Python 解释器，
    无法用 subprocess 调 `python -m figtreekit`，因此通过 runpy
    在当前进程内执行 figtreekit.__main__（argv 注入 + 输出捕获）。
    使用模块级锁串行化，防止并发请求互相覆盖 sys.argv / stdout。
    返回 (returncode, log, timed_out)。
    """
    import concurrent.futures

    def _run_impl() -> tuple[int, str]:
        old_argv = sys.argv
        buf_out, buf_err = io.StringIO(), io.StringIO()
        code = 0
        try:
            sys.argv = ["figtreekit"] + [str(a) for a in args]
            with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
                try:
                    runpy.run_module("figtreekit", run_name="__main__")
                except ImportError:
                    # 冻结环境可能未收录包级 __main__（PyInstaller 默认不打包它），
                    # 回退为直调 CLI 模块的 main()，行为与 `python -m figtreekit` 一致
                    from figtreekit._cli import main as _ftk_cli_main
                    _ftk_cli_main()
        except SystemExit as e:  # CLI 主动退出
            code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
        except BaseException as e:  # noqa: BLE001 — 把任何异常转成生成失败
            code = 1
            buf_err.write(f"{type(e).__name__}: {e}\n")
        finally:
            sys.argv = old_argv
        return code, buf_out.getvalue() + buf_err.getvalue()

    # 串行化：同一时间只有一个请求在进程内执行 figtreekit
    _inprocess_lock.acquire()
    ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        fut = ex.submit(_run_impl)
        if timeout > 0:
            try:
                code, log = fut.result(timeout=timeout)
                return code, log, False
            except concurrent.futures.TimeoutError:
                return 1, f"figtreekit 执行超时（>{timeout}s）", True
        else:
            code, log = fut.result()
            return code, log, False
    finally:
        ex.shutdown(wait=False)
        _inprocess_lock.release()


def generate_nex(params: ParamSpec | dict[str, Any], *, timeout: int = 120) -> GenResult:
    """
    根据 UI 参数调用 figtreekit CLI 生成 .nex 文件。

    参数:
        params: ParamSpec 对象或字典。
        timeout: figtreekit 执行超时秒数。

    返回:
        GenResult，成功时 nex_path 指向生成的 .nex 文件。
    """
    if isinstance(params, dict):
        params = ParamSpec.from_dict(params)

    # 1) 获取树文本（内容由前端读入后提交；服务端不读取本地文件路径）
    tree_text = (params.tree_text or "").strip()
    if not tree_text:
        return GenResult(ok=False, error="请提供树文件或 Newick 文本",
                         error_key="no_tree")

    # 2) 写树到临时文件
    work_dir = tempfile.mkdtemp(prefix="ftk_studio_")
    tree_path = os.path.join(work_dir, "input.tre")
    nex_path = os.path.join(work_dir, "output.nex")
    with open(tree_path, "w", encoding="utf-8") as f:
        f.write(tree_text + "\n")

    # 3) 拼 CLI 并执行（复用 params.to_cli_args，保证与 exporter 一致）
    cli_args = to_cli_args(params)
    py = sys.executable
    cmd = [py, "-m", "figtreekit", tree_path, "-o", nex_path, "--force"] + cli_args

    # 冻结打包（.app）：sys.executable 是应用自身而非 Python 解释器，
    # 无法经 subprocess 调 `python -m figtreekit`，改走进程内等价执行
    if getattr(sys, "frozen", False):
        _rc, _log, _to = _run_figtreekit_inprocess(cmd[3:], timeout=timeout)
        if _to:
            return GenResult(
                ok=False, work_dir=work_dir, tree_path=tree_path,
                error=f"figtreekit 执行超时（>{timeout}s，树可能过大）",
                error_key="figtreekit_timeout", error_detail=f">{timeout}s",
            )
        if _rc != 0 or not os.path.exists(nex_path):
            tail = _log[-1500:] if _log else "(no output)"
            return GenResult(
                ok=False, work_dir=work_dir, tree_path=tree_path,
                error=f"figtreekit 生成失败:\n{tail}",
                error_key="figtreekit_failed", error_detail=tail, log=_log,
            )
        return GenResult(
            ok=True, nex_path=nex_path, tree_path=tree_path,
            work_dir=work_dir, cli_args=cli_args, log=_log,
        )

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return GenResult(
            ok=False, work_dir=work_dir, tree_path=tree_path,
            error=f"figtreekit 执行超时（>{timeout}s，树可能过大）",
            error_key="figtreekit_timeout", error_detail=f">{timeout}s",
        )

    log = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0 or not os.path.exists(nex_path):
        tail = log[-1500:] if log else "(no output)"
        return GenResult(
            ok=False, work_dir=work_dir, tree_path=tree_path,
            error=f"figtreekit 生成失败:\n{tail}",
            error_key="figtreekit_failed", error_detail=tail, log=log,
        )

    return GenResult(
        ok=True, nex_path=nex_path, tree_path=tree_path,
        work_dir=work_dir, cli_args=cli_args, log=log,
    )
