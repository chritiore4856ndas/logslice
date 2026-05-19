"""Tests for logslice.progress module."""

from __future__ import annotations

import io
import os
import tempfile
import time

import pytest

from logslice.progress import ProgressReporter, make_reporter


@pytest.fixture
def tmp_file():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as f:
        f.write(b"x" * 1024)
        name = f.name
    yield name
    os.unlink(name)


class TestProgressReporter:
    def _make(self, size=1000, enabled=True):
        buf = io.StringIO()
        return ProgressReporter(file_size=size, stream=buf, enabled=enabled), buf

    def test_update_writes_to_stream(self):
        rep, buf = self._make()
        rep._last_report = 0.0  # force immediate render
        rep.report_interval = 0.0
        rep.update(500)
        assert buf.getvalue() != ""

    def test_update_suppressed_when_disabled(self):
        rep, buf = self._make(enabled=False)
        rep.update(500)
        assert buf.getvalue() == ""

    def test_finish_writes_newline(self):
        rep, buf = self._make()
        rep.finish()
        assert buf.getvalue().endswith("\n")

    def test_finish_no_output_when_disabled(self):
        rep, buf = self._make(enabled=False)
        rep.finish()
        assert buf.getvalue() == ""

    def test_percentage_at_half(self):
        rep, buf = self._make(size=1000)
        rep.report_interval = 0.0
        rep.update(500)
        output = buf.getvalue()
        assert "50.0%" in output

    def test_percentage_caps_at_100(self):
        rep, buf = self._make(size=100)
        rep.report_interval = 0.0
        rep.update(200)  # over-read
        output = buf.getvalue()
        assert "100.0%" in output

    def test_zero_file_size_does_not_crash(self):
        rep, buf = self._make(size=0)
        rep.report_interval = 0.0
        rep.update(0)  # _render returns early
        rep.finish()
        # finish writes newline even for zero-size
        assert buf.getvalue().endswith("\n")

    def test_rate_throttle_skips_render(self):
        rep, buf = self._make()
        rep.report_interval = 9999.0  # very long interval
        rep._last_report = time.monotonic()
        rep.update(500)
        assert buf.getvalue() == ""


class TestMakeReporter:
    def test_uses_file_size(self, tmp_file):
        rep = make_reporter(tmp_file)
        assert rep.file_size == 1024

    def test_missing_file_gives_zero_size(self):
        rep = make_reporter("/nonexistent/path/file.log")
        assert rep.file_size == 0

    def test_disabled_flag_passed_through(self, tmp_file):
        rep = make_reporter(tmp_file, enabled=False)
        assert rep.enabled is False

    def test_custom_stream(self, tmp_file):
        buf = io.StringIO()
        rep = make_reporter(tmp_file, stream=buf)
        assert rep.stream is buf
