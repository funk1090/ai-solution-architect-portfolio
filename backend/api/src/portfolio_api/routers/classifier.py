"""Wraps requirement_classifier (Phase 3/6)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from portfolio_api.auth import verify_api_key

router = APIRouter(prefix="/classifier", tags=["classifier"], dependencies=[Depends(verify_api_key)])


class ClassifyRequest(BaseModel):
    text: str


class ClassifyResponse(BaseModel):
    category: str


class CompareResponse(BaseModel):
    best_model: str
    accuracies: dict[str, float]


@router.post("/classify", response_model=ClassifyResponse)
def classify_text(request: ClassifyRequest) -> ClassifyResponse:
    from requirement_classifier.config import Settings
    from requirement_classifier.pipeline import load_artifact, predict

    settings = Settings()
    model = load_artifact(settings.model_output_dir / "model.joblib")
    category = predict(model, request.text)
    return ClassifyResponse(category=category)


@router.post("/compare", response_model=CompareResponse)
def compare_models() -> CompareResponse:
    """Reuses the exact comparison built for the 'compare' CLI command
    (Feature 0006) -- same functions, same methodology.
    """
    from requirement_classifier.config import Settings
    from requirement_classifier.data_validation import validate_training_data
    from requirement_classifier.models import RunMetadata
    from requirement_classifier.pipeline import (
        evaluate_with_cross_validation,
        save_artifact,
        train_final_model,
    )
    from requirement_classifier.repository import PostgresTrainingDataReader

    settings = Settings()
    reader = PostgresTrainingDataReader(settings.database_url)
    examples = reader.get_training_examples()
    validate_training_data(examples, settings.min_examples_per_class)

    model_types = ["logistic_regression", "neural_network"]
    results = {
        model_type: evaluate_with_cross_validation(
            examples, model_type, settings.seed, settings.n_folds
        )
        for model_type in model_types
    }
    best_model_type = max(
        model_types, key=lambda mt: results[mt].model_metrics_mean.accuracy
    )

    class_distribution: dict[str, int] = {}
    for example in examples:
        class_distribution[example.category] = class_distribution.get(example.category, 0) + 1

    final_model = train_final_model(examples, best_model_type, settings.seed)
    run_metadata = RunMetadata(
        model_type=best_model_type,
        seed=settings.seed,
        n_folds=settings.n_folds,
        dataset_size=len(examples),
        class_distribution=class_distribution,
        cross_validation=results[best_model_type],
    )
    save_artifact(final_model, run_metadata, settings.model_output_dir)

    return CompareResponse(
        best_model=best_model_type,
        accuracies={mt: results[mt].model_metrics_mean.accuracy for mt in model_types},
    )
