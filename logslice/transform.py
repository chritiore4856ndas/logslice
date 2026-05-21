"""Line transformation: apply regex substitutions or case transforms to matched lines."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class TransformConfig:
    substitutions: List[Tuple[str, str]] = field(default_factory=list)  # (pattern, replacement)
    uppercase: bool = False
    lowercase: bool = False
    strip_ansi: bool = False

    def __post_init__(self) -> None:
        if self.uppercase and self.lowercase:
            raise ValueError("Cannot set both uppercase and lowercase")
        self._compiled = [(re.compile(p), r) for p, r in self.substitutions]

    @property
    def active(self) -> bool:
        return bool(self.substitutions) or self.uppercase or self.lowercase or self.strip_ansi


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def transform_line(line: str, cfg: TransformConfig) -> str:
    """Apply all configured transforms to *line* and return the result."""
    if not cfg.active:
        return line

    if cfg.strip_ansi:
        line = _ANSI_RE.sub("", line)

    for pattern, replacement in cfg._compiled:
        line = pattern.sub(replacement, line)

    if cfg.uppercase:
        line = line.upper()
    elif cfg.lowercase:
        line = line.lower()

    return line


def make_transform_config(
    substitutions: Optional[List[Tuple[str, str]]] = None,
    uppercase: bool = False,
    lowercase: bool = False,
    strip_ansi: bool = False,
) -> TransformConfig:
    return TransformConfig(
        substitutions=substitutions or [],
        uppercase=uppercase,
        lowercase=lowercase,
        strip_ansi=strip_ansi,
    )
