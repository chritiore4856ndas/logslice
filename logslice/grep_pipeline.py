"""Convenience helpers that plug grep into the log-slice pipeline."""
from __future__ import annotations

from typing import IO, Iterator, Optional, Tuple

from logslice.grep import GrepConfig, GrepResult, grep_lines
from logslice.slicer import slice_log
from logslice.timestamp_parser import parse_timestamp


def _enumerate_lines(path: str, start: Optional[int], end: Optional[int]) -> Iterator[Tuple[int, str]]:
    """Yield (lineno, text) pairs from the sliced region of *path*."""
    lineno = 0
    for line in slice_log(path, start=start, end=end):
        lineno += 1
        yield lineno, line.rstrip("\n")


def grep_log(
    path: str,
    cfg: GrepConfig,
    start: Optional[int] = None,
    end: Optional[int] = None,
) -> GrepResult:
    """Run grep over a (optionally pre-sliced) log file.

    Parameters
    ----------
    path:
        Path to the log file.
    cfg:
        Grep configuration (pattern, flags, max_count).
    start / end:
        Optional byte offsets forwarded to :func:`slice_log`.
    """
    pairs = _enumerate_lines(path, start, end)
    return grep_lines(pairs, cfg)


def write_grep_result(
    result: GrepResult,
    stream: IO[str],
    numbered: bool = False,
) -> None:
    """Write *result* to *stream*, one matched line per output line."""
    text = result.as_text(numbered=numbered)
    if text:
        stream.write(text)
        if not text.endswith("\n"):
            stream.write("\n")
