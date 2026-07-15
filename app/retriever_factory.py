from __future__ import annotations

from app.embeddings import HashEmbeddingProvider, VertexEmbeddingProvider
from app.retrieval import InMemoryRetriever, Retriever
from app.retrieval_chroma import PersistentChromaRetriever
from app.settings import Settings


def create_retriever(settings: Settings) -> Retriever:
    backend = settings.retrieval_backend.strip().lower()
    if backend == "memory":
        return InMemoryRetriever()
    if backend != "chroma":
        raise ValueError(
            f"Unsupported retrieval backend: {settings.retrieval_backend}"
        )

    embedding_backend = settings.embedding_backend.strip().lower()
    if embedding_backend == "hash":
        embeddings = HashEmbeddingProvider()
    elif embedding_backend == "vertex":
        embeddings = VertexEmbeddingProvider(
            project=settings.google_cloud_project or "",
            location=settings.google_cloud_location,
            model=settings.vertex_embedding_model,
        )
    else:
        raise ValueError(
            f"Unsupported embedding backend: {settings.embedding_backend}"
        )

    return PersistentChromaRetriever(
        path=settings.vector_store_path,
        embedding_provider=embeddings,
    )
