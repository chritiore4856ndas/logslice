"""Context lines: emit N lines before/after each matched line."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Tuple


@dataclass
class ContextConfig:
    before: int = 0
    after: int = 0

    def __post_init__(self) -> None:
        if self.before < 0:
            raise ValueError("before must be >= 0")
        if self.after < 0:
            raise ValueError("after must be >= 0")

    @property
    def active(self) -> bool:
        return self.before > 0 or self.after > 0


def make_context_config(before: int = 0, after: int = 0) -> ContextConfig:
    return ContextConfig(before=before, after=after)


def iter_with_context(
    lines: Iterable[Tuple[int, str, bool]],
    cfg: ContextConfig,
) -> Iterator[Tuple[int, str, bool]]:
    """Yield (lineno, text, matched) tuples, expanding context around matches.

    Input tuples: (line_number, line_text, is_match)
    Output tuples: same shape; context lines have is_match=False.
    Overlapping context windows are merged without duplicates.
    """
    if not cfg.active:
        yield from lines
        return

    buf: deque[Tuple[int, str, bool]] = deque()
    pending_after: List[Tuple[int, str, bool]] = []
    after_remaining = 0
    emitted_up_to = -1

    def _emit(item: Tuple[int, str, bool]) -> Iterator[Tuple[int, str, bool]]:
        nonlocal emitted_up_to
        lineno = item[0]
        if lineno > emitted_up_to:
            emitted_up_to = lineno
            yield item

    for lineno, text, matched in lines:
        entry = (lineno, text, matched)
        buf.append(entry)
        if len(buf) > cfg.before + 1:
            buf.popleft()

        if after_remaining > 0:
            yield from _emit(entry)
            after_remaining -= 1
            continue

        if matched:
            # flush before-context
            for item in buf:
                yield from _emit(item)
            after_remaining = cfg.after
        # if not matched and no after pending, just keep in buf


def collect_with_context(
    lines: Iterable[Tuple[int, str, bool]],
    cfg: ContextConfig,
) -> List[Tuple[int, str, bool]]:
    return list(iter_with_context(lines, cfg))
