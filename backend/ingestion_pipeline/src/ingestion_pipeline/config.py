"""Typed application configuration.

Points at the SAME PostgreSQL database used by document-generator
(the "portfolio" database) — this pipeline reads its document_metadata
table and writes its own ingested_content table. Same database,
different tables, different Python projects (see ADR-0003).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+psycopg2://portfolio:portfolio@localhost:5432/portfolio"
    )
