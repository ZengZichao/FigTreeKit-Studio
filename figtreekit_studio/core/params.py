"""
参数 schema 与 UI→figtreekit 映射。

本模块是 generator 与 exporter 的 **单一事实来源**：
``to_cli_args(params)`` 同时被 generator（实际执行）和 exporter（导出命令）调用，
确保"GUI 所见 = 命令行所得"。

参数 schema 参考 figtreekit v1.1.2 CLI ``--help``。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


# --------------------------------------------------------------------------- #
# 枚举常量（与 figtreekit CLI 保持一致）
# --------------------------------------------------------------------------- #
LAYOUTS = ("rectilinear", "polar", "radial")
TAXONOMY_RANKS = ("domain", "phylum", "class", "order", "family", "genus", "species")
COLLAPSE_STYLES = ("collapse", "cartoon")
RENDER_FORMATS = ("PNG", "PDF", "SVG", "JPEG")
FONT_STYLES = {"plain": 0, "bold": 1, "italic": 2, "bold-italic": 3}


# --------------------------------------------------------------------------- #
# 参数 schema
# --------------------------------------------------------------------------- #
@dataclass
class ParamSpec:
    """UI 参数的完整定义：字段名、类型、默认值、合法枚举。"""

    # --- 输入 ---
    tree_text: str = ""
    tree_file: str = ""

    # --- 工作目录 ---
    work_dir: str = ""  # 必填，用于存放渲染中间文件

    # --- 布局 ---
    layout: str = "rectilinear"
    tip_labels: str = "show"  # "show" | "hide"
    align_tip_labels: bool = False

    # --- 外观 ---
    bg_color: str = ""  # #RRGGBB 或空
    branch_width: float = 0.0  # 0 = 不设置
    foreground_color: str = ""
    font_name: str = ""
    font_size: float = 0.0
    font_style: str = ""  # plain|bold|italic|bold-italic
    label_color: str = ""

    # --- 分类学 ---
    auto_color_rank: str = ""  # 空 = 不配色
    collapse_rank: str = ""  # 空 = 不折叠
    collapse_style: str = "collapse"
    taxonomy_mapping_file: str = ""

    # --- 刻度轴 ---
    scale_axis: str = ""  # "show" | "" (关)
    scale_bar: str = ""  # "show" | "" (关)

    # --- 极坐标 ---
    angular_range: float = 0.0  # 0 = 不设置
    root_angle: float = 0.0  # 0 = 不设置

    # --- 矩形树 ---
    curvature: int = -1  # -1 = 不设置

    # --- 节点/分支标签 ---
    node_labels: str = ""  # "show" | "" (关)
    node_display_attribute: str = ""
    branch_labels: str = ""  # "show" | "" (关)
    branch_display_attribute: str = ""

    # --- 图例 ---
    legend: str = ""  # "show" | "" (关)
    legend_position: str = "bottom"

    # --- 渲染输出 ---
    render_format: str = "PNG"
    width: int = 1600
    height: int = 1000

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> "ParamSpec":
        if not d:
            return cls()
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)


# --------------------------------------------------------------------------- #
# params → figtreekit CLI 参数列表（generator 和 exporter 共用）
# --------------------------------------------------------------------------- #
def to_cli_args(p: ParamSpec | dict) -> list[str]:
    """
    把 UI 参数映射为 figtreekit CLI 参数列表（不含 input 和 -o）。

    generator 和 exporter 都调用此函数，保证一致性。
    """
    if isinstance(p, dict):
        p = ParamSpec.from_dict(p)

    args: list[str] = []

    # --- 布局 ---
    if p.layout:
        args += ["--layout", p.layout]
    if p.tip_labels == "hide":
        args += ["--tip-labels-hide"]
    elif p.tip_labels == "show":
        args += ["--tip-labels-show"]
    # figtreekit 默认 alignTipLabels=True，所以未勾选时必须显式关闭
    if p.align_tip_labels:
        args += ["--align-tip-labels"]
    else:
        layout = p.layout or "rectilinear"
        args += ["--set", f"{layout}Layout.alignTipLabels=false"]

    # --- 外观 ---
    if p.bg_color:
        args += ["--background-color", p.bg_color]
    if p.branch_width > 0:
        args += ["--branch-width", str(p.branch_width)]
    if p.foreground_color:
        args += ["--foreground-color", p.foreground_color]
    if p.font_name:
        args += ["--font-name", p.font_name]
    if p.font_size > 0:
        args += ["--font-size", str(p.font_size)]
    if p.font_style and p.font_style in FONT_STYLES:
        args += ["--font-style", str(FONT_STYLES[p.font_style])]
    if p.label_color:
        args += ["--label-color", p.label_color]

    # --- 分类学 ---
    if p.auto_color_rank:
        args += ["--auto-color", p.auto_color_rank]
    if p.collapse_rank:
        args += ["--collapse-rank", p.collapse_rank]
        style = p.collapse_style if p.collapse_style in COLLAPSE_STYLES else "collapse"
        args += ["--collapse-style", style]
    if p.taxonomy_mapping_file:
        args += ["--taxonomy-mapping-file", p.taxonomy_mapping_file]

    # --- 刻度轴 ---
    if p.scale_axis == "show":
        args += ["--scale-axis-show"]
    elif p.scale_axis == "hide":
        args += ["--scale-axis-hide"]
    if p.scale_bar == "show":
        args += ["--scale-bar-show"]
    elif p.scale_bar == "hide":
        args += ["--scale-bar-hide"]

    # --- 极坐标 ---
    if p.angular_range > 0:
        args += ["--angular-range", str(p.angular_range)]
    if p.root_angle > 0:
        args += ["--root-angle", str(p.root_angle)]

    # --- 矩形树 ---
    if p.curvature is not None and p.curvature >= 0:
        args += ["--curvature", str(p.curvature)]

    # --- 节点标签 ---
    if p.node_labels == "show":
        args += ["--node-labels-show"]
        if p.node_display_attribute:
            args += ["--node-display-attribute", p.node_display_attribute]
    elif p.node_labels == "hide":
        args += ["--node-labels-hide"]

    # --- 分支标签 ---
    if p.branch_labels == "show":
        args += ["--branch-labels-show"]
        if p.branch_display_attribute:
            args += ["--branch-display-attribute", p.branch_display_attribute]
    elif p.branch_labels == "hide":
        args += ["--branch-labels-hide"]

    # --- 图例 ---
    if p.legend == "show":
        args += ["--legend-show"]
        if p.legend_position:
            args += ["--legend-position", p.legend_position]

    return args


# --------------------------------------------------------------------------- #
# params → FigTree JSON 配置（对应 figtreekit --config 用法）
# --------------------------------------------------------------------------- #
def to_config_dict(p: ParamSpec | dict) -> dict[str, Any]:
    """
    把 UI 参数映射为 FigTree JSON 配置字典。

    此字典可直接作为 ``figtreekit --config config.json`` 的输入。
    与 to_cli_args 保持语义一致。
    """
    if isinstance(p, dict):
        p = ParamSpec.from_dict(p)

    config: dict[str, Any] = {}

    if p.layout:
        config["layout.layoutType"] = p.layout.upper()
    if p.tip_labels == "hide":
        config["tipLabels.isShown"] = False
    elif p.tip_labels == "show":
        config["tipLabels.isShown"] = True
    # alignTipLabels 在 figtreekit 中默认为 True，所以未勾选时必须显式关闭
    layout_key = {
        "rectilinear": "rectilinearLayout.alignTipLabels",
        "polar": "polarLayout.alignTipLabels",
        "radial": "radialLayout.alignTipLabels",
    }.get(p.layout or "rectilinear", "rectilinearLayout.alignTipLabels")
    config[layout_key] = bool(p.align_tip_labels)
    if p.bg_color:
        config["appearance.backgroundColour"] = p.bg_color
    if p.branch_width > 0:
        config["appearance.branchLineWidth"] = p.branch_width
    if p.foreground_color:
        config["appearance.foregroundColour"] = p.foreground_color
    if p.font_name:
        config["tipLabels.fontName"] = p.font_name
    if p.font_size > 0:
        config["tipLabels.fontSize"] = int(round(p.font_size))
    if p.font_style and p.font_style in FONT_STYLES:
        config["tipLabels.fontStyle"] = FONT_STYLES[p.font_style]
    if p.label_color:
        config["tipLabels.colorAttribute"] = p.label_color
    # 显隐开关显式写出两个分支，不依赖 figtreekit 默认值
    if p.scale_axis == "show":
        config["scaleAxis.isShown"] = True
    else:
        config["scaleAxis.isShown"] = False
    if p.scale_bar == "show":
        config["scaleBar.isShown"] = True
    else:
        config["scaleBar.isShown"] = False
    if p.angular_range > 0:
        config["polarLayout.angularRange"] = p.angular_range
    if p.root_angle > 0:
        config["polarLayout.rootAngle"] = p.root_angle
    if p.curvature is not None and p.curvature >= 0:
        config["rectilinearLayout.curvature"] = p.curvature
    # 显隐开关显式写出两个分支，与 CLI 路径语义同构
    if p.node_labels == "show":
        config["nodeLabels.isShown"] = True
        if p.node_display_attribute:
            config["nodeLabels.displayAttribute"] = p.node_display_attribute
    elif p.node_labels == "hide":
        config["nodeLabels.isShown"] = False
    if p.branch_labels == "show":
        config["branchLabels.isShown"] = True
        if p.branch_display_attribute:
            config["branchLabels.displayAttribute"] = p.branch_display_attribute
    elif p.branch_labels == "hide":
        config["branchLabels.isShown"] = False
    if p.legend == "show":
        config["legend.isShown"] = True
        if p.legend_position:
            config["legend.position"] = p.legend_position.upper()

    return config


def to_config_json(p: ParamSpec | dict) -> str:
    """返回格式化的 JSON 配置字符串。"""
    return json.dumps(to_config_dict(p), ensure_ascii=False, indent=2)
