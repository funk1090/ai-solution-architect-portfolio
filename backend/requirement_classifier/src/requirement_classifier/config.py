"""Typed application configuration.

Points at the same PostgreSQL database as document-generator and
ingestion_pipeline (see ADR-0003 on the accepted duplication of schema
knowledge across independent modules).
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+psycopg2://portfolio:portfolio@localhost:5432/portfolio"
    )
    model_output_dir: Path = Path("./models")
    seed: int = 42
    n_folds: int = 5
    min_examples_per_class: int = 10
