"""Command-line entry point."""
import logging

import typer

from requirement_classifier.config import Settings
from requirement_classifier.data_validation import validate_training_data
from requirement_classifier.models import RunMetadata
from requirement_classifier.pipeline import (
    evaluate_with_cross_validation,
    load_artifact,
    predict,
    save_artifact,
    train_final_model,
)
from requirement_classifier.repository import PostgresTrainingDataReader

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = typer.Typer()


@app.callback()
def callback() -> None:
    """Requirement Intelligence Engine CLI."""


@app.command()
def train(
    model_type: str = typer.Option("logistic_regression", help="Classifier to train."),
) -> None:
    settings = Settings()

    reader = PostgresTrainingDataReader(settings.database_url)
    examples = reader.get_training_examples()

    validate_training_data(examples, settings.min_examples_per_class)

    logger.info("Training on %d examples", len(examples))
    cv_result = evaluate_with_cross_validation(
        examples, model_type, settings.seed, settings.n_folds
    )

    typer.echo(f"Model    (mean over {settings.n_folds} folds): {cv_result.model_metrics_mean}")
    typer.echo(f"Baseline (mean over {settings.n_folds} folds): {cv_result.baseline_metrics_mean}")

    class_distribution: dict[str, int] = {}
    for example in examples:
        class_distribution[example.category] = class_distribution.get(example.category, 0) + 1

    final_model = train_final_model(examples, model_type, settings.seed)
    run_metadata = RunMetadata(
        model_type=model_type,
        seed=settings.seed,
        n_folds=settings.n_folds,
        dataset_size=len(examples),
        class_distribution=class_distribution,
        cross_validation=cv_result,
    )
    model_path, metadata_path = save_artifact(
        final_model, run_metadata, settings.model_output_dir
    )
    typer.echo(f"Model saved to {model_path}")
    typer.echo(f"Run metadata saved to {metadata_path}")


@app.command()
def classify(
    text: str = typer.Option(..., help="Requirement description to classify."),
) -> None:
    settings = Settings()
    model_path = settings.model_output_dir / "model.joblib"
    model = load_artifact(model_path)
    category = predict(model, text)
    typer.echo(f"Predicted category: {category}")


if __name__ == "__main__":
    app()
