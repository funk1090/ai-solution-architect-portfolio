"""Typed application configuration.

Reads values from a local .env file (never committed to git) with
sensible defaults, so the application fails fast and explicitly if
misconfigured, instead of failing later with a confusing error deep
inside the database or filesystem layer.
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+psycopg2://portfolio:portfolio@localhost:5432/portfolio"
    )
    document_output_dir: Path = Path("./datasets/generated")
    generation_seed: int = 42
