"""
exporter — 参数 → CLI 命令字符串 + JSON 配置

保证导出命令与 generator 实际执行 **完全一致**（共用 params.to_cli_args，
避免漂移）。
"""

from __future__ import annotations

import json
from typing import Any

from figtreekit_studio.core.params import ParamSpec, to_cli_args, to_config_dict


def _quote_arg(arg: str) -> str:
    """Shell-quote one argument of the exported command line.

    Hex colours begin with ``#``, which a POSIX shell treats as the start of a
    comment when it begins a word: an unquoted ``--background-color #FAFAFA``
    silently drops the value and the command fails.  Any argument that a shell
    would not take verbatim is quoted, so the exported record is runnable as
    printed.
    """
    import shlex
    text = str(arg)
    if text and all(ch.isalnum() or ch in "@%+=:,./-_" for ch in text):
        return text
    return shlex.quote(text)


def export_cli(params: ParamSpec | dict[str, Any]) -> str:
    """
    生成等效的 figtreekit CLI 命令字符串（可脱离 GUI 直接复制运行）。

    与 generator 共用 ``params.to_cli_args``，因此命令与界面实际执行的参数
    逐项一致；需要 shell 转义的参数值（如 ``#RRGGBB`` 颜色）会被加引号，
    使导出的命令可以原样复制运行。

    格式与 README 示例一致：
    .. code-block:: bash

        python -m figtreekit input.tre -o output.nex --force \\
          --layout polar --tip-labels-hide ... \\
          && java -jar figtree_patched.jar -graphic PNG -width 1600 -height 1000 output.nex output.png
    """
    if isinstance(params, dict):
        params = ParamSpec.from_dict(params)

    cli_args = to_cli_args(params)

    # 固定使用 python 作为解释器名（冻结应用中 sys.executable 不是 python）
    # 用户需本机已安装 figtreekit 才能直接运行导出的命令
    py_name = "python"

    # figtreekit 部分
    parts = [f"{py_name} -m figtreekit input.tre -o output.nex --force"]
    if cli_args:
        parts.append("  " + " ".join(_quote_arg(a) for a in cli_args))

    # 渲染部分：走 figtreekit --render，而不是裸 java -jar。
    # 核心的渲染入口除了调用补丁 JAR，还负责全局 appearance 的后处理
    # （FigTree 1.4.4 的 headless 渲染器忽略这些颜色），因此只有经
    # figtreekit --render 复现，所得图像才与界面预览逐像素一致。
    fmt = (params.render_format or "PNG").upper()
    w = params.width or 1600
    h = params.height or 1000
    ext = {"PNG": ".png", "PDF": ".pdf", "SVG": ".svg", "JPEG": ".jpg"}.get(fmt, ".png")
    render_args = [
        "--render", f"output{ext}",
        "--render-format", fmt,
        "--render-width", str(w),
        "--render-height", str(h),
    ]
    if to_cli_args(params):
        parts.append("  " + " ".join(_quote_arg(a) for a in render_args))
    else:
        parts.insert(1, "  " + " ".join(_quote_arg(a) for a in render_args))

    return " \\\n".join(parts)


def export_config(params: ParamSpec | dict[str, Any]) -> str:
    """返回格式化的 JSON 配置字符串（对应 figtreekit --config）。"""
    return json.dumps(to_config_dict(params), ensure_ascii=False, indent=2)


def export_config_dict(params: ParamSpec | dict[str, Any]) -> dict[str, Any]:
    """返回 JSON 配置字典。"""
    return to_config_dict(params)
