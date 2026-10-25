"""Typed application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_key: str = "changeme"
    # Feature 0010: requests per minute per API key; 0 disables the tier.
    rate_limit_default_per_minute: int = 120
    rate_limit_expensive_per_minute: int = 10
