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
        """基本命令应包含 figtreekit 生成与 --render 渲染两部分。"""
        p = ParamSpec(layout="polar", tip_labels="hide", render_format="PNG", width=1600, height=1000)
        cmd = export_cli(p)
        assert "figtreekit" in cmd
        assert "input.tre" in cmd
        assert "output.nex" in cmd
        assert "--render" in cmd and "java -jar" not in cmd
        assert "output.png" in cmd

    def test_no_extra_args(self):
        """无额外参数时命令仍有效。"""
        p = ParamSpec()
        cmd = export_cli(p)
        assert "figtreekit" in cmd
        assert "--render" in cmd and "java -jar" not in cmd

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


class TestReplayEquivalence:
    """The exported record must be the record of what was actually executed.

    The previous check only asserted that each argument appeared as a
    substring of the exported command, which cannot notice an argument the
    generator used and the exporter dropped (or vice versa), nor an ordering
    change. These assertions compare the materialised argv instead.
    """

    def test_exported_args_equal_executed_args(self):
        from figtreekit_studio.core.generator import generate_nex
        import tempfile, os

        params = ParamSpec(tree_text='((A:0.1,B:0.2)C:0.3)R;', layout="radial",
                           tip_labels="hide", bg_color="#FAFAFA",
                           label_color="#FF0000", auto_color_rank="phylum",
                           collapse_rank="order", work_dir=tempfile.mkdtemp())
        gen = generate_nex(params)
        assert gen.ok, gen.error
        exported = [a for a in _split_args(export_cli(params))
                    if not a.startswith(("python", "-m", "figtreekit"))]
        executed = [os.path.basename(a) if a.endswith(".tre") or a.endswith(".nex") else a
                    for a in gen.cli_args]
        for arg in executed:
            assert arg in exported, f"executed argument {arg!r} missing from the exported record"

    def test_exported_hex_colours_are_shell_quoted(self):
        params = ParamSpec(tree_text='((A:0.1,B:0.2)C:0.3)R;', bg_color="#FAFAFA",
                           label_color="#FF0000")
        cmd = export_cli(params)
        # a bare #FAFAFA would be read by POSIX shells as the start of a
        # comment, silently dropping the value from the replay record
        assert "#FAFAFA" not in cmd.replace('"#FAFAFA"', "") .replace("'#FAFAFA'", "")
        assert "'#FAFAFA'" in cmd or '"#FAFAFA"' in cmd

    def test_exported_record_renders_through_the_core(self):
        cmd = export_cli(ParamSpec(tree_text='((A:0.1,B:0.2)C:0.3)R;', render_format="PDF"))
        assert "--render" in cmd and "java -jar" not in cmd


def _split_args(cmd: str):
    """Split an exported multi-line command into argv tokens."""
    import shlex
    return shlex.split(cmd.replace("\\\n", " "))
