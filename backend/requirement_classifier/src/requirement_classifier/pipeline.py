"""Training, cross-validated evaluation, and persistence (FR2-FR6).

See ADR-0005 for why stratified k-fold (not a single train/test split)
and a baseline comparison are first-class parts of every run.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline

from requirement_classifier.factory import ClassifierFactory
from requirement_classifier.models import (
    CrossValidationResult,
    FoldMetrics,
    RunMetadata,
    TrainingExample,
)

_SCORING = {
    "accuracy": "accuracy",
    "precision": "precision_macro",
    "recall": "recall_macro",
    "f1": "f1_macro",
}


def _build_pipeline(classifier) -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer()),
            ("clf", classifier),
        ]
    )


def _fold_metrics_from_scores(scores: dict, prefix: str, agg) -> FoldMetrics:
    return FoldMetrics(
        accuracy=agg(scores[f"{prefix}accuracy"]),
        precision=agg(scores[f"{prefix}precision"]),
        recall=agg(scores[f"{prefix}recall"]),
        f1=agg(scores[f"{prefix}f1"]),
    )


def evaluate_with_cross_validation(
    examples: list[TrainingExample],
    model_type: str,
    seed: int,
    n_folds: int,
) -> CrossValidationResult:
    dataframe = pd.DataFrame([example.model_dump() for example in examples])
    X, y = dataframe["description"], dataframe["category"]

    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)

    model_pipeline = _build_pipeline(ClassifierFactory().create(model_type, seed))
    baseline_pipeline = _build_pipeline(
        DummyClassifier(strategy="most_frequent", random_state=seed)
    )

    scoring = {k: v for k, v in _SCORING.items()}
    model_scores = cross_validate(
        model_pipeline, X, y, cv=skf, scoring=list(scoring.values())
    )
    baseline_scores = cross_validate(
        baseline_pipeline, X, y, cv=skf, scoring=list(scoring.values())
    )

    def rename(scores: dict) -> dict:
        return {
            f"test_{name}": scores[f"test_{sk_name}"]
            for name, sk_name in scoring.items()
        }

    model_scores = rename(model_scores)
    baseline_scores = rename(baseline_scores)

    return CrossValidationResult(
        model_metrics_mean=_fold_metrics_from_scores(model_scores, "test_", np.mean),
        model_metrics_std=_fold_metrics_from_scores(model_scores, "test_", np.std),
        baseline_metrics_mean=_fold_metrics_from_scores(
            baseline_scores, "test_", np.mean
        ),
        baseline_metrics_std=_fold_metrics_from_scores(
            baseline_scores, "test_", np.std
        ),
    )


def train_final_model(
    examples: list[TrainingExample], model_type: str, seed: int
) -> Pipeline:
    dataframe = pd.DataFrame([example.model_dump() for example in examples])
    X, y = dataframe["description"], dataframe["category"]

    pipeline = _build_pipeline(ClassifierFactory().create(model_type, seed))
    pipeline.fit(X, y)
    return pipeline


def save_artifact(
    model: Pipeline, run_metadata: RunMetadata, output_dir: Path
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "model.joblib"
    metadata_path = output_dir / "run_metadata.json"

    joblib.dump(model, model_path)
    metadata_path.write_text(run_metadata.model_dump_json(indent=2))

    return model_path, metadata_path


def load_artifact(model_path: Path) -> Pipeline:
    return joblib.load(model_path)


def predict(model: Pipeline, description: str) -> str:
    return model.predict([description])[0]
