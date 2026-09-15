"""
test_exporter — CLI 命令字符串与 JSON 配置导出正确性。

核心验证：exporter 与 generator 共用 to_cli_args，保证一致性。
"""

import json
import pytest
from figtreekit_studio.core.params import ParamSpec, to_cli_args
from figtreekit_studio.core.exporter import export_cli, export_config, export_config_dict


class TestExportCli:
    def test_basic_command(self):
        """基本命令应包含 figtreekit 和 java 部分。"""
        p = ParamSpec(layout="polar", tip_labels="hide", render_format="PNG", width=1600, height=1000)
        cmd = export_cli(p)
        assert "figtreekit" in cmd
        assert "input.tre" in cmd
        assert "output.nex" in cmd
        assert "java -jar" in cmd
        assert "output.png" in cmd

    def test_no_extra_args(self):
        """无额外参数时命令仍有效。"""
        p = ParamSpec()
        cmd = export_cli(p)
        assert "figtreekit" in cmd
        assert "java -jar" in cmd

    def test_format_extension(self):
        """不同格式应使用不同扩展名。"""
        for fmt, ext in [("PNG", ".png"), ("PDF", ".pdf"), ("SVG", ".svg"), ("JPEG", ".jpg")]:
            p = ParamSpec(render_format=fmt)
            cmd = export_cli(p)
            assert f"output{ext}" in cmd, f"Format {fmt} should use {ext}"

    def test_dimensions_in_command(self):
        """宽高应出现在 java 命令中。"""
        p = ParamSpec(render_format="PNG", width=2400, height=1200)
        cmd = export_cli(p)
        assert "2400" in cmd
        assert "1200" in cmd

    def test_cli_args_match(self):
        """导出的 CLI 参数与 to_cli_args 完全一致。"""
        p = ParamSpec(
            layout="polar", tip_labels="hide", bg_color="#FAFAFA",
            branch_width=2.0, auto_color_rank="phylum", scale_axis="show",
        )
        cli_args = to_cli_args(p)
        cmd = export_cli(p)
        for arg in cli_args:
            assert arg in cmd, f"CLI arg '{arg}' not found in exported command"


class TestExportConfig:
    def test_basic_config(self):
        p = ParamSpec(layout="polar", tip_labels="hide", bg_color="#FAFAFA")
        d = export_config_dict(p)
        assert d["layout.layoutType"] == "POLAR"
        assert d["tipLabels.isShown"] is False
        assert d["appearance.backgroundColour"] == "#FAFAFA"

    def test_config_json_valid(self):
        p = ParamSpec(layout="radial", tip_labels="show", scale_axis="show")
        json_str = export_config(p)
        d = json.loads(json_str)
        assert d["layout.layoutType"] == "RADIAL"
        assert d["tipLabels.isShown"] is True
        assert d["scaleAxis.isShown"] is True

    def test_default_config(self):
        """默认参数应包含 layout 和 tipLabels。"""
        p = ParamSpec()
        d = export_config_dict(p)
        assert "layout.layoutType" in d
        assert "tipLabels.isShown" in d


class TestConsistency:
    """exporter 与 generator 共用 to_cli_args，保证无漂移。"""

    def test_no_drift(self):
        """导出的 CLI 参数列表应与 to_cli_args 完全一致。"""
        p = ParamSpec(
            layout="polar",
            tip_labels="hide",
            align_tip_labels=True,
            bg_color="#FAFAFA",
            branch_width=2.5,
            foreground_color="#000000",
            font_name="Arial",
            font_size=12,
            font_style="bold",
            label_color="#FF0000",
            auto_color_rank="phylum",
            collapse_rank="class",
            collapse_style="cartoon",
            scale_axis="show",
            scale_bar="show",
            angular_range=270,
            root_angle=90,
            curvature=5,
            node_labels="show",
            node_display_attribute="height",
            branch_labels="show",
            branch_display_attribute="length",
            legend="show",
            legend_position="top",
        )
        args = to_cli_args(p)
        cmd = export_cli(p)
        for a in args:
            assert a in cmd, f"Arg '{a}' missing from exported command"
