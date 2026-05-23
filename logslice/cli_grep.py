"""CLI helpers for grep arguments."""
from __future__ import annotations

import argparse
from typing import Optional

from logslice.grep import GrepConfig


def add_grep_args(parser: argparse.ArgumentParser) -> None:
    """Attach grep-related flags to *parser*."""
    grp = parser.add_argument_group("grep")
    grp.add_argument(
        "-g",
        "--grep",
        metavar="PATTERN",
        default=None,
        help="Only output lines matching PATTERN (regex).",
    )
    grp.add_argument(
        "-i",
        "--ignore-case",
        action="store_true",
        default=False,
        help="Case-insensitive pattern matching.",
    )
    grp.add_argument(
        "-v",
        "--invert-match",
        action="store_true",
        default=False,
        help="Select lines that do NOT match the pattern.",
    )
    grp.add_argument(
        "--grep-max",
        metavar="N",
        type=int,
        default=None,
        help="Stop after N matching lines.",
    )


def build_grep_config(args: argparse.Namespace) -> GrepConfig:
    """Construct a :class:`GrepConfig` from parsed CLI *args*."""
    pattern: Optional[str] = getattr(args, "grep", None)
    ignore_case: bool = getattr(args, "ignore_case", False)
    invert: bool = getattr(args, "invert_match", False)
    max_count: Optional[int] = getattr(args, "grep_max", None)
    return GrepConfig(
        pattern=pattern,
        ignore_case=ignore_case,
        invert=invert,
        max_count=max_count,
    )
