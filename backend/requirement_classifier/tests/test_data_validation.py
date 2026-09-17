"""Unit tests for data quality validation (FR9/NFR6)."""
import pytest

from requirement_classifier.data_validation import (
    InsufficientDataError,
    validate_training_data,
)
from requirement_classifier.models import TrainingExample


def test_raises_when_no_examples() -> None:
    with pytest.raises(InsufficientDataError):
        validate_training_data([], min_examples_per_class=10)


def test_raises_when_a_class_is_underrepresented() -> None:
    examples = [
        TrainingExample(description="text", category="Security", priority="Low")
        for _ in range(3)
    ]

    with pytest.raises(InsufficientDataError):
        validate_training_data(examples, min_examples_per_class=10)


def test_passes_when_every_class_meets_the_minimum() -> None:
    examples = [
        TrainingExample(description="text", category="Security", priority="Low")
        for _ in range(10)
    ] + [
        TrainingExample(description="text", category="Performance", priority="Low")
        for _ in range(10)
    ]

    validate_training_data(examples, min_examples_per_class=10)  # should not raise
