"""Tests for logslice.formatter."""

import io
import json
import pytest

from logslice.formatter import (
    format_plain,
    format_numbered,
    format_jsonl,
    get_formatter,
    write_output,
    SUPPORTED_FORMATS,
)


class TestFormatters:
    def test_plain_returns_line_unchanged(self):
        assert format_plain("hello world\n", 1) == "hello world\n"

    def test_plain_ignores_line_number(self):
        assert format_plain("abc", 99) == "abc"

    def test_numbered_includes_line_number(self):
        result = format_numbered("some log line", 42)
        assert "42" in result
        assert "some log line" in result

    def test_numbered_right_aligns_number(self):
        result = format_numbered("msg", 5)
        assert result.startswith(" ")

    def test_jsonl_is_valid_json(self):
        result = format_jsonl("error occurred\n", 7)
        obj = json.loads(result)
        assert obj["n"] == 7
        assert obj["msg"] == "error occurred"

    def test_jsonl_strips_newline_from_msg(self):
        result = format_jsonl("line\n", 1)
        obj = json.loads(result)
        assert not obj["msg"].endswith("\n")


class TestGetFormatter:
    def test_returns_callable_for_valid_formats(self):
        for fmt in SUPPORTED_FORMATS:
            fn = get_formatter(fmt)
            assert callable(fn)

    def test_raises_for_unknown_format(self):
        with pytest.raises(ValueError, match="Unknown format"):
            get_formatter("xml")


class TestWriteOutput:
    def _lines(self, *items):
        return iter(items)

    def test_plain_output(self):
        buf = io.StringIO()
        count = write_output(self._lines("line1\n", "line2\n"), fmt="plain", out=buf)
        assert count == 2
        assert buf.getvalue() == "line1\nline2\n"

    def test_numbered_output_contains_numbers(self):
        buf = io.StringIO()
        write_output(self._lines("a\n", "b\n"), fmt="numbered", out=buf)
        output = buf.getvalue()
        assert "1" in output
        assert "2" in output

    def test_jsonl_output_each_line_valid_json(self):
        buf = io.StringIO()
        write_output(self._lines("msg1\n", "msg2\n"), fmt="jsonl", out=buf)
        for raw in buf.getvalue().strip().splitlines():
            obj = json.loads(raw)
            assert "n" in obj and "msg" in obj

    def test_start_line_offset(self):
        buf = io.StringIO()
        write_output(self._lines("x\n"), fmt="numbered", out=buf, start_line=100)
        assert "100" in buf.getvalue()

    def test_returns_zero_for_empty_input(self):
        buf = io.StringIO()
        count = write_output(iter([]), out=buf)
        assert count == 0

    def test_newline_appended_if_missing(self):
        buf = io.StringIO()
        write_output(iter(["no newline"]), fmt="plain", out=buf)
        assert buf.getvalue().endswith("\n")
