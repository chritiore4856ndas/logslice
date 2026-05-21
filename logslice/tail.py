"""Tail support: read the last N lines from a log file efficiently."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional

_DEFAULT_CHUNK = 8192


@dataclass
class TailResult:
    lines: List[str] = field(default_factory=list)
    bytes_read: int = 0
    chunks_read: int = 0

    def as_text(self) -> str:
        return "".join(self.lines)


def tail_lines(
    path: str,
    n: int,
    encoding: str = "utf-8",
    errors: str = "replace",
    chunk_size: int = _DEFAULT_CHUNK,
) -> TailResult:
    """Return the last *n* lines of *path* without reading the whole file."""
    if n <= 0:
        return TailResult()

    result = TailResult()
    file_size = os.path.getsize(path)
    if file_size == 0:
        return result

    with open(path, "rb") as fh:
        pos = file_size
        buf = b""
        found: List[bytes] = []

        while pos > 0 and len(found) <= n:
            read_size = min(chunk_size, pos)
            pos -= read_size
            fh.seek(pos)
            chunk = fh.read(read_size)
            result.bytes_read += len(chunk)
            result.chunks_read += 1
            buf = chunk + buf

            lines = buf.split(b"\n")
            # The first element may be an incomplete line — keep it in buf.
            buf = lines[0]
            found = lines[1:] + found

            if len(found) >= n:
                break

        # Include whatever is left in buf as the very first line.
        all_lines = ([buf] if buf else []) + found
        # Drop trailing empty entry caused by a final newline.
        if all_lines and all_lines[-1] == b"":
            all_lines = all_lines[:-1]

        tail = all_lines[-n:] if len(all_lines) > n else all_lines
        result.lines = [
            (ln + b"\n").decode(encoding, errors=errors) for ln in tail
        ]

    return result
