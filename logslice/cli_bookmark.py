"""CLI helpers for bookmark subcommands (show / clear)."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from logslice.bookmark import load_bookmark, clear_bookmark


def add_bookmark_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *bookmark* subcommand onto *subparsers*."""
    p = subparsers.add_parser(
        "bookmark",
        help="Manage saved read positions for log files",
    )
    sub = p.add_subparsers(dest="bookmark_cmd", required=True)

    show_p = sub.add_parser("show", help="Print the saved bookmark for a log file")
    show_p.add_argument("log_file", help="Path to the log file")

    clear_p = sub.add_parser("clear", help="Delete the saved bookmark for a log file")
    clear_p.add_argument("log_file", help="Path to the log file")


def handle_bookmark_command(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    """Dispatch *args* to the appropriate bookmark action.

    Returns an exit code (0 = success, non-zero = failure).
    """
    cmd = args.bookmark_cmd
    log_file: str = args.log_file

    if cmd == "show":
        return _cmd_show(log_file, out, err)
    if cmd == "clear":
        return _cmd_clear(log_file, out, err)

    print(f"Unknown bookmark command: {cmd}", file=err)
    return 1


def _cmd_show(log_file: str, out, err) -> int:
    bm = load_bookmark(log_file)
    if bm is None:
        print(f"No bookmark found for: {log_file}", file=err)
        return 1
    print(f"log_path      : {bm.log_path}", file=out)
    print(f"byte_offset   : {bm.byte_offset}", file=out)
    print(f"line_number   : {bm.line_number}", file=out)
    if bm.last_timestamp:
        print(f"last_timestamp: {bm.last_timestamp}", file=out)
    return 0


def _cmd_clear(log_file: str, out, err) -> int:
    removed = clear_bookmark(log_file)
    if removed:
        print(f"Bookmark cleared for: {log_file}", file=out)
        return 0
    print(f"No bookmark found for: {log_file}", file=err)
    return 1
