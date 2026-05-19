"""Build a sparse byte-offset index for a log file to accelerate binary search."""

import os
from typing import Optional

from logslice.cache import IndexEntry, load_cache, save_cache
from logslice.timestamp_parser import parse_timestamp

# Sample roughly every SAMPLE_EVERY bytes when building the index.
SAMPLE_EVERY = 512 * 1024  # 512 KB


def build_index(file_path: str, sample_every: int = SAMPLE_EVERY) -> IndexEntry:
    """Scan the file and record (timestamp, offset) pairs at regular intervals."""
    stat = os.stat(file_path)
    offsets = []
    next_sample = 0

    with open(file_path, "rb") as fh:
        while True:
            pos = fh.tell()
            raw = fh.readline()
            if not raw:
                break
            if pos >= next_sample:
                line = raw.decode("utf-8", errors="replace").rstrip("\n")
                ts = parse_timestamp(line)
                if ts is not None:
                    offsets.append((ts.isoformat(), pos))
                    next_sample = pos + sample_every

    return IndexEntry(
        file_path=file_path,
        file_size=stat.st_size,
        file_mtime=stat.st_mtime,
        offsets=offsets,
    )


def get_index(
    file_path: str,
    sample_every: int = SAMPLE_EVERY,
    use_cache: bool = True,
) -> IndexEntry:
    """Return a valid index, loading from cache or rebuilding as needed."""
    if use_cache:
        cached = load_cache(file_path)
        if cached is not None:
            return cached

    entry = build_index(file_path, sample_every=sample_every)

    if use_cache:
        save_cache(entry)

    return entry


def find_start_hint(entry: IndexEntry, target_iso: str) -> Optional[int]:
    """Binary-search the index to find the largest offset whose timestamp <= target.

    Returns a byte offset to seek to before the real binary search, or None
    if the index is empty.
    """
    if not entry.offsets:
        return None

    lo, hi = 0, len(entry.offsets) - 1
    result_offset = entry.offsets[0][1]

    while lo <= hi:
        mid = (lo + hi) // 2
        ts_str, offset = entry.offsets[mid]
        if ts_str <= target_iso:
            result_offset = offset
            lo = mid + 1
        else:
            hi = mid - 1

    return result_offset
