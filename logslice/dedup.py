"""Duplicate line detection and filtering for log slices."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Iterator, Optional


@dataclass
class DedupStats:
    total: int = 0
    duplicates: int = 0

    @property
    def unique(self) -> int:
        return self.total - self.duplicates

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "unique": self.unique,
            "duplicates": self.duplicates,
        }


class Deduplicator:
    """Filter duplicate lines using a rolling hash set.

    Parameters
    ----------
    enabled:
        When False the deduplicator is a transparent pass-through.
    window:
        Maximum number of recent line hashes to remember.  None means
        unlimited (full-file deduplication).
    """

    def __init__(self, enabled: bool = True, window: Optional[int] = None) -> None:
        self.enabled = enabled
        self.window = window
        self._seen: dict[str, int] = {}   # hash -> insertion order
        self._order: list[str] = []       # insertion-order list of hashes
        self.stats = DedupStats()

    def _hash(self, line: str) -> str:
        return hashlib.md5(line.rstrip("\n").encode(), usedforsecurity=False).hexdigest()

    def is_duplicate(self, line: str) -> bool:
        """Return True if *line* has been seen recently."""
        if not self.enabled:
            return False
        h = self._hash(line)
        if h in self._seen:
            self.stats.total += 1
            self.stats.duplicates += 1
            return True
        # Record new hash
        self._seen[h] = len(self._order)
        self._order.append(h)
        if self.window is not None and len(self._order) > self.window:
            evicted = self._order.pop(0)
            self._seen.pop(evicted, None)
        self.stats.total += 1
        return False

    def filter(self, lines: Iterator[str]) -> Iterator[str]:
        """Yield only non-duplicate lines from *lines*."""
        for line in lines:
            if not self.is_duplicate(line):
                yield line


def make_deduplicator(enabled: bool = False, window: Optional[int] = None) -> Deduplicator:
    """Convenience factory used by the pipeline."""
    return Deduplicator(enabled=enabled, window=window)
