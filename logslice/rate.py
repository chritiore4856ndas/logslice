"""Line rate limiter — throttle output to at most N lines per time bucket."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterator, Optional, Tuple


@dataclass
class RateConfig:
    max_lines: int = 0          # 0 means disabled
    bucket_seconds: int = 1     # size of each time bucket

    def __post_init__(self) -> None:
        if self.max_lines < 0:
            raise ValueError("max_lines must be >= 0")
        if self.bucket_seconds <= 0:
            raise ValueError("bucket_seconds must be > 0")

    @property
    def active(self) -> bool:
        return self.max_lines > 0


@dataclass
class RateLimiter:
    config: RateConfig
    _bucket_start: Optional[datetime] = field(default=None, init=False, repr=False)
    _bucket_count: int = field(default=0, init=False, repr=False)
    dropped: int = field(default=0, init=False, repr=False)

    def _bucket_for(self, ts: datetime) -> datetime:
        """Round ts down to the nearest bucket boundary."""
        epoch = datetime(1970, 1, 1, tzinfo=ts.tzinfo)
        delta = ts - epoch
        bucket_td = timedelta(seconds=self.config.bucket_seconds)
        bucket_index = int(delta.total_seconds() // self.config.bucket_seconds)
        return epoch + bucket_td * bucket_index

    def allow(self, ts: Optional[datetime]) -> bool:
        """Return True if this line should pass through."""
        if not self.config.active:
            return True
        if ts is None:
            return True
        bucket = self._bucket_for(ts)
        if bucket != self._bucket_start:
            self._bucket_start = bucket
            self._bucket_count = 0
        self._bucket_count += 1
        if self._bucket_count <= self.config.max_lines:
            return True
        self.dropped += 1
        return False


def make_rate_config(max_lines: int = 0, bucket_seconds: int = 1) -> RateConfig:
    return RateConfig(max_lines=max_lines, bucket_seconds=bucket_seconds)


def apply_rate_limit(
    lines: Iterator[Tuple[str, Optional[datetime]]],
    limiter: RateLimiter,
) -> Iterator[str]:
    """Yield only lines that pass the rate limiter."""
    for line, ts in lines:
        if limiter.allow(ts):
            yield line
