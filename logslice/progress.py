"""Optional progress reporting for large file slicing operations."""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field
from typing import Optional, TextIO


@dataclass
class ProgressReporter:
    """Reports slicing progress to stderr or a custom stream."""

    file_size: int
    stream: TextIO = field(default_factory=lambda: sys.stderr)
    enabled: bool = True
    _start_time: float = field(default_factory=time.monotonic, init=False)
    _last_report: float = field(default=0.0, init=False)
    _bytes_read: int = field(default=0, init=False)
    report_interval: float = 0.25  # seconds between updates

    def update(self, current_offset: int) -> None:
        """Update progress based on current file offset."""
        if not self.enabled:
            return
        self._bytes_read = current_offset
        now = time.monotonic()
        if now - self._last_report >= self.report_interval:
            self._render()
            self._last_report = now

    def _render(self) -> None:
        if self.file_size <= 0:
            return
        pct = min(100.0, self._bytes_read / self.file_size * 100)
        elapsed = time.monotonic() - self._start_time
        rate = self._bytes_read / elapsed / 1024 / 1024 if elapsed > 0 else 0.0
        bar_len = 30
        filled = int(bar_len * pct / 100)
        bar = "#" * filled + "-" * (bar_len - filled)
        self.stream.write(
            f"\r[{bar}] {pct:5.1f}%  {rate:6.2f} MB/s"
        )
        self.stream.flush()

    def finish(self) -> None:
        """Print a final newline to clean up the progress line."""
        if not self.enabled:
            return
        self._bytes_read = self.file_size
        self._render()
        self.stream.write("\n")
        self.stream.flush()


def make_reporter(
    path: str,
    enabled: bool = True,
    stream: Optional[TextIO] = None,
) -> ProgressReporter:
    """Create a ProgressReporter sized for *path*."""
    try:
        size = os.path.getsize(path)
    except OSError:
        size = 0
    return ProgressReporter(
        file_size=size,
        stream=stream or sys.stderr,
        enabled=enabled,
    )
