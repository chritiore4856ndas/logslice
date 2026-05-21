"""Tests for logslice.truncate."""

from __future__ import annotations

import pytest

from logslice.truncate import (
    TruncateConfig,
    apply_truncation,
    make_truncate_config,
    truncate_line,
)


class TestTruncateConfig:
    def test_defaults(self):
        cfg = TruncateConfig()
        assert cfg.enabled is False
        assert cfg.max_length == 512

    def test_invalid_max_length_raises(self):
        with pytest.raises(ValueError):
            TruncateConfig(max_length=0)


class TestTruncateLine:
    def test_disabled_returns_unchanged(self):
        cfg = TruncateConfig(enabled=False, max_length=5)
        line = "hello world\n"
        assert truncate_line(line, cfg) == line

    def test_short_line_unchanged(self):
        cfg = TruncateConfig(enabled=True, max_length=20)
        line = "short\n"
        assert truncate_line(line, cfg) == line

    def test_long_line_truncated(self):
        cfg = TruncateConfig(enabled=True, max_length=10, ellipsis=" ...")
        line = "0123456789ABCDEF\n"
        result = truncate_line(line, cfg)
        assert result == "012345 ...\n"

    def test_newline_preserved_after_truncation(self):
        cfg = TruncateConfig(enabled=True, max_length=5, ellipsis="...")
        line = "abcdefgh\n"
        assert truncate_line(line, cfg).endswith("\n")

    def test_no_newline_preserved(self):
        cfg = TruncateConfig(enabled=True, max_length=5, ellipsis="...")
        line = "abcdefgh"
        assert not truncate_line(line, cfg).endswith("\n")

    def test_exact_length_not_truncated(self):
        cfg = TruncateConfig(enabled=True, max_length=5, ellipsis="...")
        line = "hello"
        assert truncate_line(line, cfg) == "hello"

    def test_ellipsis_longer_than_max_still_safe(self):
        cfg = TruncateConfig(enabled=True, max_length=2, ellipsis="....")
        line = "abcdef"
        result = truncate_line(line, cfg)
        # cut becomes negative → clamped to 0, body is empty + ellipsis
        assert result == "...."

    def test_custom_ellipsis(self):
        cfg = TruncateConfig(enabled=True, max_length=8, ellipsis="[CUT]")
        line = "0123456789\n"
        result = truncate_line(line, cfg)
        assert result == "012[CUT]\n"


class TestApplyTruncation:
    def test_disabled_returns_same_list_contents(self):
        cfg = TruncateConfig(enabled=False, max_length=3)
        lines = ["hello\n", "world\n"]
        assert apply_truncation(lines, cfg) == lines

    def test_enabled_truncates_all_long_lines(self):
        cfg = TruncateConfig(enabled=True, max_length=4, ellipsis=".")
        lines = ["abcde\n", "ab\n", "abcdef\n"]
        result = apply_truncation(lines, cfg)
        assert result == ["abc.\n", "ab\n", "abc.\n"]


def test_make_truncate_config_defaults():
    cfg = make_truncate_config()
    assert cfg.enabled is False
    assert cfg.max_length == 512


def test_make_truncate_config_custom():
    cfg = make_truncate_config(enabled=True, max_length=80, ellipsis=">>>")
    assert cfg.enabled is True
    assert cfg.max_length == 80
    assert cfg.ellipsis == ">>>"
