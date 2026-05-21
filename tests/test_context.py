"""Tests for logslice.context."""
import pytest
from logslice.context import ContextConfig, collect_with_context, make_context_config


def _pairs(*flags: bool) -> list:
    """Build (lineno, text, matched) list from a sequence of bool flags."""
    return [(i + 1, f"line{i + 1}", flags[i]) for i in range(len(flags))]


class TestContextConfig:
    def test_defaults(self):
        cfg = ContextConfig()
        assert cfg.before == 0
        assert cfg.after == 0

    def test_not_active_when_zero(self):
        assert not ContextConfig().active

    def test_active_when_before_set(self):
        assert ContextConfig(before=2).active

    def test_active_when_after_set(self):
        assert ContextConfig(after=1).active

    def test_negative_before_raises(self):
        with pytest.raises(ValueError, match="before"):
            ContextConfig(before=-1)

    def test_negative_after_raises(self):
        with pytest.raises(ValueError, match="after"):
            ContextConfig(after=-1)

    def test_make_context_config_factory(self):
        cfg = make_context_config(before=1, after=2)
        assert cfg.before == 1 and cfg.after == 2


class TestIterWithContext:
    def test_no_context_passthrough(self):
        data = _pairs(True, False, True)
        cfg = ContextConfig()
        result = collect_with_context(data, cfg)
        assert result == data

    def test_after_context_includes_following_lines(self):
        data = _pairs(True, False, False)
        cfg = ContextConfig(after=2)
        result = collect_with_context(data, cfg)
        linenos = [r[0] for r in result]
        assert linenos == [1, 2, 3]

    def test_after_context_does_not_exceed_available(self):
        data = _pairs(False, True)
        cfg = ContextConfig(after=5)
        result = collect_with_context(data, cfg)
        linenos = [r[0] for r in result]
        assert linenos == [2]

    def test_before_context_includes_preceding_lines(self):
        data = _pairs(False, False, True)
        cfg = ContextConfig(before=2)
        result = collect_with_context(data, cfg)
        linenos = [r[0] for r in result]
        assert 1 in linenos
        assert 2 in linenos
        assert 3 in linenos

    def test_before_context_limited_by_available(self):
        data = _pairs(False, True)
        cfg = ContextConfig(before=5)
        result = collect_with_context(data, cfg)
        linenos = [r[0] for r in result]
        assert linenos == [1, 2]

    def test_no_duplicate_lines_when_windows_overlap(self):
        # match at 2 (after=2) and match at 4 (before=2) overlap at line 3/4
        data = _pairs(False, True, False, True, False)
        cfg = ContextConfig(before=2, after=2)
        result = collect_with_context(data, cfg)
        linenos = [r[0] for r in result]
        assert linenos == sorted(set(linenos)), "duplicate line numbers emitted"

    def test_unmatched_lines_not_emitted_without_context(self):
        data = _pairs(False, False, False)
        cfg = ContextConfig(before=0, after=0)
        result = collect_with_context(data, cfg)
        assert result == []

    def test_context_lines_have_matched_false(self):
        data = _pairs(False, True, False)
        cfg = ContextConfig(before=1, after=1)
        result = collect_with_context(data, cfg)
        by_lineno = {r[0]: r[2] for r in result}
        assert by_lineno[2] is True
        assert by_lineno.get(1) is False or 1 not in by_lineno or by_lineno[1] is False
