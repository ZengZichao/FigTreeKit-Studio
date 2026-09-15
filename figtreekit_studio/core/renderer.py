"""
renderer — .nex → PNG/PDF/SVG/JPEG（java -jar）

封装 ``java -jar figtree_patched.jar -graphic <FORMAT> -width W -height H <input.nex> <output>`` 调用，
超时保护（默认 180s）。JAR 优先使用包内分发版本，回退到 figtreekit 包内 JAR。
"""

from __future__ import annotations

import base64
import io
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

from figtreekit_studio.core.params import RENDER_FORMATS


# --------------------------------------------------------------------------- #
# JAR 定位
# --------------------------------------------------------------------------- #
def locate_jar() -> str:
    """
    定位 figtree_patched.jar。

    优先级：
    1. Studio 包内 data/figtree_patched.jar（随包分发）
    2. figtreekit 包内 figtree_patched.jar
    """
    # 1) Studio 包内
    here = os.path.dirname(os.path.abspath(__file__))
    studio_jar = os.path.join(here, "..", "data", "figtree_patched.jar")
    studio_jar = os.path.normpath(studio_jar)
    if os.path.exists(studio_jar):
        return studio_jar

    # 2) figtreekit 包内
    try:
        import figtreekit
        ftk_jar = os.path.join(
            os.path.dirname(os.path.abspath(figtreekit.__file__)),
            "figtree_patched.jar",
        )
        if os.path.exists(ftk_jar):
            return ftk_jar
    except Exception:
        pass

    return ""


# --------------------------------------------------------------------------- #
# Java 检查
# --------------------------------------------------------------------------- #
def check_java() -> tuple[bool, str]:
    """检查 java 是否可用。返回 (ok, version_string)。"""
    try:
        proc = subprocess.run(
            ["java", "-version"], capture_output=True, text=True, timeout=10
        )
        ver = (proc.stderr or proc.stdout).strip().splitlines()[0] if (proc.stderr or proc.stdout) else ""
        return True, ver
    except FileNotFoundError:
        return False, "未找到 java，请安装 Java 8+ (JRE/JDK)"
    except Exception as e:
        return False, f"java 检查失败: {e}"


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """#RRGGBB / #RGB → (R, G, B)。"""
    hex_color = hex_color.lstrip("#").upper()
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    if len(hex_color) != 6:
        return (0, 0, 0)
    try:
        return (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16),
        )
    except ValueError:
        return (0, 0, 0)


def _apply_image_colors(
    data: bytes,
    fmt: str,
    bg_color: str,
    foreground_color: str,
    label_color: str,
) -> bytes:
    """
    对 FigTree JAR 渲染出的 raster 图片做颜色校正。

    FigTree 命令行渲染器会忽略全局 appearance 颜色，因此：
    - 标签颜色已在 generator 中通过 !color 节点注释实现；
    - 背景色通过 Pillow 合成到透明区域；
    - 前景色（分支、刻度尺等默认黑色元素）通过 Pillow 重着色。
    SVG/PDF 不处理，原样返回。
    """
    fmt_upper = fmt.upper()
    if fmt_upper not in ("PNG", "JPEG"):
        return data

    try:
        from PIL import Image
    except Exception:
        # Pillow 不可用时保持原图，避免阻断渲染
        return data

    try:
        img = Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception:
        return data

    fg_rgb = _hex_to_rgb(foreground_color) if foreground_color else None
    label_rgb = _hex_to_rgb(label_color) if label_color else None

    if fg_rgb:
        pixels = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixels[x, y]
                if a == 0:
                    continue
                # 保护已在 JAR 中正确渲染的标签颜色
                if label_rgb:
                    dist = (
                        (r - label_rgb[0]) ** 2
                        + (g - label_rgb[1]) ** 2
                        + (b - label_rgb[2]) ** 2
                    ) ** 0.5
                    if dist < 80:
                        continue
                # 将近黑像素重着为前景色
                if max(r, g, b) < 50:
                    pixels[x, y] = (fg_rgb[0], fg_rgb[1], fg_rgb[2], a)

    # 无论用户是否设置背景色，都把透明区域合成到背景上：
    # 未设置时默认使用白色，避免 Pillow convert('RGB') 把透明区域变成黑色。
    bg_rgb = _hex_to_rgb(bg_color) if bg_color else (255, 255, 255)
    bg = Image.new("RGBA", img.size, bg_rgb + (255,))
    img = Image.alpha_composite(bg, img)

    buf = io.BytesIO()
    if fmt_upper == "PNG":
        img.convert("RGB").save(buf, format="PNG")
    else:
        img.convert("RGB").save(buf, format="JPEG", quality=95)
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# 渲染
# --------------------------------------------------------------------------- #
@dataclass
class RenderResult:
    """render 返回值。"""
    ok: bool
    image: str = ""  # data URI (base64)
    output_path: str = ""
    error: str = ""
    error_key: str = ""     # 前端 i18n 错误码（见 app.js I18N.err.*）
    error_detail: str = ""
    log: str = ""


