"""Collect and report statistics about a log slice operation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import time


@dataclass
class SliceStats:
    """Holds statistics gathered during a slice operation."""

    total_lines: int = 0
    matched_lines: int = 0
    skipped_lines: int = 0
    first_timestamp: Optional[datetime] = None
    last_timestamp: Optional[datetime] = None
    file_size_bytes: int = 0
    elapsed_seconds: float = 0.0
    _start_time: float = field(default_factory=time.monotonic, repr=False, compare=False)

    def start(self) -> None:
        """Record the start time."""
        self._start_time = time.monotonic()

    def stop(self) -> None:
        """Compute elapsed time since start() was called."""
        self.elapsed_seconds = time.monotonic() - self._start_time

    def record_line(self, matched: bool, ts: Optional[datetime] = None) -> None:
        """Update counters for a single processed line."""
        self.total_lines += 1
        if matched:
            self.matched_lines += 1
            if ts is not None:
                if self.first_timestamp is None:
                    self.first_timestamp = ts
                self.last_timestamp = ts
        else:
            self.skipped_lines += 1

    def as_dict(self) -> dict:
        """Return stats as a plain dictionary suitable for JSON serialisation."""
        return {
            "total_lines": self.total_lines,
            "matched_lines": self.matched_lines,
            "skipped_lines": self.skipped_lines,
            "first_timestamp": self.first_timestamp.isoformat() if self.first_timestamp else None,
            "last_timestamp": self.last_timestamp.isoformat() if self.last_timestamp else None,
            "file_size_bytes": self.file_size_bytes,
            "elapsed_seconds": round(self.elapsed_seconds, 4),
        }

    def summary(self) -> str:
        """Return a human-readable one-line summary."""
        return (
            f"{self.matched_lines}/{self.total_lines} lines matched "
            f"in {self.elapsed_seconds:.3f}s "
            f"({self.file_size_bytes} bytes scanned)"
        )
