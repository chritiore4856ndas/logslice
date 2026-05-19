"""High-level pipeline that wires slicing, filtering, formatting, and stats."""

from __future__ import annotations

import io
from typing import Optional

from logslice.filter import LineFilter, make_filter
from logslice.formatter import get_formatter, write_output
from logslice.indexer import get_index, find_start_hint
from logslice.slicer import slice_log
from logslice.stats import SliceStats
from logslice.timestamp_parser import line_in_range


def run_pipeline(
    log_path: str,
    start: str,
    end: str,
    output_stream,
    fmt: str = "plain",
    keyword: Optional[str] = None,
    pattern: Optional[str] = None,
    ignore_case: bool = False,
    use_index: bool = True,
    show_stats: bool = False,
) -> SliceStats:
    """Run the full slice → filter → format → write pipeline."""
    stats = SliceStats()
    stats.start()

    line_filter: Optional[LineFilter] = make_filter(
        keyword=keyword, pattern=pattern, ignore_case=ignore_case
    )
    formatter = get_formatter(fmt)

    hint: Optional[int] = None
    if use_index:
        index = get_index(log_path)
        if index:
            hint = find_start_hint(index, start)

    line_number = 0
    for line in slice_log(log_path, start, end, start_hint=hint):
        line_number += 1
        in_range = line_in_range(line, start, end)
        if not in_range:
            stats.record_line(line, matched=False)
            continue

        if line_filter is not None and not line_filter.matches(line):
            stats.record_line(line, matched=False)
            continue

        stats.record_line(line, matched=True)
        write_output(output_stream, formatter, line, line_number)

    stats.stop()

    if show_stats:
        import json
        output_stream.write("\n" + json.dumps(stats.as_dict(), indent=2) + "\n")

    return stats


def run_pipeline_to_string(
    log_path: str,
    start: str,
    end: str,
    fmt: str = "plain",
    keyword: Optional[str] = None,
    pattern: Optional[str] = None,
    ignore_case: bool = False,
    use_index: bool = False,
) -> tuple[str, SliceStats]:
    """Convenience wrapper that captures output into a string."""
    buf = io.StringIO()
    stats = run_pipeline(
        log_path=log_path,
        start=start,
        end=end,
        output_stream=buf,
        fmt=fmt,
        keyword=keyword,
        pattern=pattern,
        ignore_case=ignore_case,
        use_index=use_index,
    )
    return buf.getvalue(), stats