def render(
    nex_path: str,
    fmt: str = "PNG",
    width: int = 1600,
    height: int = 1000,
    *,
    bg_color: str = "",
    foreground_color: str = "",
    label_color: str = "",
    timeout: int = 180,
) -> RenderResult:
    """
    用 java -jar 渲染 .nex 为图片。

    参数:
        nex_path: 输入 .nex 文件路径。
        fmt: 输出格式 (PNG/PDF/SVG/JPEG)。
        width: 输出宽度像素。
        height: 输出高度像素。
        bg_color: 背景色 (#RRGGBB)，空则不合成。
        foreground_color: 前景色 (#RRGGBB)，空则不重着分支/刻度尺。
        label_color: 标签色 (#RRGGBB)，用于保护已正确渲染的标签像素。
        timeout: 渲染超时秒数。

    返回:
        RenderResult，成功时 image 为 data URI。
    """
    fmt_upper = (fmt or "PNG").upper()
    if fmt_upper not in RENDER_FORMATS:
        return RenderResult(ok=False, error=f"不支持的格式: {fmt}",
                            error_key="render_bad_format", error_detail=str(fmt))

    jar_path = locate_jar()
    if not jar_path:
        return RenderResult(
            ok=False,
            error=(
                "未找到 figtree_patched.jar。"
                "请运行 `python -m figtreekit --setup-figtree` 获取 JAR。"
            ),
            error_key="jar_missing",
        )

    java_ok, java_msg = check_java()
    if not java_ok:
        return RenderResult(ok=False, error=java_msg,
                            error_key="java_missing", error_detail=java_msg)

    # 输出路径
    base = os.path.splitext(nex_path)[0]
    ext = {"PNG": ".png", "PDF": ".pdf", "SVG": ".svg", "JPEG": ".jpg"}[fmt_upper]
    output_path = base + ext

    cmd = [
        "java", "-jar", jar_path,
        "-graphic", fmt_upper,
        "-width", str(width),
        "-height", str(height),
        nex_path,
        output_path,
    ]

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return RenderResult(ok=False, error=f"JAR 渲染超时（>{timeout}s）",
                            error_key="render_timeout", error_detail=f">{timeout}s")

    log = (proc.stdout or "") + (proc.stderr or "")
    if not os.path.exists(output_path):
        tail = log[-1500:] if log else "(no output)"
        return RenderResult(
            ok=False, error=f"JAR 渲染失败:\n{tail}", log=log,
            error_key="render_failed", error_detail=tail,
        )

    # 读取输出，做颜色校正，构造 data URI
    with open(output_path, "rb") as f:
        data = f.read()

    data = _apply_image_colors(data, fmt_upper, bg_color, foreground_color, label_color)

    mime_map = {
        "PNG": "image/png",
        "JPEG": "image/jpeg",
        "PDF": "application/pdf",
        "SVG": "image/svg+xml",
    }
    mime = mime_map.get(fmt_upper, "application/octet-stream")
    b64 = base64.b64encode(data).decode("ascii")
    image = f"data:{mime};base64,{b64}"

    return RenderResult(ok=True, image=image, output_path=output_path, log=log)
