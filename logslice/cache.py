"""Simple index cache for binary search offsets to speed up repeated queries."""

import json
import hashlib
import os
from dataclasses import dataclass, field
from typing import Optional

CACHE_DIR = os.path.expanduser("~/.cache/logslice")


@dataclass
class IndexEntry:
    file_path: str
    file_size: int
    file_mtime: float
    offsets: list = field(default_factory=list)  # list of (timestamp_str, byte_offset)

    def is_valid_for(self, path: str) -> bool:
        """Check if this cache entry is still valid for the given file."""
        try:
            stat = os.stat(path)
            return stat.st_size == self.file_size and stat.st_mtime == self.file_mtime
        except OSError:
            return False


def _cache_key(file_path: str) -> str:
    abs_path = os.path.abspath(file_path)
    return hashlib.md5(abs_path.encode()).hexdigest()


def _cache_path(file_path: str) -> str:
    return os.path.join(CACHE_DIR, _cache_key(file_path) + ".json")


def load_cache(file_path: str) -> Optional[IndexEntry]:
    """Load a cached index entry if it exists and is still valid."""
    path = _cache_path(file_path)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            data = json.load(f)
        entry = IndexEntry(
            file_path=data["file_path"],
            file_size=data["file_size"],
            file_mtime=data["file_mtime"],
            offsets=data["offsets"],
        )
        if entry.is_valid_for(file_path):
            return entry
    except (KeyError, json.JSONDecodeError, OSError):
        pass
    return None


def save_cache(entry: IndexEntry) -> None:
    """Persist an index entry to disk."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _cache_path(entry.file_path)
    try:
        with open(path, "w") as f:
            json.dump(
                {
                    "file_path": entry.file_path,
                    "file_size": entry.file_size,
                    "file_mtime": entry.file_mtime,
                    "offsets": entry.offsets,
                },
                f,
            )
    except OSError:
        pass  # cache write failure is non-fatal


def invalidate_cache(file_path: str) -> None:
    """Remove the cache entry for a given file."""
    path = _cache_path(file_path)
    try:
        os.remove(path)
    except OSError:
        pass
