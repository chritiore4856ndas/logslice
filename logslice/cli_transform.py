"""CLI helpers for building a TransformConfig from argparse arguments."""
from __future__ import annotations

import argparse
from typing import List, Optional, Tuple

from logslice.transform import TransformConfig, make_transform_config


def add_transform_args(parser: argparse.ArgumentParser) -> None:
    """Register transform-related flags on *parser*."""
    grp = parser.add_argument_group("output transforms")
    grp.add_argument(
        "--sub",
        metavar="PATTERN=REPLACEMENT",
        action="append",
        dest="substitutions",
        default=[],
        help="Regex substitution applied to every output line (repeatable).",
    )
    grp.add_argument(
        "--uppercase",
        action="store_true",
        default=False,
        help="Convert output lines to upper-case.",
    )
    grp.add_argument(
        "--lowercase",
        action="store_true",
        default=False,
        help="Convert output lines to lower-case.",
    )
    grp.add_argument(
        "--strip-ansi",
        action="store_true",
        default=False,
        help="Strip ANSI colour escape sequences from output.",
    )


def parse_substitution(raw: str) -> Tuple[str, str]:
    """Split ``PATTERN=REPLACEMENT`` into a *(pattern, replacement)* tuple.

    The first ``=`` is used as the delimiter so that replacement strings may
    themselves contain ``=``.
    """
    if "=" not in raw:
        raise argparse.ArgumentTypeError(
            f"--sub value must be in PATTERN=REPLACEMENT form, got: {raw!r}"
        )
    pattern, _, replacement = raw.partition("=")
    return pattern, replacement


def build_transform_config(args: argparse.Namespace) -> TransformConfig:
    """Construct a :class:`TransformConfig` from parsed CLI *args*."""
    subs: List[Tuple[str, str]] = []
    for raw in getattr(args, "substitutions", []) or []:
        subs.append(parse_substitution(raw))

    return make_transform_config(
        substitutions=subs,
        uppercase=getattr(args, "uppercase", False),
        lowercase=getattr(args, "lowercase", False),
        strip_ansi=getattr(args, "strip_ansi", False),
    )
