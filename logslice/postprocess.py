"""Postprocessor — applies dedup, truncation, and rate-limiting to matched lines."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator, Optional, Tuple

from logslice.dedup import Deduplicator
from logslice.truncate import TruncateConfig, apply_truncation
from logslice.rate import RateConfig, RateLimiter


@dataclass
class PostprocessConfig:
    dedup: bool = False
    trunc_cfg: Optional[TruncateConfig] = None
    rate_cfg: Optional[RateConfig] = None


@dataclass
class Postprocessor:
    config: PostprocessConfig
    _dedup: Deduplicator = field(init=False, repr=False)
    _rate: Optional[RateLimiter] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._dedup = Deduplicator(enabled=self.config.dedup)
        if self.config.rate_cfg is not None:
            self._rate = RateLimiter(self.config.rate_cfg)

    @property
    def dedup_stats(self):
        return self._dedup.stats

    @property
    def rate_dropped(self) -> int:
        return self._rate.dropped if self._rate else 0

    def process(
        self,
        lines: Iterator[Tuple[str, Optional[datetime]]],
    ) -> Iterator[str]:
        """Yield post-processed lines from (raw_line, timestamp) pairs."""
        for line, ts in lines:
            # 1. dedup
            if self._dedup.is_duplicate(line):
                continue
            # 2. rate limit
            if self._rate is not None and not self._rate.allow(ts):
                continue
            # 3. truncation
            if self.config.trunc_cfg is not None:
                line = apply_truncation(line, self.config.trunc_cfg)
            yield line


def make_postprocessor(
    dedup: bool = False,
    max_length: int = 0,
    rate_max_lines: int = 0,
    rate_bucket_seconds: int = 1,
) -> Postprocessor:
    from logslice.truncate import make_truncate_config
    from logslice.rate import make_rate_config

    trunc = make_truncate_config(max_length=max_length) if max_length > 0 else None
    rate = (
        make_rate_config(max_lines=rate_max_lines, bucket_seconds=rate_bucket_seconds)
        if rate_max_lines > 0
        else None
    )
    return Postprocessor(PostprocessConfig(dedup=dedup, trunc_cfg=trunc, rate_cfg=rate))
