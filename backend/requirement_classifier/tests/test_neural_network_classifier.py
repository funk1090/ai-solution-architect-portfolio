"""Unit tests for Feature 0006's neural_network addition to ClassifierFactory."""
from sklearn.neural_network import MLPClassifier

from requirement_classifier.factory import ClassifierFactory
from requirement_classifier.pipeline import evaluate_with_cross_validation
from conftest_helpers import build_synthetic_examples


def test_factory_creates_a_neural_network_classifier() -> None:
    classifier = ClassifierFactory().create("neural_network", seed=42)

    assert isinstance(classifier, MLPClassifier)


def test_neural_network_can_be_cross_validated_like_any_other_model() -> None:
    """FR2: same evaluation pipeline, no special-casing required."""
    examples = build_synthetic_examples(per_class=15, seed=42)

    result = evaluate_with_cross_validation(
        examples, model_type="neural_network", seed=42, n_folds=5
    )

    # Structural check: valid metrics were produced, not a specific
    # accuracy threshold -- this is a genuine comparison (Feature 0006),
    # not an assumption that the neural network must "win".
    assert 0.0 <= result.model_metrics_mean.accuracy <= 1.0
    assert result.baseline_metrics_mean.accuracy < 1.0
