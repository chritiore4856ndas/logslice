"""Post-processing pipeline step: dedup + truncation applied to sliced lines.

This module wires together :mod:`logslice.dedup` and :mod:`logslice.truncate`
into a single callable that the main pipeline can use after the time-range
slice has been produced.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from logslice.dedup import Deduplicator, make_deduplicator
from logslice.truncate import TruncateConfig, make_truncate_config, truncate_line


@dataclass
class PostprocessConfig:
    dedup_enabled: bool = False
    dedup_window: int | None = None
    truncate_enabled: bool = False
    truncate_max_length: int = 512
    truncate_ellipsis: str = " ..."


class Postprocessor:
    """Apply deduplication and/or truncation to a stream of log lines."""

    def __init__(self, cfg: PostprocessConfig) -> None:
        self._dedup = make_deduplicator(
            enabled=cfg.dedup_enabled,
            window=cfg.dedup_window,
        )
        self._trunc_cfg = make_truncate_config(
            enabled=cfg.truncate_enabled,
            max_length=cfg.truncate_max_length,
            ellipsis=cfg.truncate_ellipsis,
        )

    @property
    def dedup(self) -> Deduplicator:
        return self._dedup

    @property
    def trunc_cfg(self) -> TruncateConfig:
        return self._trunc_cfg

    def process(self, lines: Iterator[str]) -> Iterator[str]:
        """Yield post-processed lines."""
        for line in lines:
            if self._dedup.is_duplicate(line):
                continue
            yield truncate_line(line, self._trunc_cfg)


def make_postprocessor(cfg: PostprocessConfig | None = None) -> Postprocessor:
    """Return a :class:`Postprocessor`, using defaults when *cfg* is None."""
    return Postprocessor(cfg or PostprocessConfig())


def postprocess_lines(
    lines: Iterator[str],
    *,
    dedup: bool = False,
    dedup_window: int | None = None,
    truncate: bool = False,
    max_length: int = 512,
    ellipsis: str = " ...",
) -> Iterator[str]:
    """Convenience wrapper for one-shot use without constructing config objects."""
    cfg = PostprocessConfig(
        dedup_enabled=dedup,
        dedup_window=dedup_window,
        truncate_enabled=truncate,
        truncate_max_length=max_length,
        truncate_ellipsis=ellipsis,
    )
    return make_postprocessor(cfg).process(lines)
