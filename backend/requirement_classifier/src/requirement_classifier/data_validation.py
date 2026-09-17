"""Data quality validation (FR9/NFR6).

Fails fast and explicitly rather than silently training on a dataset
too small or too imbalanced to produce a meaningful model.
"""
from collections import Counter

from requirement_classifier.models import TrainingExample


class InsufficientDataError(Exception):
    pass


def validate_training_data(
    examples: list[TrainingExample], min_examples_per_class: int
) -> None:
    if not examples:
        raise InsufficientDataError("No training examples found.")

    counts = Counter(example.category for example in examples)
    for category, count in counts.items():
        if count < min_examples_per_class:
            raise InsufficientDataError(
                f"Category '{category}' has only {count} example(s); "
                f"at least {min_examples_per_class} are required per class."
            )
