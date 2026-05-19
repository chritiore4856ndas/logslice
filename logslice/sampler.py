"""Line sampler: collect evenly-spaced sample lines from a slice for preview."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class SampleResult:
    """Holds sampled lines with their original line numbers."""

    lines: List[Tuple[int, str]] = field(default_factory=list)
    total_seen: int = 0
    sample_size: int = 0

    def as_text(self, numbered: bool = False) -> str:
        parts = []
        for lineno, text in self.lines:
            if numbered:
                parts.append(f"{lineno:>8}  {text}")
            else:
                parts.append(text)
        return "\n".join(parts)


class ReservoirSampler:
    """Reservoir sampling (Algorithm R) so we never hold the full stream."""

    def __init__(self, k: int) -> None:
        if k <= 0:
            raise ValueError("sample size k must be a positive integer")
        self._k = k
        self._reservoir: List[Tuple[int, str]] = []
        self._count = 0
        import random
        self._rng = random.Random()

    def feed(self, lineno: int, line: str) -> None:
        self._count += 1
        if len(self._reservoir) < self._k:
            self._reservoir.append((lineno, line))
        else:
            j = self._rng.randint(0, self._count - 1)
            if j < self._k:
                self._reservoir[j] = (lineno, line)

    def result(self) -> SampleResult:
        sorted_lines = sorted(self._reservoir, key=lambda x: x[0])
        return SampleResult(
            lines=sorted_lines,
            total_seen=self._count,
            sample_size=len(sorted_lines),
        )


def sample_lines(
    lines: List[Tuple[int, str]],
    k: int,
    seed: Optional[int] = None,
) -> SampleResult:
    """Sample up to *k* lines from an already-collected list of (lineno, text) pairs."""
    sampler = ReservoirSampler(k)
    if seed is not None:
        sampler._rng.seed(seed)
    for lineno, text in lines:
        sampler.feed(lineno, text)
    return sampler.result()
