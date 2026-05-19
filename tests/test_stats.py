"""Tests for logslice.stats."""

import time
from datetime import datetime, timezone

import pytest

from logslice.stats import SliceStats


DT1 = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
DT2 = datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc)


class TestSliceStats:
    def test_initial_state(self):
        s = SliceStats()
        assert s.total_lines == 0
        assert s.matched_lines == 0
        assert s.skipped_lines == 0
        assert s.first_timestamp is None
        assert s.last_timestamp is None

    def test_record_matched_line_increments_counters(self):
        s = SliceStats()
        s.record_line(matched=True, ts=DT1)
        assert s.total_lines == 1
        assert s.matched_lines == 1
        assert s.skipped_lines == 0

    def test_record_skipped_line_increments_counters(self):
        s = SliceStats()
        s.record_line(matched=False)
        assert s.total_lines == 1
        assert s.matched_lines == 0
        assert s.skipped_lines == 1

    def test_first_and_last_timestamp_tracked(self):
        s = SliceStats()
        s.record_line(matched=True, ts=DT1)
        s.record_line(matched=True, ts=DT2)
        assert s.first_timestamp == DT1
        assert s.last_timestamp == DT2

    def test_skipped_lines_do_not_update_timestamps(self):
        s = SliceStats()
        s.record_line(matched=True, ts=DT1)
        s.record_line(matched=False, ts=DT2)
        assert s.first_timestamp == DT1
        assert s.last_timestamp == DT1

    def test_matched_line_without_timestamp_does_not_crash(self):
        s = SliceStats()
        s.record_line(matched=True, ts=None)
        assert s.matched_lines == 1
        assert s.first_timestamp is None

    def test_elapsed_seconds_after_stop(self):
        s = SliceStats()
        s.start()
        time.sleep(0.05)
        s.stop()
        assert s.elapsed_seconds >= 0.04

    def test_as_dict_keys(self):
        s = SliceStats(file_size_bytes=1024)
        s.record_line(matched=True, ts=DT1)
        d = s.as_dict()
        assert set(d.keys()) == {
            "total_lines", "matched_lines", "skipped_lines",
            "first_timestamp", "last_timestamp",
            "file_size_bytes", "elapsed_seconds",
        }
        assert d["file_size_bytes"] == 1024
        assert d["first_timestamp"] == DT1.isoformat()

    def test_as_dict_null_timestamps_when_no_matches(self):
        s = SliceStats()
        d = s.as_dict()
        assert d["first_timestamp"] is None
        assert d["last_timestamp"] is None

    def test_summary_contains_key_info(self):
        s = SliceStats(file_size_bytes=500)
        s.record_line(matched=True, ts=DT1)
        s.record_line(matched=False)
        s.stop()
        summary = s.summary()
        assert "1/2" in summary
        assert "500" in summary
