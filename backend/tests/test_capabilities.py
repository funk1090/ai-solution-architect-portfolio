from shared_core.capabilities import (
    ALL_SUPPORTED_PHRASES,
    SUPPORTED_CAPABILITIES,
    is_supported,
    requested_phrase,
)


def test_every_category_has_two_supported_phrases() -> None:
    assert len(SUPPORTED_CAPABILITIES) == 8
    assert all(len(p) == 2 for p in SUPPORTED_CAPABILITIES.values())
    assert len(ALL_SUPPORTED_PHRASES) == 16


def test_requested_phrase_strips_the_priority_sentence() -> None:
    text = "The solution shall provide a well-documented and modular codebase. This requirement is mission-critical."

    assert requested_phrase(text) == "a well-documented and modular codebase"


def test_requested_phrase_keeps_inner_dots() -> None:
    text = "The solution shall provide 99.99% uptime guarantees. This requirement would be a nice-to-have enhancement."

    assert requested_phrase(text) == "99.99% uptime guarantees"


def test_requested_phrase_without_priority_sentence() -> None:
    assert requested_phrase("The solution shall provide continuous vulnerability scanning.") == "continuous vulnerability scanning"


def test_ground_truth_distinguishes_supported_from_unsupported() -> None:
    supported = "The solution shall provide complete regulatory audit trails. This requirement is high."
    unsupported = "The solution shall provide configurable data residency by region. This requirement is high."

    assert is_supported(supported) is True
    assert is_supported(unsupported) is False


def test_ground_truth_is_none_for_unrecognised_text() -> None:
    assert is_supported("Something else entirely.") is None
