"""版本号同步守卫。

`0.1.2` 目前硬编码在 7 个文件里（发布时必须逐个手改，且没有任何东西会在
漏改时报错）。本测试把"发布时必须成组更新的那些位置"变成断言：只要有人
只改了其中一部分，CI 立刻红。

覆盖面刻意包含三个容易被漏掉的：
  * `FigTreeKit Studio.spec` 与 `setup_py2app.py` 的 CFBundle 版本 ——
    前者决定打包产物的版本号，漏改会让 .app 自报旧版本；
  * CHANGELOG 的最新**已发布**条目 —— 决定"最新发布"到底是哪一版；
    顶部的 `## [Unreleased]` 累积段会被正确跳过；
  * CITATION.cff 的 date-released 与 CHANGELOG 的条目日期必须同日，
    否则引用元数据与实际发布记录对不上。

不覆盖 README 正文里作为历史记录出现的版本号（那是叙述，不是配置）。
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

from figtreekit_studio import __version__
from tests.conftest import require

ROOT = Path(__file__).resolve().parent.parent

# 仅当以可编辑方式安装、且在源码树内运行时才可校验。
# 严格模式下若缺文件会判失败——因为 CI 一定是可编辑安装，缺文件说明
# 测试跑错了地方，而不是「没法检查」。
SOURCE_FILES = [
    "pyproject.toml",
    "CITATION.cff",
    "CHANGELOG.md",
    "README.md",
    "README_EN.md",
    "FigTreeKit Studio.spec",
    "setup_py2app.py",
]


def _read(name: str) -> str:
    path = ROOT / name
    require(path.is_file(), f"找不到 {name}（当前不在源码树内，无法校验版本一致性）")
    return path.read_text(encoding="utf-8")


def _search(pattern: str, text: str, name: str) -> str:
    m = re.search(pattern, text, re.MULTILINE)
    require(m is not None, f"在 {name} 中找不到匹配 {pattern!r} 的版本号，请更新本测试")
    return m.group(1)


def _latest_released_version(changelog: str) -> str:
    """取 CHANGELOG 里最新的**已发布**版本号。

    Keep a Changelog 惯例允许顶部存在 `## [Unreleased]` 段做开发累积。
    那不是一次发布，直接拿它当"当前版本"会在每次开发周期开头误报。
    """
    for m in re.finditer(r'^##\s*\[([^\]]+)\]', changelog, re.MULTILINE):
        if re.match(r'^\d', m.group(1)):
            return m.group(1)
    raise AssertionError("CHANGELOG.md 中找不到形如 `## [x.y.z]` 的已发布条目")


class TestVersionIsSynchronised:
    def test_source_tree_is_available(self):
        """先把前置条件摆平，后续用例的报错才指向真正的原因。"""
        require(ROOT.is_dir() and (ROOT / "pyproject.toml").is_file(),
                "测试未在源码树内运行")
        for name in SOURCE_FILES:
            require((ROOT / name).is_file(), f"版本来源缺失：{name}")

    def test_pyproject_matches_package(self):
        data = tomllib.loads(_read("pyproject.toml"))
        assert data["project"]["version"] == __version__, (
            "pyproject.toml 的 project.version 与 figtreekit_studio.__version__ 不一致"
        )

    def test_citation_version_matches_package(self):
        got = _search(r'^version:\s*"?([^"\n]+)"?\s*$', _read("CITATION.cff"), "CITATION.cff")
        assert got == __version__, "CITATION.cff 的 version 与包版本不一致"

    def test_changelog_latest_entry_matches_package(self):
        got = _latest_released_version(_read("CHANGELOG.md"))
        assert got == __version__, (
            f"CHANGELOG.md 最新已发布条目是 {got}，与包版本 {__version__} 不一致"
        )

    def test_changelog_date_matches_citation_release_date(self):
        changelog = _read("CHANGELOG.md")
        m = re.search(
            r'^##\s*\[([^\]]+)\]\s*-\s*(\d{4}-\d{2}-\d{2})', changelog, re.MULTILINE
        )
        require(m is not None, "CHANGELOG.md 中找不到带日期的发布条目")
        version, got = m.group(1), m.group(2)
        # 取与"最新已发布版本"对应的那一条的日期
        if version != _latest_released_version(changelog):
            m2 = re.search(
                rf'^##\s*\[{re.escape(_latest_released_version(changelog))}\]'
                r'\s*-\s*(\d{4}-\d{2}-\d{2})',
                changelog, re.MULTILINE,
            )
            require(m2 is not None, "找不到最新已发布条目的日期")
            got = m2.group(1)
        cited = _search(r'^date-released:\s*"?([\d-]+)"?\s*$', _read("CITATION.cff"),
                        "CITATION.cff")
        assert got == cited, (
            f"CHANGELOG 最新条目日期 {got} 与 CITATION.cff 的 date-released {cited} 不一致；"
            "发布时这两处必须一起改"
        )

    def test_unreleased_section_does_not_confuse_the_guard(self):
        """开发中新增 `## [Unreleased]` 段不应让守卫误报。"""
        text = "## [Unreleased]\n\n### Fixed\n\n- 某修复\n\n## [0.1.2] - 2026-09-26\n"
        assert _latest_released_version(text) == "0.1.2"

    @pytest.mark.parametrize("filename", ["FigTreeKit Studio.spec", "setup_py2app.py"])
    def test_bundle_version_matches_package(self, filename):
        text = _read(filename)
        for key in ("CFBundleShortVersionString", "CFBundleVersion"):
            # 两种文件风格不同：.spec 用单引号，setup_py2app.py 用双引号。
            got = _search(rf"""['"]{key}['"]\s*:\s*['"]([^'"]+)['"]""", text, filename)
            assert got == __version__, (
                f"{filename} 的 {key} = {got}，与包版本 {__version__} 不一致"
            )

    @pytest.mark.parametrize(
        ("filename", "marker"),
        [("README.md", "当前发布版本"), ("README_EN.md", "current release")],
    )
    def test_readme_advertised_version_matches_package(self, filename, marker):
        got = _search(rf'^\*\*v([0-9][^*]*?)\s*—\s*{re.escape(marker)}\*\*$',
                      _read(filename), filename)
        assert got == __version__, (
            f"{filename} 标称的当前发布版本是 {got}，与包版本 {__version__} 不一致"
        )


class TestGuardItselfWorks:
    """证明上面的守卫不是空转：故意构造漂移，断言它会红。"""

    def test_pyproject_parser_detects_drift(self, tmp_path):
        fake = tmp_path / "pyproject.toml"
        fake.write_text('[project]\nname = "x"\nversion = "9.9.9"\n', encoding="utf-8")
        data = tomllib.loads(fake.read_text(encoding="utf-8"))
        assert data["project"]["version"] != __version__

    def test_changelog_parser_detects_drift(self):
        assert _latest_released_version("## [9.9.9] - 2030-01-01\n") != __version__

    @pytest.mark.parametrize(
        "text",
        [
            "'CFBundleShortVersionString': '9.9.9',",   # .spec 的单引号风格
            '"CFBundleShortVersionString": "9.9.9",',   # setup_py2app.py 的双引号风格
        ],
    )
    def test_bundle_key_parser_detects_drift(self, text):
        got = _search(
            r"""['"]CFBundleShortVersionString['"]\s*:\s*['"]([^'"]+)['"]""", text, "x"
        )
        assert got != __version__

    def test_readme_pattern_requires_the_exact_marker(self):
        # marker 写错时不应误匹配（例如中文 README 用英文 marker）
        text = "**v0.1.2 — 当前发布版本**"
        assert re.search(
            r'^\*\*v([0-9][^*]*?)\s*—\s*current release\*\*$', text, re.MULTILINE
        ) is None
