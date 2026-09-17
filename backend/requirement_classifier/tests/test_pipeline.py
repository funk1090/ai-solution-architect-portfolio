"""Unit tests for the training/evaluation pipeline.

These validate the core promise of ADR-0004 and ADR-0005: given
correlated (but noisy) synthetic data, a trained model must
meaningfully outperform the majority-class baseline.
"""
from requirement_classifier.pipeline import (
    evaluate_with_cross_validation,
    predict,
    train_final_model,
)
from conftest_helpers import build_synthetic_examples


def test_model_beats_baseline_on_correlated_data() -> None:
    examples = build_synthetic_examples(per_class=15, seed=42)

    result = evaluate_with_cross_validation(
        examples, model_type="logistic_regression", seed=42, n_folds=5
    )

    assert result.model_metrics_mean.accuracy > result.baseline_metrics_mean.accuracy


def test_trained_model_predicts_a_known_category() -> None:
    examples = build_synthetic_examples(per_class=15, seed=42)
    model = train_final_model(examples, model_type="logistic_regression", seed=42)

    prediction = predict(
        model, "The solution shall provide multi-factor authentication for all users."
    )

    assert prediction in {"Security", "Performance", "Reliability"}
