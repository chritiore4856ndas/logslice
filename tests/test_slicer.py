"""Tests for the binary-search slicer core."""

import io
import os
import tempfile
import pytest

from logslice.slicer import _find_line_start, _read_line_at, _binary_search_start, slice_log


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_log(lines):
    """Write *lines* to a NamedTemporaryFile and return its path.

    The caller is responsible for deleting the file.
    """
    tf = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False)
    for line in lines:
        tf.write(line + "\n")
    tf.flush()
    tf.close()
    return tf.name


SAMPLE_LINES = [
    "2024-01-01T00:00:00 startup",
    "2024-01-01T01:00:00 event A",
    "2024-01-01T02:00:00 event B",
    "2024-01-01T03:00:00 event C",
    "2024-01-01T04:00:00 event D",
    "2024-01-01T05:00:00 shutdown",
]


@pytest.fixture()
def sample_log(tmp_path):
    path = tmp_path / "sample.log"
    path.write_text("\n".join(SAMPLE_LINES) + "\n")
    return str(path)


# ---------------------------------------------------------------------------
# _find_line_start
# ---------------------------------------------------------------------------

class TestFindLineStart:
    def test_offset_zero_returns_zero(self, sample_log):
        with open(sample_log, "rb") as fh:
            assert _find_line_start(fh, 0) == 0

    def test_mid_line_offset_backs_up_to_start(self, sample_log):
        with open(sample_log, "rb") as fh:
            # Jump into the middle of the first line and expect offset 0 back.
            result = _find_line_start(fh, 10)
            assert result == 0

    def test_exact_line_boundary(self, sample_log):
        with open(sample_log, "rb") as fh:
            # Find byte offset of second line.
            fh.seek(0)
            first_line = fh.readline()
            second_line_offset = fh.tell()
            # Passing that exact offset should return the same offset.
            assert _find_line_start(fh, second_line_offset) == second_line_offset


# ---------------------------------------------------------------------------
# _read_line_at
# ---------------------------------------------------------------------------

class TestReadLineAt:
    def test_reads_first_line(self, sample_log):
        with open(sample_log, "rb") as fh:
            line = _read_line_at(fh, 0)
        assert line.startswith("2024-01-01T00:00:00")

    def test_reads_line_at_known_offset(self, sample_log):
        with open(sample_log, "rb") as fh:
            fh.seek(0)
            first = fh.readline()
            offset = fh.tell()
            line = _read_line_at(fh, offset)
        assert "event A" in line

    def test_returns_none_at_eof(self, sample_log):
        size = os.path.getsize(sample_log)
        with open(sample_log, "rb") as fh:
            result = _read_line_at(fh, size)
        assert result is None


# ---------------------------------------------------------------------------
# _binary_search_start
# ---------------------------------------------------------------------------

class TestBinarySearchStart:
    def test_finds_exact_timestamp(self, sample_log):
        from datetime import datetime, timezone
        target = datetime(2024, 1, 1, 2, 0, 0, tzinfo=timezone.utc)
        with open(sample_log, "rb") as fh:
            offset = _binary_search_start(fh, target)
        assert offset >= 0
        with open(sample_log, "rb") as fh:
            fh.seek(offset)
            line = fh.readline().decode()
        assert "event B" in line or "event A" in line or "2024-01-01T02" in line

    def test_returns_zero_when_target_before_all(self, sample_log):
        from datetime import datetime, timezone
        target = datetime(2023, 1, 1, tzinfo=timezone.utc)
        with open(sample_log, "rb") as fh:
            offset = _binary_search_start(fh, target)
        assert offset == 0


# ---------------------------------------------------------------------------
# slice_log  (integration)
# ---------------------------------------------------------------------------

class TestSliceLog:
    def test_returns_lines_in_range(self, sample_log):
        from datetime import datetime, timezone
        start = datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc)
        lines = list(slice_log(sample_log, start, end))
        texts = [l for l in lines]
        assert any("event A" in t for t in texts)
        assert any("event B" in t for t in texts)
        assert not any("startup" in t for t in texts)
        assert not any("event D" in t for t in texts)

    def test_empty_range_returns_nothing(self, sample_log):
        from datetime import datetime, timezone
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 6, 1, tzinfo=timezone.utc)
        lines = list(slice_log(sample_log, start, end))
        assert lines == []

    def test_full_range_returns_all_lines(self, sample_log):
        from datetime import datetime, timezone
        start = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 1, 1, tzinfo=timezone.utc)
        lines = list(slice_log(sample_log, start, end))
        assert len(lines) == len(SAMPLE_LINES)

    def test_yields_strings(self, sample_log):
        from datetime import datetime, timezone
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 1, 6, 0, 0, tzinfo=timezone.utc)
        for line in slice_log(sample_log, start, end):
            assert isinstance(line, str)
