"""Tests for timestamp_parser module."""

from datetime import datetime
import pytest

from logslice.timestamp_parser import parse_timestamp, line_in_range


class TestParseTimestamp:
    def test_iso8601_basic(self):
        line = "2024-01-15T13:45:22 INFO server started"
        ts = parse_timestamp(line)
        assert ts == datetime(2024, 1, 15, 13, 45, 22)

    def test_iso8601_with_millis(self):
        line = "2024-01-15T13:45:22.456 DEBUG connection established"
        ts = parse_timestamp(line)
        assert ts is not None
        assert ts.year == 2024 and ts.second == 22

    def test_date_space_time(self):
        line = "2024-03-01 09:00:01.000 ERROR disk full"
        ts = parse_timestamp(line)
        assert ts == datetime(2024, 3, 1, 9, 0, 1)

    def test_syslog_format(self):
        line = "Jan 15 13:45:22 myhost kernel: something happened"
        ts = parse_timestamp(line)
        assert ts is not None
        assert ts.month == 1 and ts.day == 15

    def test_nginx_format(self):
        line = '192.168.1.1 - - [15/Jan/2024:13:45:22 +0000] "GET / HTTP/1.1" 200'
        ts = parse_timestamp(line)
        assert ts is not None
        assert ts.day == 15 and ts.month == 1

    def test_no_timestamp_returns_none(self):
        line = "    at com.example.Main.run(Main.java:42)"
        assert parse_timestamp(line) is None

    def test_empty_line(self):
        assert parse_timestamp("") is None


class TestLineInRange:
    START = datetime(2024, 1, 15, 10, 0, 0)
    END = datetime(2024, 1, 15, 12, 0, 0)

    def test_within_range(self):
        line = "2024-01-15T11:00:00 INFO ok"
        assert line_in_range(line, self.START, self.END) is True

    def test_before_start(self):
        line = "2024-01-15T09:59:59 INFO early"
        assert line_in_range(line, self.START, self.END) is False

    def test_after_end(self):
        line = "2024-01-15T12:00:01 INFO late"
        assert line_in_range(line, self.START, self.END) is False

    def test_no_timestamp_returns_none(self):
        line = "    traceback line without timestamp"
        assert line_in_range(line, self.START, self.END) is None

    def test_open_ended_start_only(self):
        line = "2024-01-15T23:59:59 INFO late night"
        assert line_in_range(line, self.START, None) is True

    def test_open_ended_end_only(self):
        line = "2024-01-15T00:00:01 INFO early morning"
        assert line_in_range(line, None, self.END) is True
