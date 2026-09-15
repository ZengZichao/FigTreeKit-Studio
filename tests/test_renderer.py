"""
test_renderer — JAR 渲染正确性 + 错误处理。
"""

import os
import pytest
from figtreekit_studio.core.renderer import render, locate_jar, check_java, RenderResult
from figtreekit_studio.core.generator import generate_nex
from figtreekit_studio.core.params import ParamSpec


SIMPLE_TREE = "((A:0.1,B:0.2):0.3,(C:0.4,D:0.5):0.6);"


@pytest.fixture(scope="module")
def nex_file():
    """生成一个 .nex 供渲染测试。"""
    p = ParamSpec(tree_text=SIMPLE_TREE, layout="rectilinear", tip_labels="show")
    r = generate_nex(p)
    if not r.ok:
        pytest.skip(f"无法生成 .nex: {r.error}")
    return r.nex_path


class TestLocateJar:
    def test_jar_exists(self):
        """JAR 应能定位到。"""
        jar = locate_jar()
        assert jar, "未找到 figtree_patched.jar"
        assert os.path.exists(jar)


class TestCheckJava:
    def test_java_available(self):
        """Java 应可用。"""
        ok, ver = check_java()
        assert ok, f"Java 不可用: {ver}"


class TestRender:
    def test_render_png(self, nex_file):
        """PNG 渲染应成功且返回 data URI。"""
        r = render(nex_file, fmt="PNG", width=800, height=600)
        assert r.ok, f"渲染失败: {r.error}"
        assert r.image.startswith("data:image/png;base64,")
        assert os.path.exists(r.output_path)

    def test_render_invalid_format(self, nex_file):
        """无效格式应失败。"""
        r = render(nex_file, fmt="GIF")
        assert not r.ok
        assert "不支持" in r.error

    def test_render_nonexistent_nex(self):
        """不存在的 .nex 应失败。"""
        r = render("/tmp/nonexistent.nex", fmt="PNG")
        # JAR 会报错或文件不存在
        assert not r.ok

    def test_render_svg(self, nex_file):
        """SVG 渲染应成功。"""
        r = render(nex_file, fmt="SVG", width=800, height=600)
        assert r.ok, f"SVG 渲染失败: {r.error}"
        assert r.image.startswith("data:image/svg+xml;base64,")
