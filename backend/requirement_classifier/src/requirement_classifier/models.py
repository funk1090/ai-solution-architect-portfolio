"""Typed domain models for the requirement classifier."""
from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class TrainingExample(BaseModel):
    description: str
    category: str
    priority: str


class FoldMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float


class CrossValidationResult(BaseModel):
    model_metrics_mean: FoldMetrics
    model_metrics_std: FoldMetrics
    baseline_metrics_mean: FoldMetrics
    baseline_metrics_std: FoldMetrics


class RunMetadata(BaseModel):
    model_type: str
    seed: int
    n_folds: int
    dataset_size: int
    class_distribution: dict[str, int]
    cross_validation: CrossValidationResult
    trained_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
