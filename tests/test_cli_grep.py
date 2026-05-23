"""Tests for logslice.cli_grep."""
from __future__ import annotations

import argparse

import pytest

from logslice.cli_grep import add_grep_args, build_grep_config


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_grep_args(p)
    return p


class TestAddGrepArgs:
    def test_default_no_pattern(self):
        args = _parser().parse_args([])
        assert args.grep is None

    def test_short_flag(self):
        args = _parser().parse_args(["-g", "error"])
        assert args.grep == "error"

    def test_long_flag(self):
        args = _parser().parse_args(["--grep", "warn"])
        assert args.grep == "warn"

    def test_ignore_case_default_false(self):
        args = _parser().parse_args([])
        assert args.ignore_case is False

    def test_ignore_case_flag(self):
        args = _parser().parse_args(["-i"])
        assert args.ignore_case is True

    def test_invert_default_false(self):
        args = _parser().parse_args([])
        assert args.invert_match is False

    def test_invert_flag(self):
        args = _parser().parse_args(["-v"])
        assert args.invert_match is True

    def test_grep_max_default_none(self):
        args = _parser().parse_args([])
        assert args.grep_max is None

    def test_grep_max_value(self):
        args = _parser().parse_args(["--grep-max", "10"])
        assert args.grep_max == 10


class TestBuildGrepConfig:
    def test_no_flags_gives_inactive_config(self):
        args = _parser().parse_args([])
        cfg = build_grep_config(args)
        assert not cfg.active

    def test_pattern_transferred(self):
        args = _parser().parse_args(["-g", "timeout"])
        cfg = build_grep_config(args)
        assert cfg.pattern == "timeout"

    def test_ignore_case_transferred(self):
        args = _parser().parse_args(["-g", "x", "-i"])
        cfg = build_grep_config(args)
        assert cfg.ignore_case is True

    def test_invert_transferred(self):
        args = _parser().parse_args(["-g", "x", "-v"])
        cfg = build_grep_config(args)
        assert cfg.invert is True

    def test_max_count_transferred(self):
        args = _parser().parse_args(["-g", "x", "--grep-max", "3"])
        cfg = build_grep_config(args)
        assert cfg.max_count == 3

    def test_combined_flags(self):
        args = _parser().parse_args(["-g", "ERR", "-i", "-v", "--grep-max", "5"])
        cfg = build_grep_config(args)
        assert cfg.pattern == "ERR"
        assert cfg.ignore_case
        assert cfg.invert
        assert cfg.max_count == 5
