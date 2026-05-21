"""Keyword highlighting for log output lines."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


ANSI_RESET = "\033[0m"
ANSI_COLORS = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "magenta": "\033[35m",
    "bold": "\033[1m",
}
DEFAULT_COLOR = "yellow"


@dataclass
class HighlightConfig:
    terms: List[str] = field(default_factory=list)
    color: str = DEFAULT_COLOR
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        if self.color not in ANSI_COLORS:
            raise ValueError(
                f"Unknown color '{self.color}'. Choose from: {sorted(ANSI_COLORS)}"
            )

    @property
    def active(self) -> bool:
        return bool(self.terms)


def _build_pattern(terms: List[str], case_sensitive: bool) -> Optional[re.Pattern]:
    if not terms:
        return None
    escaped = [re.escape(t) for t in terms]
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile("|".join(escaped), flags)


def highlight_line(line: str, config: HighlightConfig) -> str:
    """Return *line* with matching terms wrapped in ANSI color codes.

    If *config* is not active or the terminal does not support color the
    original line is returned unchanged.
    """
    if not config.active:
        return line

    pattern = _build_pattern(config.terms, config.case_sensitive)
    if pattern is None:
        return line

    color_code = ANSI_COLORS[config.color]

    def _replace(match: re.Match) -> str:
        return f"{color_code}{match.group(0)}{ANSI_RESET}"

    return pattern.sub(_replace, line)


def make_highlight_config(
    terms: Optional[List[str]] = None,
    color: str = DEFAULT_COLOR,
    case_sensitive: bool = False,
) -> HighlightConfig:
    """Convenience constructor – *terms* defaults to an empty list."""
    return HighlightConfig(
        terms=list(terms) if terms else [],
        color=color,
        case_sensitive=case_sensitive,
    )
