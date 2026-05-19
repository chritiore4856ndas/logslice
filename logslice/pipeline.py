"""High-level pipeline combining slicer + formatter for CLI and library use."""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Optional, TextIO

from logslice.slicer import slice_log
from logslice.formatter import write_output, DEFAULT_FORMAT, SUPPORTED_FORMATS


def run_pipeline(
    log_path: str,
    start: datetime,
    end: datetime,
    fmt: str = DEFAULT_FORMAT,
    out: Optional[TextIO] = None,
    encoding: str = "utf-8",
) -> dict:
    """
    Slice *log_path* between *start* and *end*, then write formatted output.

    Returns a summary dict with keys:
      - ``lines_written`` (int)
      - ``format`` (str)
      - ``path`` (str)
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format {fmt!r}. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )

    if out is None:
        out = sys.stdout

    lines = slice_log(log_path, start, end, encoding=encoding)
    written = write_output(lines, fmt=fmt, out=out)

    return {
        "lines_written": written,
        "format": fmt,
        "path": log_path,
    }


def run_pipeline_to_string(
    log_path: str,
    start: datetime,
    end: datetime,
    fmt: str = DEFAULT_FORMAT,
    encoding: str = "utf-8",
) -> str:
    """Convenience wrapper that returns the formatted output as a string."""
    import io

    buf = io.StringIO()
    run_pipeline(log_path, start, end, fmt=fmt, out=buf, encoding=encoding)
    return buf.getvalue()
