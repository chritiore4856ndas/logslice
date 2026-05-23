"""Chunk iterator: splits a log slice into fixed-size batches of lines."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Tuple


@dataclass
class ChunkConfig:
    size: int = 500
    overlap: int = 0

    def __post_init__(self) -> None:
        if self.size < 1:
            raise ValueError(f"chunk size must be >= 1, got {self.size}")
        if self.overlap < 0:
            raise ValueError(f"overlap must be >= 0, got {self.overlap}")
        if self.overlap >= self.size:
            raise ValueError(
                f"overlap ({self.overlap}) must be less than size ({self.size})"
            )

    @property
    def active(self) -> bool:
        return self.size > 0


@dataclass
class Chunk:
    index: int
    lines: List[Tuple[int, str]]  # (line_number, text)
    is_last: bool = False

    @property
    def texts(self) -> List[str]:
        return [t for _, t in self.lines]

    def as_text(self) -> str:
        return "".join(t if t.endswith("\n") else t + "\n" for _, t in self.lines)


def iter_chunks(
    lines: Iterable[Tuple[int, str]],
    config: ChunkConfig,
) -> Iterator[Chunk]:
    """Yield Chunk objects from an iterable of (line_number, text) pairs."""
    buf: List[Tuple[int, str]] = []
    chunk_index = 0

    for pair in lines:
        buf.append(pair)
        if len(buf) == config.size:
            yield Chunk(index=chunk_index, lines=list(buf))
            chunk_index += 1
            if config.overlap:
                buf = buf[-config.overlap :]
            else:
                buf = []

    if buf:
        yield Chunk(index=chunk_index, lines=buf, is_last=True)
    elif chunk_index > 0:
        # mark the last emitted chunk as final — re-yield not possible here,
        # so callers that need is_last should use collect_chunks instead
        pass


def collect_chunks(
    lines: Iterable[Tuple[int, str]],
    config: ChunkConfig,
) -> List[Chunk]:
    """Collect all chunks into a list and mark the final one."""
    chunks = list(iter_chunks(lines, config))
    if chunks:
        chunks[-1].is_last = True
    return chunks


def make_chunk_config(size: int = 500, overlap: int = 0) -> ChunkConfig:
    return ChunkConfig(size=size, overlap=overlap)
