"""Pipeline integration for rotated log files.

Provides a helper that runs slice_log across all rotated variants of a
log file and merges the results in chronological order.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, List, Optional

from logslice.rotate import find_rotated_files
from logslice.slicer import slice_log
from logslice.timestamp_parser import parse_timestamp


def slice_rotated(
    base_path: str | Path,
    start: Optional[str] = None,
    end: Optional[str] = None,
    *,
    encoding: str = 'utf-8',
) -> Iterator[str]:
    """Yield matching lines from all rotated files, oldest-first.

    Each rotated file is sliced independently so binary-search hints
    still apply per file.  Lines are yielded in file order (oldest
    rotation first, current file last).

    Args:
        base_path: Path to the *current* log file (e.g. ``/var/log/app.log``).
        start:     ISO-8601 or syslog-style start timestamp string, or ``None``.
        end:       ISO-8601 or syslog-style end timestamp string, or ``None``.
        encoding:  Text encoding passed to underlying readers.

    Yields:
        Raw log lines (including newline) that fall within [start, end].
    """
    rotated = find_rotated_files(base_path)
    for rf in rotated:
        if rf.compressed:
            # Binary search not possible on compressed streams; fall back to
            # sequential scan via slice_log with a plain open.
            import gzip
            with gzip.open(rf.path, 'rt', encoding=encoding, errors='replace') as fh:
                for line in fh:
                    yield from _filter_line(line, start, end)
        else:
            yield from slice_log(
                str(rf.path),
                start=start,
                end=end,
            )


def collect_rotated(
    base_path: str | Path,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> List[str]:
    """Convenience wrapper — return all matching lines as a list."""
    return list(slice_rotated(base_path, start=start, end=end))


def _filter_line(line: str, start: Optional[str], end: Optional[str]) -> Iterator[str]:
    """Yield *line* if its timestamp falls within [start, end]."""
    from logslice.timestamp_parser import line_in_range
    if line_in_range(line, start, end):
        yield line
