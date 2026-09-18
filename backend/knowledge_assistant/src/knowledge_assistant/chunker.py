"""Text chunking (FR1).

Fixed-size, word-based chunking with overlap -- deliberately simple as
a first iteration (Feature 0004, Design Decision 4). Semantic/structural
chunking is a listed Future Improvement, not implemented here.
"""


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = text.split()
    if not words:
        return []

    step = chunk_size - overlap
    chunks: list[str] = []
    start = 0
    while start < len(words):
        chunk_words = words[start : start + chunk_size]
        chunks.append(" ".join(chunk_words))
        if start + chunk_size >= len(words):
            break
        start += step
    return chunks
