"""Tests for logslice.sampler."""

import pytest

from logslice.sampler import ReservoirSampler, SampleResult, sample_lines


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pairs(n: int):
    return [(i, f"line {i}") for i in range(1, n + 1)]


# ---------------------------------------------------------------------------
# SampleResult
# ---------------------------------------------------------------------------

class TestSampleResult:
    def test_as_text_plain(self):
        sr = SampleResult(lines=[(1, "hello"), (3, "world")], total_seen=5, sample_size=2)
        assert sr.as_text() == "hello\nworld"

    def test_as_text_numbered(self):
        sr = SampleResult(lines=[(1, "hello"), (3, "world")], total_seen=5, sample_size=2)
        text = sr.as_text(numbered=True)
        assert "1" in text
        assert "hello" in text
        assert "3" in text
        assert "world" in text

    def test_empty_as_text(self):
        sr = SampleResult()
        assert sr.as_text() == ""


# ---------------------------------------------------------------------------
# ReservoirSampler
# ---------------------------------------------------------------------------

class TestReservoirSampler:
    def test_invalid_k_raises(self):
        with pytest.raises(ValueError):
            ReservoirSampler(0)

    def test_fewer_lines_than_k_returns_all(self):
        sampler = ReservoirSampler(10)
        for lineno, text in _pairs(5):
            sampler.feed(lineno, text)
        result = sampler.result()
        assert result.total_seen == 5
        assert result.sample_size == 5
        assert [ln for ln, _ in result.lines] == [1, 2, 3, 4, 5]

    def test_more_lines_than_k_returns_k(self):
        sampler = ReservoirSampler(5)
        for lineno, text in _pairs(100):
            sampler.feed(lineno, text)
        result = sampler.result()
        assert result.total_seen == 100
        assert result.sample_size == 5

    def test_result_is_sorted_by_lineno(self):
        sampler = ReservoirSampler(10)
        sampler._rng.seed(42)
        for lineno, text in _pairs(50):
            sampler.feed(lineno, text)
        result = sampler.result()
        line_numbers = [ln for ln, _ in result.lines]
        assert line_numbers == sorted(line_numbers)

    def test_empty_feed_returns_empty_result(self):
        sampler = ReservoirSampler(5)
        result = sampler.result()
        assert result.total_seen == 0
        assert result.sample_size == 0
        assert result.lines == []


# ---------------------------------------------------------------------------
# sample_lines helper
# ---------------------------------------------------------------------------

class TestSampleLines:
    def test_deterministic_with_seed(self):
        pairs = _pairs(200)
        r1 = sample_lines(pairs, k=10, seed=7)
        r2 = sample_lines(pairs, k=10, seed=7)
        assert r1.lines == r2.lines

    def test_different_seeds_may_differ(self):
        pairs = _pairs(200)
        r1 = sample_lines(pairs, k=10, seed=1)
        r2 = sample_lines(pairs, k=10, seed=999)
        # With 200 lines and k=10 it is astronomically unlikely they match
        assert r1.lines != r2.lines

    def test_k_larger_than_input_returns_all(self):
        pairs = _pairs(3)
        result = sample_lines(pairs, k=50, seed=0)
        assert result.sample_size == 3
