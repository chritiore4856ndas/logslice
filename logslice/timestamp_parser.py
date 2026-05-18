"""Utilities for detecting and parsing timestamps from log lines."""

import re
from datetime import datetime
from typing import Optional

# Common log timestamp patterns ordered by specificity
TIMESTAMP_PATTERNS = [
    # ISO 8601: 2024-01-15T13:45:22.123Z or 2024-01-15T13:45:22
    (
        r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)",
        ["%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"],
    ),
    # Common syslog: Jan 15 13:45:22
    (
        r"([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})",
        ["%b %d %H:%M:%S", "%b  %d %H:%M:%S"],
    ),
    # Date + time: 2024-01-15 13:45:22
    (
        r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)",
        ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"],
    ),
    # Nginx/Apache: 15/Jan/2024:13:45:22
    (
        r"(\d{2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2})",
        ["%d/%b/%Y:%H:%M:%S"],
    ),
]

_COMPILED = [(re.compile(pat), fmts) for pat, fmts in TIMESTAMP_PATTERNS]


def parse_timestamp(line: str) -> Optional[datetime]:
    """Extract and parse the first recognizable timestamp from a log line.

    Returns a naive or aware datetime, or None if no timestamp is found.
    """
    for pattern, formats in _COMPILED:
        match = pattern.search(line)
        if not match:
            continue
        raw = match.group(1)
        for fmt in formats:
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
    return None


def line_in_range(line: str, start: Optional[datetime], end: Optional[datetime]) -> Optional[bool]:
    """Check whether a log line's timestamp falls within [start, end].

    Returns:
        True  — timestamp is within range
        False — timestamp is outside range
        None  — no timestamp could be parsed
    """
    ts = parse_timestamp(line)
    if ts is None:
        return None
    # Strip timezone info for naive comparison if needed
    if start and start.tzinfo is None and ts.tzinfo is not None:
        ts = ts.replace(tzinfo=None)
    if start and ts < start:
        return False
    if end and ts > end:
        return False
    return True
