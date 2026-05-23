"""Tests for logslice.grep."""
from __future__ import annotations

import pytest

from logslice.grep import GrepConfig, GrepResult, grep_lines, make_grep_config


def _pairs(lines):
    return list(enumerate(lines, start=1))


class TestGrepConfig:
    def test_defaults(self):
        cfg = GrepConfig()
        assert cfg.pattern is None
        assert cfg.ignore_case is False
        assert cfg.invert is False
        assert cfg.max_count is None

    def test_not_active_without_pattern(self):
        assert not GrepConfig().active

    def test_active_with_pattern(self):
        assert GrepConfig(pattern="error").active

    def test_invalid_max_count_raises(self):
        with pytest.raises(ValueError):
            GrepConfig(pattern="x", max_count=0)

    def test_matches_returns_true_when_no_pattern(self):
        assert GrepConfig().matches("anything")

    def test_matches_basic_pattern(self):
        cfg = GrepConfig(pattern="error")
        assert cfg.matches("an error occurred")
        assert not cfg.matches("all good")

    def test_matches_ignore_case(self):
        cfg = GrepConfig(pattern="ERROR", ignore_case=True)
        assert cfg.matches("an error occurred")

    def test_matches_invert(self):
        cfg = GrepConfig(pattern="error", invert=True)
        assert not cfg.matches("an error occurred")
        assert cfg.matches("all good")


class TestGrepLines:
    def test_no_pattern_returns_all(self):
        pairs = _pairs(["line one", "line two"])
        result = grep_lines(iter(pairs), GrepConfig())
        assert len(result.matched) == 2
        assert result.total_scanned == 2

    def test_filters_matching_lines(self):
        pairs = _pairs(["error here", "ok line", "another error"])
        result = grep_lines(iter(pairs), GrepConfig(pattern="error"))
        assert len(result.matched) == 2
        assert result.matched[0] == (1, "error here")

    def test_max_count_stops_early(self):
        pairs = _pairs(["err1", "err2", "err3"])
        result = grep_lines(iter(pairs), GrepConfig(pattern="err", max_count=2))
        assert len(result.matched) == 2

    def test_total_scanned_reflects_consumed_input(self):
        pairs = _pairs(["err1", "ok", "err2", "err3"])
        result = grep_lines(iter(pairs), GrepConfig(pattern="err", max_count=2))
        # stops after consuming up to the 3rd line (err2)
        assert result.total_scanned == 3

    def test_invert_match(self):
        pairs = _pairs(["error", "warn", "info"])
        result = grep_lines(iter(pairs), GrepConfig(pattern="error", invert=True))
        assert [t for _, t in result.matched] == ["warn", "info"]


class TestGrepResult:
    def test_as_text_plain(self):
        r = GrepResult(matched=[(1, "hello"), (3, "world")])
        assert r.as_text() == "hello\nworld"

    def test_as_text_numbered(self):
        r = GrepResult(matched=[(1, "hello")])
        text = r.as_text(numbered=True)
        assert "1" in text
        assert "hello" in text

    def test_empty_as_text(self):
        assert GrepResult().as_text() == ""


def test_make_grep_config_defaults():
    cfg = make_grep_config()
    assert not cfg.active


def test_make_grep_config_with_values():
    cfg = make_grep_config(pattern="foo", ignore_case=True, invert=True, max_count=5)
    assert cfg.pattern == "foo"
    assert cfg.ignore_case
    assert cfg.invert
    assert cfg.max_count == 5
