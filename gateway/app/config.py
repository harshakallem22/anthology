"""Application configuration via pydantic-settings (spec §8)."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql+asyncpg://anthology:anthology@db:5432/anthology"
    jwt_secret: str = "change-me"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    extraction_service_url: str = "http://extraction:8000"
    search_service_url: str = "http://search:8000"

    web_origin: str = "http://localhost:5173"

    cookie_name: str = "anthology_session"

    @property
    def google_oauth_enabled(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
