from __future__ import annotations

import io
import logging

from fastapi import (
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    UploadFile,
    status,
)
from pypdf import PdfReader

from app.agent import PolicyAgent
from app.models import create_model_provider
from app.observability import configure_observability
from app.retriever_factory import create_retriever
from app.schemas import ChatRequest, ChatResponse, HealthResponse, IngestResponse
from app.settings import Settings, get_settings
from app.structured_data import SQLiteContractRepository

logger = logging.getLogger(__name__)
settings = get_settings()
retriever = create_retriever(settings)
model_provider = create_model_provider(settings)
contract_repository = SQLiteContractRepository(settings.structured_data_path)
agent = PolicyAgent(
    retriever=retriever,
    retrieval_k=settings.retrieval_k,
    model_provider=model_provider,
    contract_repository=contract_repository,
)

app = FastAPI(
    title=settings.app_name,
    version="0.6.0",
    description="Tenant-aware policy RAG and agent orchestration service.",
)
observability_enabled = configure_observability(app, settings)


def tenant_id(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    config: Settings = Depends(get_settings),
) -> str:
    if config.require_tenant_header and not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID header is required.",
        )
    return x_tenant_id or "local-demo"


@app.get("/health", response_model=HealthResponse, tags=["operations"])
def health(config: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        environment=config.environment,
        model_backend=config.model_backend,
    )


@app.post("/v1/documents", response_model=IngestResponse, tags=["documents"])
async def ingest_document(
    file: UploadFile = File(...),
    tenant: str = Depends(tenant_id),
    config: Settings = Depends(get_settings),
) -> IngestResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only application/pdf uploads are accepted.",
        )

    payload = await file.read()
    if len(payload) > config.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded PDF exceeds the configured limit.",
        )

    try:
        reader = PdfReader(io.BytesIO(payload))
        pages = [
            (index + 1, page.extract_text() or "")
            for index, page in enumerate(reader.pages)
        ]
    except Exception as exc:
        logger.warning("PDF parsing failed", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded PDF could not be parsed.",
        ) from exc

    document_id = ""
    chunk_count = 0
    title = file.filename or "uploaded-document.pdf"
    for page_number, text in pages:
        if not text.strip():
            continue
        document_id, created = retriever.ingest(
            tenant_id=tenant,
            title=title,
            text=text,
            page=page_number,
        )
        chunk_count += created

    if not chunk_count:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The PDF does not contain extractable text.",
        )

    return IngestResponse(
        document_id=document_id,
        title=title,
        chunks=chunk_count,
        tenant_id=tenant,
    )


@app.post("/v1/chat", response_model=ChatResponse, tags=["agents"])
def chat(request: ChatRequest, tenant: str = Depends(tenant_id)) -> ChatResponse:
    return agent.answer(
        tenant_id=tenant,
        query=request.query,
        session_id=request.session_id,
    )


@app.get("/metrics", tags=["operations"])
def metrics() -> dict[str, object]:
    return {
        "agent": agent.metrics.snapshot(),
        "indexed_chunks": retriever.count(),
        "retrieval_backend": settings.retrieval_backend,
        "embedding_backend": settings.embedding_backend,
        "model_provider": model_provider.name,
        "observability_enabled": observability_enabled,
    }
