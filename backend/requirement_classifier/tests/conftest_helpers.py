"""Shared test fixtures.

Builds a small synthetic dataset mirroring the correlated vocabulary
structure from EnterpriseFakerProvider (ADR-0004), without depending on
the document-generator project (independent uv projects, ADR-0003).
"""
import random

from requirement_classifier.models import TrainingExample

_VOCAB = {
    "Security": [
        "end-to-end encryption",
        "multi-factor authentication",
        "role-based access control",
    ],
    "Performance": [
        "sub-second response times",
        "high-throughput processing",
        "low-latency data access",
    ],
    "Reliability": [
        "99.99% uptime guarantees",
        "automatic failover",
        "graceful degradation",
    ],
}


def build_synthetic_examples(
    per_class: int = 15, seed: int = 42, noise: float = 0.15
) -> list[TrainingExample]:
    rng = random.Random(seed)
    all_phrases = [phrase for phrases in _VOCAB.values() for phrase in phrases]

    examples = []
    for category, phrases in _VOCAB.items():
        for _ in range(per_class):
            phrase = rng.choice(all_phrases) if rng.random() < noise else rng.choice(phrases)
            examples.append(
                TrainingExample(
                    description=f"The solution shall provide {phrase}.",
                    category=category,
                    priority="Medium",
                )
            )
    return examples
