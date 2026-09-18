import pytest

from knowledge_assistant.chunker import chunk_text


def test_empty_text_returns_no_chunks() -> None:
    assert chunk_text("", 10, 2) == []


def test_short_text_returns_a_single_chunk() -> None:
    assert chunk_text("one two three", 10, 2) == ["one two three"]


def test_consecutive_chunks_overlap_correctly() -> None:
    text = " ".join(f"w{i}" for i in range(1, 21))
    chunks = chunk_text(text, chunk_size=8, overlap=2)

    assert len(chunks) == 3
    assert chunks[0].split()[-2:] == chunks[1].split()[:2]


def test_rejects_overlap_not_smaller_than_chunk_size() -> None:
    with pytest.raises(ValueError):
        chunk_text("a b c", chunk_size=5, overlap=5)
