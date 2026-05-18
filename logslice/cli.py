"""Command-line interface for logslice."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from logslice.slicer import slice_log
from logslice.timestamp_parser import parse_timestamp


DEFAULT_OUTPUT_ENCODING = "utf-8"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="Extract a time-range window from a large log file without loading it fully into memory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  logslice app.log --start '2024-01-15 10:00:00' --end '2024-01-15 11:00:00'\n"
            "  logslice app.log --start '2024-01-15T10:00:00' -o out.log\n"
            "  logslice app.log --end '2024-01-15 12:00:00'\n"
        ),
    )

    parser.add_argument(
        "logfile",
        type=Path,
        help="Path to the log file to slice.",
    )
    parser.add_argument(
        "--start",
        metavar="DATETIME",
        default=None,
        help="Start of the time window (inclusive). Omit to slice from the beginning.",
    )
    parser.add_argument(
        "--end",
        metavar="DATETIME",
        default=None,
        help="End of the time window (inclusive). Omit to slice to the end.",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        type=Path,
        default=None,
        help="Write output to FILE instead of stdout.",
    )
    parser.add_argument(
        "--encoding",
        default=DEFAULT_OUTPUT_ENCODING,
        help=f"File encoding (default: {DEFAULT_OUTPUT_ENCODING}).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    return parser


def parse_dt_arg(value: str, label: str) -> datetime:
    """Parse a datetime string from CLI args, exiting with a friendly message on failure."""
    dt = parse_timestamp(value)
    if dt is None:
        print(f"error: could not parse {label} timestamp: {value!r}", file=sys.stderr)
        print("  Supported formats: ISO 8601, 'YYYY-MM-DD HH:MM:SS[.fff]', syslog", file=sys.stderr)
        sys.exit(1)
    return dt


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.logfile.exists():
        print(f"error: file not found: {args.logfile}", file=sys.stderr)
        return 1

    if not args.logfile.is_file():
        print(f"error: not a regular file: {args.logfile}", file=sys.stderr)
        return 1

    start_dt = parse_dt_arg(args.start, "--start") if args.start else None
    end_dt = parse_dt_arg(args.end, "--end") if args.end else None

    if start_dt and end_dt and start_dt > end_dt:
        print("error: --start must be before or equal to --end", file=sys.stderr)
        return 1

    try:
        if args.output:
            with open(args.output, "w", encoding=args.encoding) as out_fh:
                count = slice_log(args.logfile, start_dt, end_dt, out_fh)
        else:
            # Write bytes directly to stdout buffer to avoid encoding issues
            count = slice_log(args.logfile, start_dt, end_dt, sys.stdout)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if count == 0:
        print("warning: no lines matched the specified time range", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
