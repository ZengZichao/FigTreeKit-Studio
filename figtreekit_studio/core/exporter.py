"""
exporter — 参数 → CLI 命令字符串 + JSON 配置

保证导出命令与 generator 实际执行 **完全一致**（共用 params.to_cli_args，
避免漂移）。
"""

from __future__ import annotations

import json
from typing import Any

from figtreekit_studio.core.params import ParamSpec, to_cli_args, to_config_dict


def export_cli(params: ParamSpec | dict[str, Any]) -> str:
    """
    生成等效的 figtreekit CLI 命令字符串（可脱离 GUI 直接复制运行）。

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
        parts.append("  " + " ".join(cli_args))

    # java 渲染部分
    fmt = (params.render_format or "PNG").upper()
    w = params.width or 1600
    h = params.height or 1000
    ext = {"PNG": ".png", "PDF": ".pdf", "SVG": ".svg", "JPEG": ".jpg"}.get(fmt, ".png")
    render_part = (
        f"  && java -jar figtree_patched.jar -graphic {fmt} "
        f"-width {w} -height {h} output.nex output{ext}"
    )
    parts.append(render_part)

    return " \\\n".join(parts)


def export_config(params: ParamSpec | dict[str, Any]) -> str:
    """返回格式化的 JSON 配置字符串（对应 figtreekit --config）。"""
    return json.dumps(to_config_dict(params), ensure_ascii=False, indent=2)


def export_config_dict(params: ParamSpec | dict[str, Any]) -> dict[str, Any]:
    """返回 JSON 配置字典。"""
    return to_config_dict(params)
