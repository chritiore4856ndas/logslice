"""Tests for logslice.rate."""

import pytest
from datetime import datetime, timezone
from logslice.rate import RateConfig, RateLimiter, make_rate_config, apply_rate_limit


def _dt(second: int, minute: int = 0) -> datetime:
    return datetime(2024, 1, 1, 0, minute, second, tzinfo=timezone.utc)


class TestRateConfig:
    def test_defaults(self):
        cfg = RateConfig()
        assert cfg.max_lines == 0
        assert cfg.bucket_seconds == 1

    def test_not_active_when_zero(self):
        assert not RateConfig(max_lines=0).active

    def test_active_when_positive(self):
        assert RateConfig(max_lines=5).active

    def test_negative_max_lines_raises(self):
        with pytest.raises(ValueError, match="max_lines"):
            RateConfig(max_lines=-1)

    def test_zero_bucket_seconds_raises(self):
        with pytest.raises(ValueError, match="bucket_seconds"):
            RateConfig(max_lines=1, bucket_seconds=0)


class TestRateLimiter:
    def _limiter(self, max_lines: int, bucket_seconds: int = 1) -> RateLimiter:
        return RateLimiter(RateConfig(max_lines=max_lines, bucket_seconds=bucket_seconds))

    def test_disabled_always_allows(self):
        lim = RateLimiter(RateConfig(max_lines=0))
        for _ in range(100):
            assert lim.allow(_dt(0)) is True
        assert lim.dropped == 0

    def test_allows_up_to_max_per_bucket(self):
        lim = self._limiter(max_lines=3)
        results = [lim.allow(_dt(0)) for _ in range(5)]
        assert results == [True, True, True, False, False]
        assert lim.dropped == 2

    def test_new_bucket_resets_count(self):
        lim = self._limiter(max_lines=2)
        assert lim.allow(_dt(0)) is True
        assert lim.allow(_dt(0)) is True
        assert lim.allow(_dt(0)) is False   # over limit in second 0
        assert lim.allow(_dt(1)) is True    # new bucket
        assert lim.allow(_dt(1)) is True
        assert lim.dropped == 1

    def test_none_timestamp_always_passes(self):
        lim = self._limiter(max_lines=1)
        # fill the bucket
        lim.allow(_dt(0))
        lim.allow(_dt(0))  # would be dropped normally
        assert lim.allow(None) is True

    def test_multi_second_bucket(self):
        lim = self._limiter(max_lines=2, bucket_seconds=10)
        # seconds 0-9 are the same bucket
        results = [lim.allow(_dt(s)) for s in range(5)]
        assert results == [True, True, False, False, False]


class TestApplyRateLimit:
    def _pairs(self, seconds):
        return [(_dt(s).isoformat(), _dt(s)) for s in seconds]

    def test_no_limit_passes_all(self):
        lim = RateLimiter(RateConfig(max_lines=0))
        pairs = self._pairs(range(5))
        result = list(apply_rate_limit(iter(pairs), lim))
        assert len(result) == 5

    def test_limit_drops_excess(self):
        lim = RateLimiter(RateConfig(max_lines=1))
        # 3 lines all in second 0
        pairs = [("a", _dt(0)), ("b", _dt(0)), ("c", _dt(0))]
        result = list(apply_rate_limit(iter(pairs), lim))
        assert result == ["a"]
        assert lim.dropped == 2

    def test_make_rate_config_helper(self):
        cfg = make_rate_config(max_lines=10, bucket_seconds=60)
        assert cfg.max_lines == 10
        assert cfg.bucket_seconds == 60
