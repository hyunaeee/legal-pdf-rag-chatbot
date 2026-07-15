from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="EPA_",
        extra="ignore",
    )

    app_name: str = "Enterprise Policy Agent"
    environment: str = "local"
    log_level: str = "INFO"
    max_upload_mb: int = Field(default=10, ge=1, le=100)
    retrieval_k: int = Field(default=5, ge=1, le=20)
    require_tenant_header: bool = True

    retrieval_backend: str = "memory"
    vector_store_path: str = "data/chroma"
    embedding_backend: str = "hash"
    vertex_embedding_model: str = "gemini-embedding-001"

    model_backend: str = "local"
    model_temperature: float = Field(default=0.1, ge=0, le=2)
    max_output_tokens: int = Field(default=1024, ge=64, le=8192)
    google_cloud_project: str | None = None
    google_cloud_location: str = "asia-northeast3"
    vertex_model: str = "gemini-2.5-flash"

    session_store_path: str = ":memory:"
    session_history_limit: int = Field(default=6, ge=0, le=20)
    structured_data_path: str = ":memory:"

    otel_enabled: bool = False
    otel_service_name: str = "enterprise-policy-agent"
    otel_exporter_otlp_endpoint: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
