"""Line truncation helpers — keep long log lines readable in output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

_ELLIPSIS = " ..."
_DEFAULT_MAX = 512


@dataclass
class TruncateConfig:
    enabled: bool = False
    max_length: int = _DEFAULT_MAX
    ellipsis: str = _ELLIPSIS

    def __post_init__(self) -> None:
        if self.max_length < 1:
            raise ValueError("max_length must be at least 1")


def truncate_line(line: str, cfg: TruncateConfig) -> str:
    """Return *line* truncated according to *cfg*.

    The trailing newline (if present) is preserved after truncation so the
    output stream remains well-formed.
    """
    if not cfg.enabled:
        return line

    has_newline = line.endswith("\n")
    body = line.rstrip("\n")

    if len(body) <= cfg.max_length:
        return line

    suffix = cfg.ellipsis
    cut = cfg.max_length - len(suffix)
    if cut < 0:
        cut = 0
    truncated = body[:cut] + suffix
    return truncated + ("\n" if has_newline else "")


def make_truncate_config(
    enabled: bool = False,
    max_length: int = _DEFAULT_MAX,
    ellipsis: str = _ELLIPSIS,
) -> TruncateConfig:
    """Convenience factory used by the pipeline and CLI."""
    return TruncateConfig(enabled=enabled, max_length=max_length, ellipsis=ellipsis)


def apply_truncation(lines: list[str], cfg: TruncateConfig) -> list[str]:
    """Return a new list with every line truncated per *cfg*."""
    if not cfg.enabled:
        return lines
    return [truncate_line(line, cfg) for line in lines]
