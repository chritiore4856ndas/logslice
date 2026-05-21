"""Tests for logslice.rotate — rotated log file discovery and reading."""

import gzip
import os
from pathlib import Path

import pytest

from logslice.rotate import RotatedFile, find_rotated_files, iter_rotated_lines


@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, text: str, compressed: bool = False) -> None:
    if compressed:
        with gzip.open(path, 'wt', encoding='utf-8') as fh:
            fh.write(text)
    else:
        path.write_text(text, encoding='utf-8')


class TestFindRotatedFiles:
    def test_only_base_file(self, log_dir):
        base = log_dir / 'app.log'
        _write(base, 'line\n')
        files = find_rotated_files(base)
        assert len(files) == 1
        assert files[0].path == base
        assert files[0].index == 0
        assert files[0].compressed is False

    def test_numbered_variants_discovered(self, log_dir):
        base = log_dir / 'app.log'
        _write(base, 'current\n')
        _write(log_dir / 'app.log.1', 'older\n')
        _write(log_dir / 'app.log.2', 'oldest\n')
        files = find_rotated_files(base)
        indices = [f.index for f in files]
        assert sorted(indices) == [0, 1, 2]

    def test_compressed_variant_detected(self, log_dir):
        base = log_dir / 'srv.log'
        _write(base, 'now\n')
        gz = log_dir / 'srv.log.1.gz'
        _write(gz, 'old\n', compressed=True)
        files = find_rotated_files(base)
        compressed_files = [f for f in files if f.compressed]
        assert len(compressed_files) == 1
        assert compressed_files[0].path == gz

    def test_unrelated_files_ignored(self, log_dir):
        base = log_dir / 'app.log'
        _write(base, 'x\n')
        _write(log_dir / 'other.log', 'y\n')
        _write(log_dir / 'app.log.bak', 'z\n')  # no numeric suffix
        files = find_rotated_files(base)
        paths = [f.path for f in files]
        assert log_dir / 'other.log' not in paths
        assert log_dir / 'app.log.bak' not in paths

    def test_sorted_oldest_first(self, log_dir):
        base = log_dir / 'app.log'
        _write(base, 'current\n')
        _write(log_dir / 'app.log.1', 'one\n')
        _write(log_dir / 'app.log.3', 'three\n')
        _write(log_dir / 'app.log.2', 'two\n')
        files = find_rotated_files(base)
        # oldest (highest index) should come first
        assert files[0].index == 3
        assert files[-1].index == 0


class TestRotatedFileOpen:
    def test_plain_file_readable(self, log_dir):
        p = log_dir / 'test.log'
        _write(p, 'hello\nworld\n')
        rf = RotatedFile(path=p, index=0, compressed=False)
        with rf.open() as fh:
            lines = fh.readlines()
        assert lines == ['hello\n', 'world\n']

    def test_gz_file_readable(self, log_dir):
        p = log_dir / 'test.log.1.gz'
        _write(p, 'compressed line\n', compressed=True)
        rf = RotatedFile(path=p, index=1, compressed=True)
        with rf.open() as fh:
            content = fh.read()
        assert 'compressed line' in content


class TestIterRotatedLines:
    def test_lines_from_all_files_yielded(self, log_dir):
        base = log_dir / 'app.log'
        _write(base, 'current\n')
        _write(log_dir / 'app.log.1', 'older\n')
        lines = list(iter_rotated_lines(base))
        assert 'older\n' in lines
        assert 'current\n' in lines

    def test_oldest_lines_come_first(self, log_dir):
        base = log_dir / 'app.log'
        _write(base, 'new\n')
        _write(log_dir / 'app.log.1', 'old\n')
        lines = list(iter_rotated_lines(base))
        assert lines.index('old\n') < lines.index('new\n')
