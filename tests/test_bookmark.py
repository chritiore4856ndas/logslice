"""Tests for logslice.bookmark."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from logslice.bookmark import (
    Bookmark,
    _bookmark_path,
    save_bookmark,
    load_bookmark,
    clear_bookmark,
)


@pytest.fixture()
def bm_dir(tmp_path, monkeypatch):
    """Redirect bookmark storage to a temp directory."""
    import logslice.bookmark as bm_mod
    fake_dir = tmp_path / "bookmarks"
    monkeypatch.setattr(bm_mod, "_BOOKMARK_DIR", fake_dir)
    return fake_dir


class TestBookmark:
    def test_as_dict_contains_all_fields(self):
        bm = Bookmark(log_path="/var/log/app.log", byte_offset=1024,
                      last_timestamp="2024-01-01T00:00:00", line_number=42)
        d = bm.as_dict()
        assert d["log_path"] == "/var/log/app.log"
        assert d["byte_offset"] == 1024
        assert d["last_timestamp"] == "2024-01-01T00:00:00"
        assert d["line_number"] == 42

    def test_optional_fields_default_to_none_or_zero(self):
        bm = Bookmark(log_path="/tmp/x.log", byte_offset=0)
        assert bm.last_timestamp is None
        assert bm.line_number == 0


def test_bookmark_path_is_deterministic(bm_dir):
    p1 = _bookmark_path("/var/log/app.log")
    p2 = _bookmark_path("/var/log/app.log")
    assert p1 == p2


def test_bookmark_path_differs_for_different_files(bm_dir):
    assert _bookmark_path("/a.log") != _bookmark_path("/b.log")


def test_save_creates_file(bm_dir):
    bm = Bookmark(log_path="/tmp/test.log", byte_offset=512)
    dest = save_bookmark(bm)
    assert dest.exists()


def test_save_writes_valid_json(bm_dir):
    bm = Bookmark(log_path="/tmp/test.log", byte_offset=256, line_number=10)
    dest = save_bookmark(bm)
    data = json.loads(dest.read_text())
    assert data["byte_offset"] == 256
    assert data["line_number"] == 10


def test_load_returns_none_when_no_bookmark(bm_dir):
    assert load_bookmark("/nonexistent/file.log") is None


def test_load_round_trips_bookmark(bm_dir):
    bm = Bookmark(log_path="/tmp/rt.log", byte_offset=999,
                  last_timestamp="2024-06-15T12:00:00", line_number=77)
    save_bookmark(bm)
    loaded = load_bookmark("/tmp/rt.log")
    assert loaded is not None
    assert loaded.byte_offset == 999
    assert loaded.last_timestamp == "2024-06-15T12:00:00"
    assert loaded.line_number == 77


def test_load_returns_none_on_corrupt_file(bm_dir):
    import logslice.bookmark as bm_mod
    p = _bookmark_path("/tmp/bad.log")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("not json at all")
    assert load_bookmark("/tmp/bad.log") is None


def test_clear_returns_true_when_bookmark_existed(bm_dir):
    bm = Bookmark(log_path="/tmp/clear.log", byte_offset=0)
    save_bookmark(bm)
    assert clear_bookmark("/tmp/clear.log") is True


def test_clear_returns_false_when_no_bookmark(bm_dir):
    assert clear_bookmark("/tmp/ghost.log") is False


def test_clear_removes_file(bm_dir):
    bm = Bookmark(log_path="/tmp/del.log", byte_offset=0)
    dest = save_bookmark(bm)
    clear_bookmark("/tmp/del.log")
    assert not dest.exists()
