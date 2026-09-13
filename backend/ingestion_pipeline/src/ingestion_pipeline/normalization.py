"""Text normalization utilities (FR4).

Deliberately minimal for this iteration: collapsing whitespace and
stripping stray control characters is enough for the synthetic corpus
from Feature 0001. More aggressive cleaning (e.g., de-hyphenation across
line breaks, encoding repair) is out of scope until a real need appears.
"""
import re

_MULTIPLE_SPACES = re.compile(r"[ \t]+")
_MULTIPLE_NEWLINES = re.compile(r"\n{3,}")


def normalize_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = _MULTIPLE_SPACES.sub(" ", text)
    text = _MULTIPLE_NEWLINES.sub("\n\n", text)
    return text.strip()
