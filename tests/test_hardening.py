"""安全与可达性加固的回归测试。

覆盖审阅中确认的三类问题：
  * `--host` 过去无校验，可静默监听全部网卡；
  * 文本颜色令牌曾低于 WCAG AA 所要求的 4.5:1；
  * 会话产物过去按"每次渲染"散落，而非按会话归拢。
"""

import os
import re
import tempfile

import pytest

from figtreekit_studio.server import LOOPBACK_HOSTS, resolve_bind_host
from tests.conftest import require

STATIC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "figtreekit_studio", "static")


class TestBindAddress:
    def test_loopback_aliases_are_accepted(self):
        for host in ("127.0.0.1", "localhost", "::1", "127.0.0.53"):
            assert resolve_bind_host(host)  # no exception

    def test_non_loopback_requires_explicit_opt_in(self):
        for host in ("0.0.0.0", "192.168.1.10", "10.0.0.5"):
            with pytest.raises(ValueError) as exc:
                resolve_bind_host(host)
            assert "authentication" in str(exc.value) or "--allow-remote-bind" in str(exc.value)

    def test_non_loopback_allowed_only_when_deliberate(self):
        assert resolve_bind_host("0.0.0.0", allow_remote=True) == "0.0.0.0"

    def test_cli_exposes_the_guard(self):
        from figtreekit_studio import cli
        parser_src = open(os.path.join(STATIC, os.pardir, "cli.py"),
                          encoding="utf-8").read()
        assert "--allow-remote-bind" in parser_src


def _relative_luminance(rgb):
    c = [v / 255 for v in rgb]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _contrast(fg, bg):
    a, b = sorted((_relative_luminance(fg), _relative_luminance(bg)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def _hex(value):
    v = value.lstrip("#")
    if len(v) == 3:
        v = "".join(ch * 2 for ch in v)
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def _css_tokens():
    text = open(os.path.join(STATIC, "style.css"), encoding="utf-8").read()
    block = text.split(":root", 1)[1].split("}", 1)[0]
    return dict(re.findall(r"(--[\w-]+):\s*(#[0-9a-fA-F]{3,6})", block))


class TestContrast:
    """Text tokens must meet WCAG 2.1 AA (4.5:1) on both page backgrounds."""

    TEXT_TOKENS = ("--ink", "--mut", "--accent")

    def test_tokens_present(self):
        tokens = _css_tokens()
        for name in self.TEXT_TOKENS + ("--bg", "--card"):
            assert name in tokens, f"{name} missing from :root"

    @pytest.mark.parametrize("token", TEXT_TOKENS)
    def test_aa_on_both_backgrounds(self, token):
        tokens = _css_tokens()
        for bg_name in ("--bg", "--card"):
            ratio = _contrast(_hex(tokens[token]), _hex(tokens[bg_name]))
            assert ratio >= 4.5, (
                f"{token} on {bg_name} is {ratio:.2f}:1, below WCAG AA 4.5:1")

    def test_control_border_has_3_to_1(self):
        tokens = _css_tokens()
        ratio = _contrast(_hex(tokens["--line-strong"]), _hex(tokens["--bg"]))
        assert ratio >= 3.0, f"--line-strong on --bg is {ratio:.2f}:1, below 3:1"


class TestSessionWorkDirectory:
    def test_runs_are_grouped_under_one_session_directory(self):
        from figtreekit_studio.core.generator import generate_nex, SESSION_ID
        from figtreekit_studio.core.params import ParamSpec

        base = tempfile.mkdtemp()
        paths = []
        for _ in range(2):
            gen = generate_nex(ParamSpec(tree_text="((A:0.1,B:0.2)C:0.3)R;",
                                         work_dir=base))
            assert gen.ok, gen.error
            paths.append(os.path.dirname(gen.nex_path))
        session_dirs = {os.path.dirname(p) for p in paths}
        assert session_dirs == {os.path.join(base, f"ftk_session_{SESSION_ID}")}, (
            "a single app session must keep its renders in one session directory")


class TestBundledJarIsNotDrifted:
    """Studio may ship a fallback JAR, but it must be byte-identical to the
    authoritative copy in the core package."""

    @pytest.mark.requires_jar
    def test_fallback_jar_matches_the_core_jar(self):
        import hashlib
        import figtreekit
        core = os.path.join(os.path.dirname(os.path.abspath(figtreekit.__file__)),
                            "figtree_patched.jar")
        fallback = os.path.join(os.path.dirname(STATIC), "data", "figtree_patched.jar")
        # 这一条是「两份 JAR 未漂移」的唯一防线，绝不能静默跳过：
        # 一旦 skip，JAR 漂移就能悄无声息地进入发布产物。
        require(
            os.path.exists(core) and os.path.exists(fallback),
            "核心库或回退 JAR 缺失：core={} fallback={}".format(
                os.path.exists(core), os.path.exists(fallback)),
        )
        h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
        assert h(core) == h(fallback), (
            "the two shipped copies of figtree_patched.jar have drifted")

    @pytest.mark.requires_jar
    def test_core_copy_is_preferred(self):
        import figtreekit
        from figtreekit_studio.core.renderer import locate_jar
        jar = locate_jar()
        core_dir = os.path.dirname(os.path.abspath(figtreekit.__file__))
        assert os.path.abspath(jar).startswith(core_dir), (
            f"locate_jar() must prefer the core copy, got {jar}")


class TestJavaFloor:
    def test_legacy_and_modern_version_lines_parse(self):
        from figtreekit_studio.core.renderer import _java_major_version
        assert _java_major_version('java version "1.8.0_501"') == 8
        assert _java_major_version('openjdk version "17.0.20" 2026') == 17

    def test_old_java_is_rejected_as_unavailable(self):
        from unittest import mock
        from figtreekit_studio.core import renderer

        proc = mock.Mock(returncode=0, stdout="",
                         stderr='java version "1.7.0_80"\n')
        with mock.patch("subprocess.run", return_value=proc):
            ok, msg = renderer.check_java()
        assert not ok and "1.7" in msg

    def test_current_java_is_accepted(self):
        from unittest import mock
        from figtreekit_studio.core import renderer

        proc = mock.Mock(returncode=0, stdout="",
                         stderr='java version "1.8.0_501"\n')
        with mock.patch("subprocess.run", return_value=proc):
            ok, msg = renderer.check_java()
        assert ok, msg
