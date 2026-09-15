"""
test_renderer — JAR 渲染正确性 + 错误处理。
"""

import base64
import io
import os

import pytest
from PIL import Image

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


@pytest.fixture(scope="module")
def nex_file_with_label_color():
    """生成带标签色的 .nex 供渲染测试。"""
    p = ParamSpec(
        tree_text=SIMPLE_TREE, layout="rectilinear", tip_labels="show",
        label_color="#0000FF",
    )
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


class TestRenderColors:
    """验证颜色参数能在 headless 渲染结果中生效。"""

    @staticmethod
    def _decode_image(r: RenderResult) -> Image.Image:
        data = base64.b64decode(r.image.split(",")[1])
        return Image.open(io.BytesIO(data)).convert("RGB")

    def test_background_color_applied(self, nex_file):
        r = render(nex_file, fmt="PNG", width=400, height=300, bg_color="#FF0000")
        assert r.ok, f"渲染失败: {r.error}"
        img = self._decode_image(r)
        # 角落属于背景区域，应被合成红色
        assert img.getpixel((10, 10)) == (255, 0, 0)

    def test_foreground_color_applied(self, nex_file):
        r = render(nex_file, fmt="PNG", width=400, height=300, foreground_color="#00FF00")
        assert r.ok, f"渲染失败: {r.error}"
        img = self._decode_image(r)
        # 找非背景、非白色的像素（树/刻度元素），应被重着为绿色
        # 允许抗锯齿产生的过渡色：R、B 接近 0，G 占主导
        tree_pixels = [
            px for px in img.get_flattened_data()
            if px != (255, 255, 255) and max(px) > 0
        ]
        assert tree_pixels
        # 抗锯齿会在白色背景上产生绿白过渡色，特征为 R≈B、G=255
        assert all(
            abs(p[0] - p[2]) <= 5 and p[1] == 255
            for p in tree_pixels
        ), f"存在未重着像素: {set(tree_pixels)}"

    def test_label_color_applied(self, nex_file_with_label_color):
        r = render(
            nex_file_with_label_color, fmt="PNG", width=400, height=300,
            label_color="#0000FF",
        )
        assert r.ok, f"渲染失败: {r.error}"
        img = self._decode_image(r)
        # 标签像素应为蓝色
        label_pixels = [px for px in img.get_flattened_data() if px == (0, 0, 255)]
        assert label_pixels, "未找到蓝色标签像素"
