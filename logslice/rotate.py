"""Support for reading rotated log files (e.g. app.log, app.log.1, app.log.2.gz)."""

from __future__ import annotations

import gzip
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List


_ROTATE_SUFFIX = re.compile(r'\.(\d+)(\.gz)?$')


@dataclass
class RotatedFile:
    path: Path
    index: int          # 0 = current, 1 = oldest-ish for numbered scheme
    compressed: bool

    def open(self):
        """Return a text-mode file object, transparently decompressing .gz files."""
        if self.compressed:
            return gzip.open(self.path, 'rt', encoding='utf-8', errors='replace')
        return self.path.open('r', encoding='utf-8', errors='replace')


def find_rotated_files(base_path: str | Path) -> List[RotatedFile]:
    """Return all rotated variants of *base_path* sorted oldest-first.

    Supports:
      - app.log          (index 0, current)
      - app.log.1        (index 1)
      - app.log.2.gz     (index 2, compressed)
    """
    base = Path(base_path)
    parent = base.parent
    name = base.name

    results: List[RotatedFile] = []

    if base.exists():
        results.append(RotatedFile(path=base, index=0, compressed=False))

    for entry in sorted(parent.iterdir()):
        candidate = entry.name
        if not candidate.startswith(name + '.'):
            continue
        suffix = candidate[len(name):]
        m = _ROTATE_SUFFIX.match(suffix)
        if m:
            idx = int(m.group(1))
            compressed = m.group(2) is not None
            results.append(RotatedFile(path=entry, index=idx, compressed=compressed))

    # oldest first: higher index number = older
    results.sort(key=lambda r: (-r.index if r.index > 0 else 1e9))
    return results


def iter_rotated_lines(base_path: str | Path) -> Iterator[str]:
    """Yield lines from all rotated files, oldest-first, newest last."""
    for rf in find_rotated_files(base_path):
        with rf.open() as fh:
            yield from fh
