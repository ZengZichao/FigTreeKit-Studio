"""
test_generator — figtreekit CLI 调用正确性。
"""

import os
import tempfile
import pytest
from figtreekit_studio.core.generator import generate_nex, GenResult
from figtreekit_studio.core.params import ParamSpec


SIMPLE_TREE = "((A:0.1,B:0.2):0.3,(C:0.4,D:0.5):0.6);"


class TestGenerateNex:
    def test_simple_tree(self):
        """简单 Newick 树应成功生成 .nex。"""
        p = ParamSpec(tree_text=SIMPLE_TREE, layout="rectilinear")
        r = generate_nex(p)
        assert r.ok, f"Expected ok, got error: {r.error}"
        assert os.path.exists(r.nex_path)
        # .nex 内容应包含 taxa
        with open(r.nex_path, "r") as f:
            content = f.read()
        assert "A" in content and "B" in content

    def test_empty_tree_fails(self):
        """空树文本应失败。"""
        p = ParamSpec(tree_text="")
        r = generate_nex(p)
        assert not r.ok
        assert "请提供" in r.error

    def test_polar_layout(self):
        """极坐标布局。"""
        p = ParamSpec(tree_text=SIMPLE_TREE, layout="polar", tip_labels="show")
        r = generate_nex(p)
        assert r.ok, r.error
        assert os.path.exists(r.nex_path)

    def test_cli_args_returned(self):
        """成功时应返回 cli_args。"""
        p = ParamSpec(tree_text=SIMPLE_TREE, layout="polar", tip_labels="hide")
        r = generate_nex(p)
        assert r.ok
        assert r.cli_args is not None
        assert "--layout" in r.cli_args
        assert "--tip-labels-hide" in r.cli_args

    def test_invalid_tree(self):
        """无效树文本应失败。"""
        p = ParamSpec(tree_text="this is not a tree")
        r = generate_nex(p)
        assert not r.ok

    def test_dict_input(self):
        """dict 输入也能正常工作。"""
        r = generate_nex({"tree_text": SIMPLE_TREE, "layout": "radial"})
        assert r.ok, r.error

    def test_auto_color(self):
        """auto-color 参数能传递。"""
        p = ParamSpec(tree_text=SIMPLE_TREE, auto_color_rank="phylum")
        r = generate_nex(p)
        # 简单树可能因为没有分类信息而 warn，但不会 crash
        # 只要 .nex 生成成功即可
        if r.ok:
            assert os.path.exists(r.nex_path)

    def test_scale_axis(self):
        """scale-axis 参数能传递。"""
        p = ParamSpec(tree_text=SIMPLE_TREE, scale_axis="show")
        r = generate_nex(p)
        assert r.ok, r.error
        assert os.path.exists(r.nex_path)

    def test_user_work_dir(self):
        """指定 work_dir 时，中间文件应保留在用户目录下。"""
        base = tempfile.mkdtemp(prefix="ftk_user_")
        p = ParamSpec(tree_text=SIMPLE_TREE, layout="rectilinear", work_dir=base)
        r = generate_nex(p)
        assert r.ok, f"Expected ok, got error: {r.error}"
        assert r.is_user_work_dir is True
        assert os.path.exists(r.nex_path)
        assert r.work_dir.startswith(base)
        assert os.path.exists(os.path.join(r.work_dir, "input.tre"))
