"""Tests for logslice.highlight."""
import pytest

from logslice.highlight import (
    ANSI_RESET,
    ANSI_COLORS,
    HighlightConfig,
    highlight_line,
    make_highlight_config,
)


class TestHighlightConfig:
    def test_defaults(self):
        cfg = HighlightConfig()
        assert cfg.terms == []
        assert cfg.color == "yellow"
        assert cfg.case_sensitive is False

    def test_active_when_terms_present(self):
        cfg = HighlightConfig(terms=["error"])
        assert cfg.active is True

    def test_not_active_when_no_terms(self):
        cfg = HighlightConfig(terms=[])
        assert cfg.active is False

    def test_invalid_color_raises(self):
        with pytest.raises(ValueError, match="Unknown color"):
            HighlightConfig(terms=["x"], color="purple")

    def test_valid_colors_accepted(self):
        for color in ANSI_COLORS:
            cfg = HighlightConfig(terms=["x"], color=color)
            assert cfg.color == color


class TestHighlightLine:
    def test_no_terms_returns_line_unchanged(self):
        cfg = make_highlight_config()
        line = "2024-01-01 ERROR something went wrong"
        assert highlight_line(line, cfg) == line

    def test_matching_term_is_wrapped(self):
        cfg = make_highlight_config(terms=["ERROR"])
        result = highlight_line("prefix ERROR suffix", cfg)
        assert ANSI_COLORS["yellow"] in result
        assert ANSI_RESET in result
        assert "ERROR" in result

    def test_non_matching_term_leaves_line_unchanged(self):
        cfg = make_highlight_config(terms=["CRITICAL"])
        line = "INFO nothing special here"
        assert highlight_line(line, cfg) == line

    def test_case_insensitive_by_default(self):
        cfg = make_highlight_config(terms=["error"])
        result = highlight_line("An ERROR occurred", cfg)
        assert ANSI_COLORS["yellow"] in result

    def test_case_sensitive_no_match(self):
        cfg = make_highlight_config(terms=["error"], case_sensitive=True)
        line = "An ERROR occurred"
        assert highlight_line(line, cfg) == line

    def test_case_sensitive_match(self):
        cfg = make_highlight_config(terms=["ERROR"], case_sensitive=True)
        result = highlight_line("An ERROR occurred", cfg)
        assert ANSI_COLORS["yellow"] in result

    def test_multiple_terms_all_highlighted(self):
        cfg = make_highlight_config(terms=["foo", "bar"])
        result = highlight_line("foo and bar are here", cfg)
        assert result.count(ANSI_RESET) == 2

    def test_custom_color_used(self):
        cfg = make_highlight_config(terms=["warn"], color="red")
        result = highlight_line("warn: disk full", cfg)
        assert ANSI_COLORS["red"] in result

    def test_make_highlight_config_none_terms(self):
        cfg = make_highlight_config(terms=None)
        assert cfg.terms == []
        assert cfg.active is False
