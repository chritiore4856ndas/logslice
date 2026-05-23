"""Tests for logslice.chunk."""

import pytest

from logslice.chunk import ChunkConfig, Chunk, iter_chunks, collect_chunks, make_chunk_config


def _pairs(n: int):
    return [(i + 1, f"line {i + 1}\n") for i in range(n)]


class TestChunkConfig:
    def test_defaults(self):
        cfg = ChunkConfig()
        assert cfg.size == 500
        assert cfg.overlap == 0

    def test_active_by_default(self):
        assert ChunkConfig().active is True

    def test_invalid_size_raises(self):
        with pytest.raises(ValueError, match="size"):
            ChunkConfig(size=0)

    def test_negative_overlap_raises(self):
        with pytest.raises(ValueError, match="overlap"):
            ChunkConfig(size=10, overlap=-1)

    def test_overlap_equal_to_size_raises(self):
        with pytest.raises(ValueError, match="overlap"):
            ChunkConfig(size=5, overlap=5)

    def test_overlap_less_than_size_ok(self):
        cfg = ChunkConfig(size=10, overlap=3)
        assert cfg.overlap == 3


class TestIterChunks:
    def test_empty_input_yields_nothing(self):
        assert list(iter_chunks([], ChunkConfig(size=10))) == []

    def test_single_partial_chunk(self):
        chunks = list(iter_chunks(_pairs(3), ChunkConfig(size=10)))
        assert len(chunks) == 1
        assert len(chunks[0].lines) == 3

    def test_exact_multiple_yields_correct_count(self):
        chunks = list(iter_chunks(_pairs(9), ChunkConfig(size=3)))
        assert len(chunks) == 3
        for c in chunks:
            assert len(c.lines) == 3

    def test_remainder_in_last_chunk(self):
        chunks = list(iter_chunks(_pairs(10), ChunkConfig(size=3)))
        assert len(chunks) == 4
        assert len(chunks[-1].lines) == 1

    def test_chunk_index_increments(self):
        chunks = list(iter_chunks(_pairs(6), ChunkConfig(size=2)))
        assert [c.index for c in chunks] == [0, 1, 2]

    def test_texts_property(self):
        chunks = list(iter_chunks(_pairs(2), ChunkConfig(size=5)))
        assert chunks[0].texts == ["line 1\n", "line 2\n"]

    def test_as_text_joins_lines(self):
        chunks = list(iter_chunks([(1, "hello"), (2, "world")], ChunkConfig(size=5)))
        result = chunks[0].as_text()
        assert result == "hello\nworld\n"

    def test_as_text_no_double_newline(self):
        chunks = list(iter_chunks([(1, "hello\n"), (2, "world\n")], ChunkConfig(size=5)))
        assert chunks[0].as_text() == "hello\nworld\n"


class TestOverlap:
    def test_overlap_repeats_tail_lines(self):
        pairs = _pairs(5)
        chunks = list(iter_chunks(pairs, ChunkConfig(size=3, overlap=1)))
        # chunk 0: lines 1-3, chunk 1: lines 3-5
        assert chunks[0].lines[-1] == chunks[1].lines[0]

    def test_overlap_two(self):
        pairs = _pairs(6)
        chunks = list(iter_chunks(pairs, ChunkConfig(size=4, overlap=2)))
        assert chunks[0].lines[-2:] == chunks[1].lines[:2]


class TestCollectChunks:
    def test_last_chunk_marked(self):
        chunks = collect_chunks(_pairs(7), ChunkConfig(size=3))
        assert chunks[-1].is_last is True

    def test_non_last_chunks_not_marked(self):
        chunks = collect_chunks(_pairs(7), ChunkConfig(size=3))
        for c in chunks[:-1]:
            assert c.is_last is False

    def test_empty_returns_empty_list(self):
        assert collect_chunks([], ChunkConfig(size=10)) == []


def test_make_chunk_config_defaults():
    cfg = make_chunk_config()
    assert cfg.size == 500
    assert cfg.overlap == 0


def test_make_chunk_config_custom():
    cfg = make_chunk_config(size=100, overlap=10)
    assert cfg.size == 100
    assert cfg.overlap == 10
