"""Capability catalog used as the answer key for compliance evaluation
(ADR-0008).

The catalog is the category phrase bank from ADR-0004. SUPPORTED_CAPABILITIES
is the fixed subset (the first and third phrase of each category) that the
fictional company's products actually provide:

  - document_generator writes technical manuals whose "Capabilities"
    section draws ONLY from this subset.
  - knowledge_assistant's evaluation uses it as ground truth: an RFP
    requirement is "supported" exactly when the phrase it asks for is in
    this set.

Changing this set changes the answer key; evaluation results are only
comparable across runs that use the same set.

Pure data and two tiny pure functions: no I/O, no business logic.
"""
from __future__ import annotations

SUPPORTED_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "Reliability": (
        "99.99% uptime guarantees",
        "graceful degradation under partial outages",
    ),
    "Security": (
        "end-to-end encryption of data in transit",
        "role-based access control across all modules",
    ),
    "Performance": (
        "sub-second response times under peak load",
        "low-latency access to frequently used data",
    ),
    "Usability": (
        "an intuitive interface requiring minimal training",
        "a streamlined onboarding experience for new users",
    ),
    "Compliance": (
        "GDPR-compliant handling of personal data",
        "complete regulatory audit trails",
    ),
    "Integration": (
        "seamless integration with existing enterprise APIs",
        "compatibility with legacy backend systems",
    ),
    "Scalability": (
        "elastic scaling of compute resources on demand",
        "a horizontally distributed processing architecture",
    ),
    "Maintainability": (
        "a well-documented and modular codebase",
        "clear semantic versioning of all releases",
    ),
}

ALL_SUPPORTED_PHRASES: frozenset[str] = frozenset(
    phrase for phrases in SUPPORTED_CAPABILITIES.values() for phrase in phrases
)

_REQUEST_MARKER = "shall provide"
_PRIORITY_SENTENCE = ". This requirement"


def requested_phrase(requirement_text: str) -> str | None:
    """Return the capability phrase a generated RFP requirement asks for,
    for example 'The solution shall provide X. This requirement ...' -> 'X'.
    None when the text does not follow the generated pattern."""
    if _REQUEST_MARKER not in requirement_text:
        return None
    after = requirement_text.split(_REQUEST_MARKER, 1)[1].strip()
    after = after.split(_PRIORITY_SENTENCE, 1)[0]
    return after.strip().rstrip(".").strip() or None


def is_supported(requirement_text: str) -> bool | None:
    """Ground truth for a generated requirement: True/False, or None when
    the requested phrase cannot be determined."""
    phrase = requested_phrase(requirement_text)
    if phrase is None:
        return None
    return phrase in ALL_SUPPORTED_PHRASES
