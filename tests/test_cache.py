"""Tests for logslice.cache module."""

import os
import json
import time
import tempfile
import pytest

from logslice.cache import (
    IndexEntry,
    load_cache,
    save_cache,
    invalidate_cache,
    _cache_path,
    CACHE_DIR,
)


@pytest.fixture
def tmp_log(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("2024-01-01 00:00:00 hello\n2024-01-01 00:01:00 world\n")
    return str(log)


def make_entry(file_path):
    stat = os.stat(file_path)
    return IndexEntry(
        file_path=file_path,
        file_size=stat.st_size,
        file_mtime=stat.st_mtime,
        offsets=[("2024-01-01T00:00:00", 0), ("2024-01-01T00:01:00", 26)],
    )


class TestIndexEntry:
    def test_is_valid_returns_true_for_unchanged_file(self, tmp_log):
        entry = make_entry(tmp_log)
        assert entry.is_valid_for(tmp_log) is True

    def test_is_valid_returns_false_after_modification(self, tmp_log):
        entry = make_entry(tmp_log)
        with open(tmp_log, "a") as f:
            f.write("extra line\n")
        assert entry.is_valid_for(tmp_log) is False

    def test_is_valid_returns_false_for_missing_file(self, tmp_log):
        entry = make_entry(tmp_log)
        os.remove(tmp_log)
        assert entry.is_valid_for(tmp_log) is False


class TestLoadSaveCache:
    def test_save_and_load_roundtrip(self, tmp_log, monkeypatch, tmp_path):
        monkeypatch.setattr("logslice.cache.CACHE_DIR", str(tmp_path))
        import logslice.cache as cache_mod
        cache_mod.CACHE_DIR = str(tmp_path)

        entry = make_entry(tmp_log)
        save_cache(entry)
        loaded = load_cache(tmp_log)
        assert loaded is not None
        assert loaded.offsets == entry.offsets
        assert loaded.file_size == entry.file_size

    def test_load_returns_none_for_unknown_file(self, tmp_path):
        result = load_cache(str(tmp_path / "nonexistent.log"))
        assert result is None

    def test_load_returns_none_when_cache_stale(self, tmp_log, monkeypatch, tmp_path):
        monkeypatch.setattr("logslice.cache.CACHE_DIR", str(tmp_path))
        import logslice.cache as cache_mod
        cache_mod.CACHE_DIR = str(tmp_path)

        entry = make_entry(tmp_log)
        save_cache(entry)
        with open(tmp_log, "a") as f:
            f.write("new line\n")
        assert load_cache(tmp_log) is None

    def test_invalidate_removes_cache_file(self, tmp_log, monkeypatch, tmp_path):
        monkeypatch.setattr("logslice.cache.CACHE_DIR", str(tmp_path))
        import logslice.cache as cache_mod
        cache_mod.CACHE_DIR = str(tmp_path)

        entry = make_entry(tmp_log)
        save_cache(entry)
        invalidate_cache(tmp_log)
        assert load_cache(tmp_log) is None

    def test_save_handles_unwritable_dir_gracefully(self, tmp_log, monkeypatch):
        monkeypatch.setattr("logslice.cache.CACHE_DIR", "/nonexistent/path/xyz")
        import logslice.cache as cache_mod
        cache_mod.CACHE_DIR = "/nonexistent/path/xyz"
        entry = make_entry(tmp_log)
        save_cache(entry)  # should not raise
