"""测试前置条件与 strict 模式。

背景：本仓库有四处「前置条件不满足就 ``pytest.skip``」的写法（渲染 fixture、
JAR 一致性校验、figtreekit schema 校验）。这些 skip 在本地开发时是合理的便利，
但一旦被环境变化触发，就会让整套测试**静默变绿而实际什么都没验**——
最坏的一种失败模式：`test_renderer.py` 的两个 fixture 若因生成器故障而 skip，
整个渲染测试套件（9 个用例）会全部消失而 CI 依然通过。

因此引入 strict 模式：
  * 本地/CI 常规运行：保持 skip 语义，不打扰开发者。
  * CI（FIGTREEKIT_STUDIO_STRICT_TESTS=1）：同样的前置条件不满足时**判失败**，
    并且整个 session 只要出现过任何 skip 就整体失败。

这样「没测到」永远不会被误读成「通过了」。
"""

from __future__ import annotations

import os

import pytest

STRICT_ENV = "FIGTREEKIT_STUDIO_STRICT_TESTS"

# strict 模式下收集到的跳过节点；pytest_sessionfinish 收尾时统一裁决。
_STRICT_SKIPS: list[str] = []


def strict_mode() -> bool:
    """当前是否处于 strict 模式（CI 强制开启）。"""
    return os.environ.get(STRICT_ENV) == "1"


def require(condition: bool, reason: str) -> None:
    """断言测试前置条件。

    condition 为真时直接返回；否则 strict 模式下判失败，本地开发下跳过。
    新增需要外部依赖（真实 JAR / java / 核心库）的测试时，请一律走这里，
    不要直接调用 ``pytest.skip``。
    """
    if condition:
        return
    if strict_mode():
        pytest.fail(f"前置条件不满足：{reason}（strict 模式不允许静默跳过）")
    pytest.skip(reason)


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    # 只在 call 阶段判定，避免 collection 阶段的 skip 被重复计数。
    if report.when == "call" and report.outcome == "skipped":
        _STRICT_SKIPS.append(report.nodeid)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """strict 模式下，任何 skip 都让整次运行失败。"""
    if not strict_mode() or exitstatus != 0 or not _STRICT_SKIPS:
        return
    session.exitstatus = 1
    print(  # noqa: T201 - 故意走 stdout，pytest 会原样带进 CI 日志
        "\n[strict] 本次运行存在被跳过的用例，整次运行按失败处理：",
    )
    for nodeid in _STRICT_SKIPS:
        print(f"  - {nodeid}")  # noqa: T201
    print(
        "[strict] 若确属预期跳过，请在测试里改用 require(..., reason) 并说明"
        "为什么该前置条件在 CI 中必然满足。\n",
    )
