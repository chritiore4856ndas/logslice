"""Tests for logslice.tail."""

from __future__ import annotations

import os
import tempfile

import pytest

from logslice.tail import TailResult, tail_lines


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write(lines: list[str]) -> str:
    """Write *lines* to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".log")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.writelines(lines)
    return path


@pytest.fixture()
def ten_line_log(tmp_path):
    p = tmp_path / "ten.log"
    p.write_text("".join(f"line {i}\n" for i in range(1, 11)), encoding="utf-8")
    return str(p)


# ---------------------------------------------------------------------------
# TailResult
# ---------------------------------------------------------------------------

class TestTailResult:
    def test_as_text_joins_lines(self):
        tr = TailResult(lines=["a\n", "b\n"])
        assert tr.as_text() == "a\nb\n"

    def test_empty_as_text(self):
        assert TailResult().as_text() == ""


# ---------------------------------------------------------------------------
# tail_lines
# ---------------------------------------------------------------------------

class TestTailLines:
    def test_returns_last_n_lines(self, ten_line_log):
        result = tail_lines(ten_line_log, 3)
        assert len(result.lines) == 3
        assert result.lines[-1] == "line 10\n"
        assert result.lines[0] == "line 8\n"

    def test_n_larger_than_file_returns_all(self, ten_line_log):
        result = tail_lines(ten_line_log, 50)
        assert len(result.lines) == 10
        assert result.lines[0] == "line 1\n"

    def test_n_zero_returns_empty(self, ten_line_log):
        result = tail_lines(ten_line_log, 0)
        assert result.lines == []

    def test_empty_file_returns_empty(self, tmp_path):
        p = tmp_path / "empty.log"
        p.write_bytes(b"")
        result = tail_lines(str(p), 5)
        assert result.lines == []

    def test_single_line_no_newline(self, tmp_path):
        p = tmp_path / "single.log"
        p.write_text("only line", encoding="utf-8")
        result = tail_lines(str(p), 1)
        assert len(result.lines) == 1
        assert "only line" in result.lines[0]

    def test_small_chunk_size_same_result(self, ten_line_log):
        normal = tail_lines(ten_line_log, 4)
        small = tail_lines(ten_line_log, 4, chunk_size=16)
        assert normal.lines == small.lines

    def test_bytes_read_is_positive(self, ten_line_log):
        result = tail_lines(ten_line_log, 3)
        assert result.bytes_read > 0

    def test_chunks_read_increases_with_small_chunk(self, ten_line_log):
        big = tail_lines(ten_line_log, 5, chunk_size=8192)
        small = tail_lines(ten_line_log, 5, chunk_size=8)
        assert small.chunks_read >= big.chunks_read
