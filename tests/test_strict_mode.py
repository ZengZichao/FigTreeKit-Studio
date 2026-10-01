"""strict 模式的自我验证。

本文件测试的是 conftest 里的 require() 机制本身。如果 require() 写坏了
（比如忘了判 strict、或吞掉了异常），下面三条会先失败——而不是等到某天
真实依赖缺失时，我们误以为门禁还在。

conftest 的 session 级裁决（"strict 下出现任何 skip 即整次失败"）
依赖 pytest 进程生命周期，无法在进程内自测，改由 CI 脚本
scripts/check_strict_mode.sh 做端到端验证。
"""

from __future__ import annotations

import pytest

from tests.conftest import STRICT_ENV, require, strict_mode


class TestStrictModeDetection:
    def test_absent_env_is_not_strict(self, monkeypatch):
        monkeypatch.delenv(STRICT_ENV, raising=False)
        assert strict_mode() is False

    def test_env_one_is_strict(self, monkeypatch):
        monkeypatch.setenv(STRICT_ENV, "1")
        assert strict_mode() is True

    def test_other_values_are_not_strict(self, monkeypatch):
        # 避免 "true" / "yes" 之类拼写被误当成开启，悄悄关掉整道门禁。
        for value in ("0", "", "true", "yes", "TRUE", "false"):
            monkeypatch.setenv(STRICT_ENV, value)
            assert strict_mode() is False, f"{STRICT_ENV}={value!r} 不应开启 strict"


class TestRequire:
    def test_satisfied_condition_is_a_noop(self, monkeypatch):
        monkeypatch.setenv(STRICT_ENV, "1")
        require(True, "这条 reason 不该被用到")  # 不抛异常即通过

    def test_unsatisfied_skips_outside_strict_mode(self, monkeypatch):
        monkeypatch.delenv(STRICT_ENV, raising=False)
        with pytest.raises(pytest.skip.Exception):
            require(False, "本地缺少可选依赖")

    def test_unsatisfied_fails_inside_strict_mode(self, monkeypatch):
        monkeypatch.setenv(STRICT_ENV, "1")
        with pytest.raises(pytest.fail.Exception):
            require(False, "CI 上缺少必需依赖")

    def test_strict_mode_failure_mentions_the_reason(self, monkeypatch):
        """失败信息必须带上原因，否则 strict 模式会变成无信息的红灯。"""
        monkeypatch.setenv(STRICT_ENV, "1")
        with pytest.raises(pytest.fail.Exception) as excinfo:
            require(False, "JAR 缺失")
        assert "JAR 缺失" in str(excinfo.value)
