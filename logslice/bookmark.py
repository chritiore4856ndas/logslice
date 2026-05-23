"""Bookmark support — save and restore the last processed position in a log file."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


_BOOKMARK_DIR = Path.home() / ".logslice" / "bookmarks"


@dataclass
class Bookmark:
    log_path: str
    byte_offset: int
    last_timestamp: Optional[str] = None
    line_number: int = 0

    def as_dict(self) -> dict:
        return asdict(self)


def _bookmark_path(log_path: str) -> Path:
    """Return the path to the bookmark file for *log_path*."""
    safe = log_path.replace(os.sep, "_").replace(":", "_").lstrip("_")
    return _BOOKMARK_DIR / f"{safe}.json"


def save_bookmark(bookmark: Bookmark) -> Path:
    """Persist *bookmark* to disk and return the file path."""
    dest = _bookmark_path(bookmark.log_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(bookmark.as_dict(), indent=2))
    return dest


def load_bookmark(log_path: str) -> Optional[Bookmark]:
    """Load a previously saved bookmark for *log_path*, or return None."""
    p = _bookmark_path(log_path)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
        return Bookmark(**data)
    except Exception:
        return None


def clear_bookmark(log_path: str) -> bool:
    """Delete the bookmark for *log_path*. Returns True if one existed."""
    p = _bookmark_path(log_path)
    if p.exists():
        p.unlink()
        return True
    return False
