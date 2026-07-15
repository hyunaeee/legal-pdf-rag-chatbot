from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="EPA_", extra="ignore")

    app_name: str = "Enterprise Policy Agent"
    environment: str = "local"
    log_level: str = "INFO"
    max_upload_mb: int = Field(default=10, ge=1, le=100)
    retrieval_k: int = Field(default=5, ge=1, le=20)
    require_tenant_header: bool = True
    model_backend: str = "local"
    google_cloud_project: str | None = None
    google_cloud_location: str = "asia-northeast3"
    vertex_model: str = "gemini-2.5-flash"


@lru_cache
def get_settings() -> Settings:
    return Settings()
