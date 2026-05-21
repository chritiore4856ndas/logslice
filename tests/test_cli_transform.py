"""Tests for logslice.cli_transform."""
import argparse
import pytest

from logslice.cli_transform import (
    add_transform_args,
    build_transform_config,
    parse_substitution,
)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_transform_args(p)
    return p


class TestParseSubstitution:
    def test_simple(self):
        assert parse_substitution("foo=bar") == ("foo", "bar")

    def test_replacement_contains_equals(self):
        assert parse_substitution("a=b=c") == ("a", "b=c")

    def test_empty_replacement(self):
        assert parse_substitution("foo=") == ("foo", "")

    def test_missing_equals_raises(self):
        with pytest.raises(argparse.ArgumentTypeError):
            parse_substitution("nodivider")


class TestAddTransformArgs:
    def test_defaults(self):
        args = _parser().parse_args([])
        assert args.substitutions == []
        assert args.uppercase is False
        assert args.lowercase is False
        assert args.strip_ansi is False

    def test_uppercase_flag(self):
        args = _parser().parse_args(["--uppercase"])
        assert args.uppercase is True

    def test_lowercase_flag(self):
        args = _parser().parse_args(["--lowercase"])
        assert args.lowercase is True

    def test_strip_ansi_flag(self):
        args = _parser().parse_args(["--strip-ansi"])
        assert args.strip_ansi is True

    def test_single_sub(self):
        args = _parser().parse_args(["--sub", "ERROR=ERR"])
        assert args.substitutions == ["ERROR=ERR"]

    def test_multiple_subs(self):
        args = _parser().parse_args(["--sub", "a=b", "--sub", "c=d"])
        assert args.substitutions == ["a=b", "c=d"]


class TestBuildTransformConfig:
    def test_empty_args_gives_inactive_config(self):
        args = _parser().parse_args([])
        cfg = build_transform_config(args)
        assert cfg.active is False

    def test_uppercase_propagated(self):
        args = _parser().parse_args(["--uppercase"])
        cfg = build_transform_config(args)
        assert cfg.uppercase is True

    def test_lowercase_propagated(self):
        args = _parser().parse_args(["--lowercase"])
        cfg = build_transform_config(args)
        assert cfg.lowercase is True

    def test_strip_ansi_propagated(self):
        args = _parser().parse_args(["--strip-ansi"])
        cfg = build_transform_config(args)
        assert cfg.strip_ansi is True

    def test_substitutions_parsed(self):
        args = _parser().parse_args(["--sub", "foo=bar"])
        cfg = build_transform_config(args)
        assert cfg.substitutions == [("foo", "bar")]
        assert cfg.active is True

    def test_both_case_flags_raises_at_config_level(self):
        args = _parser().parse_args(["--uppercase", "--lowercase"])
        with pytest.raises(ValueError):
            build_transform_config(args)
