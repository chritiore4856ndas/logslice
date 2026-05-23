"""Grep-style pattern matching with context and count support."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterator, List, Optional, Tuple


@dataclass
class GrepConfig:
    pattern: Optional[str] = None
    ignore_case: bool = False
    invert: bool = False
    max_count: Optional[int] = None

    def __post_init__(self) -> None:
        if self.max_count is not None and self.max_count < 1:
            raise ValueError("max_count must be a positive integer")

    @property
    def active(self) -> bool:
        return self.pattern is not None

    def _compiled(self) -> re.Pattern:
        flags = re.IGNORECASE if self.ignore_case else 0
        return re.compile(self.pattern, flags)  # type: ignore[arg-type]

    def matches(self, line: str) -> bool:
        if not self.active:
            return True
        hit = bool(self._compiled().search(line))
        return (not hit) if self.invert else hit


@dataclass
class GrepResult:
    matched: List[Tuple[int, str]] = field(default_factory=list)
    total_scanned: int = 0

    def as_text(self, numbered: bool = False) -> str:
        if not self.matched:
            return ""
        lines = []
        for lineno, text in self.matched:
            if numbered:
                lines.append(f"{lineno:>6}: {text}")
            else:
                lines.append(text)
        return "\n".join(lines)


def grep_lines(
    pairs: Iterator[Tuple[int, str]],
    cfg: GrepConfig,
) -> GrepResult:
    """Filter (lineno, text) pairs using *cfg*, respecting max_count."""
    result = GrepResult()
    for lineno, text in pairs:
        result.total_scanned += 1
        if cfg.matches(text):
            result.matched.append((lineno, text))
            if cfg.max_count is not None and len(result.matched) >= cfg.max_count:
                break
    return result


def make_grep_config(
    pattern: Optional[str] = None,
    ignore_case: bool = False,
    invert: bool = False,
    max_count: Optional[int] = None,
) -> GrepConfig:
    return GrepConfig(
        pattern=pattern,
        ignore_case=ignore_case,
        invert=invert,
        max_count=max_count,
    )
