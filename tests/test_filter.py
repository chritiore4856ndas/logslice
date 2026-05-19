"""Tests for logslice.filter module."""

import pytest
from logslice.filter import LineFilter, make_filter


class TestLineFilter:
    def test_no_criteria_is_not_active(self):
        f = LineFilter()
        assert not f.active

    def test_keyword_makes_filter_active(self):
        f = LineFilter(keyword="error")
        assert f.active

    def test_pattern_makes_filter_active(self):
        f = LineFilter(pattern=r"\d+")
        assert f.active

    def test_matches_returns_true_when_no_criteria(self):
        f = LineFilter()
        assert f.matches("any line at all")

    def test_keyword_match(self):
        f = LineFilter(keyword="ERROR")
        assert f.matches("2024-01-01 ERROR something failed")
        assert not f.matches("2024-01-01 INFO all good")

    def test_keyword_case_insensitive(self):
        f = LineFilter(keyword="error", ignore_case=True)
        assert f.matches("2024-01-01 ERROR something")
        assert f.matches("2024-01-01 error something")

    def test_keyword_case_sensitive_by_default(self):
        f = LineFilter(keyword="error")
        assert not f.matches("2024-01-01 ERROR something")

    def test_regex_match(self):
        f = LineFilter(pattern=r"user_id=\d+")
        assert f.matches("login user_id=42 success")
        assert not f.matches("login anonymous success")

    def test_regex_case_insensitive(self):
        f = LineFilter(pattern=r"error", ignore_case=True)
        assert f.matches("ERROR occurred")
        assert f.matches("error occurred")

    def test_invalid_regex_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            LineFilter(pattern=r"[unclosed")

    def test_both_keyword_and_pattern_must_match(self):
        f = LineFilter(keyword="timeout", pattern=r"user_id=\d+")
        assert f.matches("user_id=7 timeout error")
        assert not f.matches("user_id=7 success")  # keyword missing
        assert not f.matches("timeout without id")  # pattern missing

    def test_matches_empty_line_no_criteria(self):
        f = LineFilter()
        assert f.matches("")

    def test_keyword_not_in_empty_line(self):
        f = LineFilter(keyword="error")
        assert not f.matches("")


class TestMakeFilter:
    def test_returns_none_when_no_args(self):
        assert make_filter() is None

    def test_returns_filter_with_keyword(self):
        f = make_filter(keyword="warn")
        assert f is not None
        assert f.active

    def test_returns_filter_with_pattern(self):
        f = make_filter(pattern=r"\bERROR\b")
        assert f is not None
        assert f.active

    def test_passes_ignore_case(self):
        f = make_filter(keyword="error", ignore_case=True)
        assert f is not None
        assert f.matches("ERROR line")
