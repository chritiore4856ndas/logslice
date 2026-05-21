"""Tests for logslice.dedup."""

from __future__ import annotations

import pytest

from logslice.dedup import Deduplicator, DedupStats, make_deduplicator


class TestDedupStats:
    def test_unique_is_total_minus_duplicates(self):
        s = DedupStats(total=10, duplicates=3)
        assert s.unique == 7

    def test_as_dict_keys(self):
        s = DedupStats(total=5, duplicates=2)
        d = s.as_dict()
        assert set(d.keys()) == {"total", "unique", "duplicates"}
        assert d["unique"] == 3


class TestDeduplicator:
    def test_disabled_never_reports_duplicate(self):
        d = Deduplicator(enabled=False)
        assert d.is_duplicate("hello\n") is False
        assert d.is_duplicate("hello\n") is False

    def test_first_occurrence_is_not_duplicate(self):
        d = Deduplicator()
        assert d.is_duplicate("line one\n") is False

    def test_second_occurrence_is_duplicate(self):
        d = Deduplicator()
        d.is_duplicate("line one\n")
        assert d.is_duplicate("line one\n") is True

    def test_different_lines_not_duplicate(self):
        d = Deduplicator()
        d.is_duplicate("alpha\n")
        assert d.is_duplicate("beta\n") is False

    def test_stats_total_increments(self):
        d = Deduplicator()
        d.is_duplicate("a\n")
        d.is_duplicate("a\n")
        d.is_duplicate("b\n")
        assert d.stats.total == 3
        assert d.stats.duplicates == 1
        assert d.stats.unique == 2

    def test_window_evicts_old_hashes(self):
        d = Deduplicator(window=2)
        d.is_duplicate("line1\n")  # slot 0
        d.is_duplicate("line2\n")  # slot 1
        d.is_duplicate("line3\n")  # evicts line1
        # line1 should have been evicted, so not a duplicate now
        assert d.is_duplicate("line1\n") is False

    def test_window_still_catches_recent_dup(self):
        d = Deduplicator(window=3)
        d.is_duplicate("line1\n")
        d.is_duplicate("line2\n")
        assert d.is_duplicate("line2\n") is True

    def test_filter_yields_unique_lines(self):
        d = Deduplicator()
        lines = ["a\n", "b\n", "a\n", "c\n", "b\n", "d\n"]
        result = list(d.filter(iter(lines)))
        assert result == ["a\n", "b\n", "c\n", "d\n"]

    def test_filter_disabled_yields_all(self):
        d = Deduplicator(enabled=False)
        lines = ["x\n", "x\n", "x\n"]
        assert list(d.filter(iter(lines))) == lines

    def test_trailing_newline_ignored_in_hash(self):
        d = Deduplicator()
        d.is_duplicate("hello\n")
        # Same content without newline should still be a dup
        assert d.is_duplicate("hello") is True


def test_make_deduplicator_defaults():
    d = make_deduplicator()
    assert d.enabled is False
    assert d.window is None


def test_make_deduplicator_enabled():
    d = make_deduplicator(enabled=True, window=100)
    assert d.enabled is True
    assert d.window == 100
