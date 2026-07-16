from __future__ import annotations

from app.models.base import ModelProvider
from app.models.local import LocalExtractiveProvider
from app.models.vertex import VertexGeminiProvider
from app.settings import Settings


def create_model_provider(settings: Settings) -> ModelProvider:
    backend = settings.model_backend.strip().lower()
    if backend == "local":
        return LocalExtractiveProvider()
    if backend == "vertex":
        return VertexGeminiProvider(
            project=settings.google_cloud_project or "",
            location=settings.google_cloud_location,
            model=settings.vertex_model,
            temperature=settings.model_temperature,
            max_output_tokens=settings.max_output_tokens,
        )
    raise ValueError(f"Unsupported model backend: {settings.model_backend}")
