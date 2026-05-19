"""Output formatting utilities for logslice."""

import sys
from typing import Iterator, Optional, TextIO


DEFAULT_FORMAT = "plain"
SUPPORTED_FORMATS = ("plain", "jsonl", "numbered")


def format_plain(line: str, _line_number: int) -> str:
    """Return the line as-is."""
    return line


def format_numbered(line: str, line_number: int) -> str:
    """Prefix each line with its line number."""
    return f"{line_number:>8}  {line}"


def format_jsonl(line: str, line_number: int) -> str:
    """Wrap each line as a JSON object with metadata."""
    import json
    stripped = line.rstrip("\n")
    return json.dumps({"n": line_number, "msg": stripped})


_FORMATTERS = {
    "plain": format_plain,
    "numbered": format_numbered,
    "jsonl": format_jsonl,
}


def get_formatter(fmt: str):
    """Return the formatter callable for the given format name."""
    if fmt not in _FORMATTERS:
        raise ValueError(
            f"Unknown format {fmt!r}. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )
    return _FORMATTERS[fmt]


def write_output(
    lines: Iterator[str],
    fmt: str = DEFAULT_FORMAT,
    out: Optional[TextIO] = None,
    start_line: int = 1,
) -> int:
    """
    Write formatted lines to *out* (defaults to stdout).

    Returns the total number of lines written.
    """
    if out is None:
        out = sys.stdout

    formatter = get_formatter(fmt)
    count = 0

    for i, line in enumerate(lines, start=start_line):
        formatted = formatter(line, i)
        if not formatted.endswith("\n"):
            formatted += "\n"
        out.write(formatted)
        count += 1

    return count
