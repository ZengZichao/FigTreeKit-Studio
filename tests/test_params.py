"""
test_params — 参数映射正确性 + exporter 与 generator 共用同一映射（无漂移）。
"""

import pytest
from figtreekit_studio.core.params import (
    ParamSpec,
    to_cli_args,
    to_config_dict,
    to_config_json,
)


# --------------------------------------------------------------------------- #
# to_cli_args
# --------------------------------------------------------------------------- #
class TestToCliArgs:
    def test_default_params(self):
        """默认参数会包含 layout=rectilinear 和 tip_labels=show。"""
        p = ParamSpec()
        args = to_cli_args(p)
        # 默认值有 layout=rectilinear, tip_labels=show
        assert "--layout" in args
        assert "rectilinear" in args
        assert "--tip-labels-show" in args

    def test_layout(self):
        p = ParamSpec(layout="polar")
        assert "--layout" in to_cli_args(p)
        assert "polar" in to_cli_args(p)

    def test_tip_labels_hide(self):
        p = ParamSpec(tip_labels="hide")
        assert "--tip-labels-hide" in to_cli_args(p)
        assert "--tip-labels-show" not in to_cli_args(p)

    def test_tip_labels_show(self):
        p = ParamSpec(tip_labels="show")
        assert "--tip-labels-show" in to_cli_args(p)
        assert "--tip-labels-hide" not in to_cli_args(p)

    def test_bg_color(self):
        p = ParamSpec(bg_color="#FAFAFA")
        args = to_cli_args(p)
        assert "--background-color" in args
        assert "#FAFAFA" in args

    def test_branch_width(self):
        p = ParamSpec(branch_width=2.5)
        args = to_cli_args(p)
        assert "--branch-width" in args
        assert "2.5" in args

    def test_branch_width_zero_skipped(self):
        p = ParamSpec(branch_width=0.0)
        assert "--branch-width" not in to_cli_args(p)

    def test_auto_color_rank(self):
        p = ParamSpec(auto_color_rank="phylum")
        args = to_cli_args(p)
        assert "--auto-color" in args
        assert "phylum" in args

    def test_collapse_rank_and_style(self):
        p = ParamSpec(collapse_rank="phylum", collapse_style="cartoon")
        args = to_cli_args(p)
        assert "--collapse-rank" in args
        assert "phylum" in args
        assert "--collapse-style" in args
        assert "cartoon" in args

    def test_scale_axis(self):
        p = ParamSpec(scale_axis="show")
        assert "--scale-axis-show" in to_cli_args(p)

    def test_scale_bar(self):
        p = ParamSpec(scale_bar="show")
        assert "--scale-bar-show" in to_cli_args(p)

    def test_polar_params(self):
        p = ParamSpec(angular_range=270, root_angle=90)
        args = to_cli_args(p)
        assert "--angular-range" in args
        assert "--root-angle" in args

    def test_curvature(self):
        p = ParamSpec(curvature=5)
        args = to_cli_args(p)
        assert "--curvature" in args
        assert "5" in args

    def test_node_labels(self):
        p = ParamSpec(node_labels="show", node_display_attribute="height")
        args = to_cli_args(p)
        assert "--node-labels-show" in args
        assert "--node-display-attribute" in args
        assert "height" in args

    def test_branch_labels(self):
        p = ParamSpec(branch_labels="show", branch_display_attribute="length")
        args = to_cli_args(p)
        assert "--branch-labels-show" in args
        assert "--branch-display-attribute" in args

    def test_legend(self):
        p = ParamSpec(legend="show", legend_position="top")
        args = to_cli_args(p)
        assert "--legend-show" in args
        assert "--legend-position" in args
        assert "top" in args

    def test_dict_input(self):
        """dict 输入也能正常工作。"""
        args = to_cli_args({"layout": "polar", "tip_labels": "hide"})
        assert "--layout" in args
        assert "--tip-labels-hide" in args

    def test_full_params(self):
        """全参数组合不应报错。"""
        p = ParamSpec(
            layout="polar",
            tip_labels="hide",
            align_tip_labels=True,
            bg_color="#FAFAFA",
            branch_width=2.0,
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
        assert len(args) > 10  # 确实生成了参数


# --------------------------------------------------------------------------- #
# to_config_dict
# --------------------------------------------------------------------------- #
class TestToConfigDict:
    def test_layout(self):
        p = ParamSpec(layout="polar")
        d = to_config_dict(p)
        assert d["layout.layoutType"] == "POLAR"

    def test_tip_labels_hide(self):
        p = ParamSpec(tip_labels="hide")
        d = to_config_dict(p)
        assert d["tipLabels.isShown"] is False

    def test_tip_labels_show(self):
        p = ParamSpec(tip_labels="show")
        d = to_config_dict(p)
        assert d["tipLabels.isShown"] is True

    def test_bg_color(self):
        p = ParamSpec(bg_color="#FAFAFA")
        d = to_config_dict(p)
        assert d["appearance.backgroundColour"] == "#FAFAFA"

    def test_branch_width(self):
        p = ParamSpec(branch_width=2.5)
        d = to_config_dict(p)
        assert d["appearance.branchLineWidth"] == 2.5

    def test_scale_axis(self):
        p = ParamSpec(scale_axis="show")
        d = to_config_dict(p)
        assert d["scaleAxis.isShown"] is True

    def test_polar_params(self):
        p = ParamSpec(angular_range=270, root_angle=90)
        d = to_config_dict(p)
        assert d["polarLayout.angularRange"] == 270
        assert d["polarLayout.rootAngle"] == 90

    def test_default_params_config(self):
        """默认参数应包含 layout 和 tipLabels。"""
        p = ParamSpec()
        d = to_config_dict(p)
        assert d["layout.layoutType"] == "RECTILINEAR"
        assert d["tipLabels.isShown"] is True

    def test_config_json_is_valid_json(self):
        p = ParamSpec(layout="polar", tip_labels="hide")
        import json
        d = json.loads(to_config_json(p))
        assert d["layout.layoutType"] == "POLAR"
        assert d["tipLabels.isShown"] is False


class TestConfigKeySchema:
    """断言 to_config_dict 产出的每个键都能在 figtreekit schema 中命中。"""

    def test_all_config_keys_in_schema(self):
        """to_config_dict 产出的所有键必须存在于 figtreekit schema 中。"""
        try:
            from figtreekit._defaults import get_figtree_defaults
            defaults = get_figtree_defaults()
        except Exception:
            pytest.skip("figtreekit not available for schema check")
        keys = set()
        for category, params in defaults.items():
            for param in params:
                keys.add(f"{category}.{param}")

        p = ParamSpec(
            layout="polar", tip_labels="show", align_tip_labels=True,
            bg_color="#FAFAFA", branch_width=2.0, foreground_color="#000000",
            font_name="Arial", font_size=14, font_style="bold",
            label_color="#FF0000", curvature=5,
            scale_axis="show", scale_bar="show",
            node_labels="show", node_display_attribute="height",
            branch_labels="show", branch_display_attribute="length",
            legend="show", legend_position="top",
        )
        config = to_config_dict(p)
        for key in config:
            assert key in keys, (
                f"Config key '{key}' not in figtreekit schema — will be silently ignored"
            )

    def test_align_tip_labels_dispatches_by_layout(self):
        """align_tip_labels 应按布局写入对应布局节点的 alignTipLabels 键。"""
        for layout, expected_key in [
            ("rectilinear", "rectilinearLayout.alignTipLabels"),
            ("polar", "polarLayout.alignTipLabels"),
            ("radial", "radialLayout.alignTipLabels"),
        ]:
            p = ParamSpec(layout=layout, align_tip_labels=True)
            config = to_config_dict(p)
            assert expected_key in config, (
                f"Layout '{layout}' should produce key '{expected_key}'"
            )
            assert config[expected_key] is True


class TestCurvatureNullSafety:
    """curvature=None 不应导致 TypeError。"""

    def test_curvature_none_does_not_crash(self):
        p = ParamSpec.from_dict({"curvature": None})
        args = to_cli_args(p)
        # None → 不传 --curvature，不报 TypeError
        assert "--curvature" not in args

    def test_curvature_none_config_does_not_crash(self):
        p = ParamSpec.from_dict({"curvature": None})
        config = to_config_dict(p)
        assert "rectilinearLayout.curvature" not in config


class TestCliConfigHideSync:
    """凡 to_cli_args 产出的显隐开关，to_config_dict 必须有对应键。"""

    def test_node_labels_hide_in_both(self):
        p = ParamSpec.from_dict({"node_labels": "hide"})
        assert "--node-labels-hide" in to_cli_args(p)
        assert to_config_dict(p)["nodeLabels.isShown"] is False

    def test_branch_labels_hide_in_both(self):
        p = ParamSpec.from_dict({"branch_labels": "hide"})
        assert "--branch-labels-hide" in to_cli_args(p)
        assert to_config_dict(p)["branchLabels.isShown"] is False

    def test_scale_bar_hide_in_both(self):
        p = ParamSpec.from_dict({"scale_bar": "hide"})
        assert "--scale-bar-hide" in to_cli_args(p)
        assert to_config_dict(p)["scaleBar.isShown"] is False

    def test_scale_axis_hide_in_both(self):
        p = ParamSpec.from_dict({"scale_axis": "hide"})
        assert "--scale-axis-hide" in to_cli_args(p)
        assert to_config_dict(p)["scaleAxis.isShown"] is False
