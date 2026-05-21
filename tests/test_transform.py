"""Tests for logslice.transform."""
import pytest

from logslice.transform import (
    TransformConfig,
    make_transform_config,
    transform_line,
)


class TestTransformConfig:
    def test_defaults(self):
        cfg = TransformConfig()
        assert cfg.substitutions == []
        assert cfg.uppercase is False
        assert cfg.lowercase is False
        assert cfg.strip_ansi is False

    def test_not_active_by_default(self):
        cfg = TransformConfig()
        assert cfg.active is False

    def test_active_when_substitution_present(self):
        cfg = make_transform_config(substitutions=[("foo", "bar")])
        assert cfg.active is True

    def test_active_when_uppercase(self):
        cfg = make_transform_config(uppercase=True)
        assert cfg.active is True

    def test_active_when_lowercase(self):
        cfg = make_transform_config(lowercase=True)
        assert cfg.active is True

    def test_active_when_strip_ansi(self):
        cfg = make_transform_config(strip_ansi=True)
        assert cfg.active is True

    def test_both_case_flags_raises(self):
        with pytest.raises(ValueError, match="both"):
            TransformConfig(uppercase=True, lowercase=True)

    def test_invalid_regex_raises(self):
        with pytest.raises(re.error if False else Exception):
            # re.compile is called in __post_init__
            TransformConfig(substitutions=[("[", "x")])


import re  # noqa: E402 — needed for re.error reference above


class TestTransformLine:
    def test_no_op_when_inactive(self):
        cfg = TransformConfig()
        assert transform_line("Hello World", cfg) == "Hello World"

    def test_simple_substitution(self):
        cfg = make_transform_config(substitutions=[("ERROR", "ERR")])
        assert transform_line("ERROR: disk full", cfg) == "ERR: disk full"

    def test_multiple_substitutions_applied_in_order(self):
        cfg = make_transform_config(substitutions=[("foo", "bar"), ("bar", "baz")])
        result = transform_line("foo", cfg)
        assert result == "baz"

    def test_regex_group_reference(self):
        cfg = make_transform_config(substitutions=[(r"(\d+)ms", r"[\1ms]")])
        assert transform_line("took 42ms", cfg) == "took [42ms]"

    def test_uppercase_transform(self):
        cfg = make_transform_config(uppercase=True)
        assert transform_line("hello world", cfg) == "HELLO WORLD"

    def test_lowercase_transform(self):
        cfg = make_transform_config(lowercase=True)
        assert transform_line("HELLO WORLD", cfg) == "hello world"

    def test_strip_ansi_codes(self):
        cfg = make_transform_config(strip_ansi=True)
        colored = "\x1b[31mERROR\x1b[0m: something bad"
        assert transform_line(colored, cfg) == "ERROR: something bad"

    def test_strip_ansi_then_substitute(self):
        cfg = make_transform_config(strip_ansi=True, substitutions=[("ERROR", "ERR")])
        colored = "\x1b[31mERROR\x1b[0m: oops"
        assert transform_line(colored, cfg) == "ERR: oops"

    def test_substitution_then_uppercase(self):
        cfg = make_transform_config(substitutions=[("warn", "warning")], uppercase=True)
        assert transform_line("warn: low disk", cfg) == "WARNING: LOW DISK"

    def test_empty_line_unchanged(self):
        cfg = make_transform_config(uppercase=True)
        assert transform_line("", cfg) == ""
