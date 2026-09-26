"""
renderer — .nex → PNG/PDF/SVG/JPEG（java -jar）

封装 ``java -jar figtree_patched.jar -graphic <FORMAT> -width W -height H <input.nex> <output>`` 调用，
超时保护（默认 180s）。JAR 优先使用包内分发版本，回退到 figtreekit 包内 JAR。
"""

from __future__ import annotations

import base64
import os
import subprocess
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
    1. figtreekit 包内 figtree_patched.jar（权威副本，与被审的渲染行为同源）
    2. Studio 包内 data/figtree_patched.jar（仅用于冻结打包；两份副本的
       SHA-256 一致，由 tests/test_hardening 之外的 packaging 校验保证）

    先取核心库副本，可避免核心更新后 Studio 仍用旧 JAR 渲染而产生行为漂移。
    """
    # 1) figtreekit 包内（权威）
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

    # 2) Studio 包内（冻结打包回退）
    here = os.path.dirname(os.path.abspath(__file__))
    studio_jar = os.path.normpath(os.path.join(here, "..", "data", "figtree_patched.jar"))
    if os.path.exists(studio_jar):
        return studio_jar

    return ""


# --------------------------------------------------------------------------- #
# Java 检查
# --------------------------------------------------------------------------- #
MIN_JAVA_MAJOR = 8


def _java_major_version(version_line: str) -> int | None:
    """从 `java -version` 首行解析主版本号（支持 1.8.0_501 与 17.0.2 两种写法）。"""
    import re
    m = re.search(r'"(?:1\.)?(\d+)', version_line or "")
    return int(m.group(1)) if m else None


def check_java() -> tuple[bool, str]:
    """检查 java 是否可用。返回 (ok, version_string)。"""
    try:
        proc = subprocess.run(
            ["java", "-version"], capture_output=True, text=True, timeout=10
        )
        text = (proc.stderr or proc.stdout or "")
        ver = text.strip().splitlines()[0] if text.strip() else ""
        major = _java_major_version(ver)
        if major is not None and major < MIN_JAVA_MAJOR:
            return False, (f"Java {major} 过旧：FigTree 1.4.4 渲染需要 Java "
                           f"{MIN_JAVA_MAJOR} 及以上（{ver}）")
        return True, ver
    except FileNotFoundError:
        return False, "未找到 java，请安装 Java 8+ (JRE/JDK)"
    except Exception as e:
        return False, f"java 检查失败: {e}"


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """#RRGGBB / #RGB → (R, G, B)。仅用于界面校验，不参与渲染。"""
    hex_color = hex_color.lstrip("#").upper()
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    try:
        return (int(hex_color[0:2], 16), int(hex_color[2:4], 16),
                int(hex_color[4:6], 16))
    except ValueError:
        return (0, 0, 0)


# --------------------------------------------------------------------------- #
# 渲染：全部委托给 figtreekit 核心
#
# 核心 FigTree 1.4.4 的 headless 渲染器不读取全局 appearance 颜色，FigTreeKit
# 在 figtreekit._appearance_post 中把它作为渲染后处理步骤实现。Studio 因此不
# 再自带任何配色/位图处理逻辑：预览与 `figtreekit --render` 走的是同一份核心
# 代码，导出的命令行因此可以逐像素复现界面所见。
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

    from figtreekit import render_with_figtree
    from figtreekit.exceptions import RenderError

    try:
        render_with_figtree(
            nex_path, output_path, fmt_upper, width, height,
            jar_path=jar_path, timeout=timeout,
            background_color=bg_color or None,
            foreground_color=foreground_color or None,
            label_color=label_color or None,
        )
    except subprocess.TimeoutExpired:
        return RenderResult(ok=False, error=f"JAR 渲染超时（>{timeout}s）",
                            error_key="render_timeout", error_detail=f">{timeout}s")
    except RenderError as exc:
        detail = str(exc)[-1500:]
        return RenderResult(ok=False, error=f"JAR 渲染失败:\n{detail}",
                            error_key="render_failed", error_detail=detail)
    except Exception as exc:  # noqa: BLE001 — 任何失败都要变成界面可见的错误
        return RenderResult(ok=False, error=f"渲染异常: {type(exc).__name__}: {exc}",
                            error_key="render_failed", error_detail=str(exc))

    if not os.path.exists(output_path):
        return RenderResult(ok=False, error="渲染未产出文件",
                            error_key="render_failed", error_detail=output_path)

    with open(output_path, "rb") as f:
        data = f.read()

    mime_map = {
        "PNG": "image/png",
        "JPEG": "image/jpeg",
        "PDF": "application/pdf",
        "SVG": "image/svg+xml",
    }
    mime = mime_map.get(fmt_upper, "application/octet-stream")
    b64 = base64.b64encode(data).decode("ascii")
    image = f"data:{mime};base64,{b64}"


    return RenderResult(ok=True, image=image, output_path=output_path, log="")
