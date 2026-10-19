"""Frontend configuration (NFR1/NFR4). The API key is read here, on the
Streamlit server side, and is never sent to the browser."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_base_url: str = "http://localhost:8000"
    api_key: str = "changeme"
    # Quick calls (health, summary, classify) vs. long operations
    # (ingest, index, compare, ask with a local LLM), in seconds.
    short_timeout: float = 15.0
    long_timeout: float = 600.0
