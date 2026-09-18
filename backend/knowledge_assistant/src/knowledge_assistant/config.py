"""Typed application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql+psycopg2://portfolio:portfolio@localhost:5432/portfolio"
    )
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3:latest"
    embedding_model_name: str = "all-MiniLM-L6-v2"
    chunk_size: int = 200
    chunk_overlap: int = 40
    top_k: int = 4
    similarity_threshold: float = 0.3
