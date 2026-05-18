"""Core log slicing logic using binary search + streaming."""

import os
from datetime import datetime
from typing import Iterator, Optional

from logslice.timestamp_parser import parse_timestamp, line_in_range


def _find_line_start(f, pos: int) -> int:
    """Given an arbitrary byte offset, rewind to the start of the current line."""
    if pos == 0:
        return 0
    f.seek(pos)
    f.seek(-1, 1)
    while f.tell() > 0:
        ch = f.read(1)
        if ch == b"\n":
            return f.tell()
        f.seek(-2, 1)
    return 0


def _read_line_at(f, pos: int) -> Optional[str]:
    """Seek to pos and read the next complete line."""
    f.seek(pos)
    raw = f.readline()
    if not raw:
        return None
    return raw.decode("utf-8", errors="replace").rstrip("\n")


def _binary_search_start(f, file_size: int, start: datetime) -> int:
    """Binary search for the byte offset of the first line >= start timestamp."""
    lo, hi = 0, file_size
    while lo < hi:
        mid = (lo + hi) // 2
        pos = _find_line_start(f, mid)
        line = _read_line_at(f, pos)
        if line is None:
            hi = mid
            continue
        ts = parse_timestamp(line)
        if ts is not None and ts < start:
            lo = pos + len(line.encode()) + 1
        else:
            hi = mid
    return lo


def slice_log(
    path: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> Iterator[str]:
    """Yield log lines from *path* whose timestamps fall within [start, end].

    Uses binary search to locate the start offset so the entire file is never
    loaded into memory.
    """
    file_size = os.path.getsize(path)
    if file_size == 0:
        return

    with open(path, "rb") as f:
        offset = 0
        if start is not None:
            offset = _binary_search_start(f, file_size, start)

        f.seek(offset)
        for raw in f:
            line = raw.decode("utf-8", errors="replace").rstrip("\n")
            result = line_in_range(line, start, end)
            if result is False:
                # Timestamps are ordered; once we pass end we can stop
                ts = parse_timestamp(line)
                if ts is not None:
                    break
                # No timestamp — keep going (could be a continuation line)
                yield line
            else:
                yield line
