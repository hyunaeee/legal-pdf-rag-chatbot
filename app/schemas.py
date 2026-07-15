from typing import Any

from pydantic import BaseModel, Field


class Source(BaseModel):
    document_id: str
    title: str
    page: int | None = None
    excerpt: str
    score: float = Field(ge=0, le=1)


class ChatRequest(BaseModel):
    query: str = Field(min_length=2, max_length=4000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    route: str
    model: str | None = None
    sources: list[Source] = Field(default_factory=list)
    safety_flags: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    document_id: str
    title: str
    chunks: int
    tenant_id: str


class HealthResponse(BaseModel):
    status: str
    environment: str
    model_backend: str
