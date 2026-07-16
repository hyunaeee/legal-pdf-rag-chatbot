from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from app.embeddings import EmbeddingProvider
from app.retrieval import Chunk, chunk_text, tokenize


class PersistentChromaRetriever:
    """Persistent vector retriever with mandatory tenant metadata filtering."""

    def __init__(
        self,
        *,
        path: str,
        embedding_provider: EmbeddingProvider,
        collection_name: str = "enterprise_policy_chunks",
    ) -> None:
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError(
                "Install the AI dependencies with `pip install -e '.[ai]'`."
            ) from exc

        Path(path).mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=path)
        self.collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self.embedding_provider = embedding_provider

    def ingest(
        self,
        *,
        tenant_id: str,
        title: str,
        text: str,
        page: int | None = None,
    ) -> tuple[str, int]:
        document_id = hashlib.sha256(
            f"{tenant_id}:{title}:{text}".encode()
        ).hexdigest()[:16]
        chunks = chunk_text(text)
        if not chunks:
            return document_id, 0

        ids = [
            f"{document_id}:{page or 0}:{index}"
            for index in range(len(chunks))
        ]
        metadatas = [
            {
                "document_id": document_id,
                "tenant_id": tenant_id,
                "title": title,
                "page": page if page is not None else -1,
            }
            for _ in chunks
        ]
        embeddings = self.embedding_provider.embed_documents(chunks)
        self.collection.upsert(
            ids=ids,
            documents=chunks,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        return document_id, len(chunks)

    def search(
        self,
        *,
        tenant_id: str,
        query: str,
        k: int,
    ) -> list[tuple[Chunk, float]]:
        result = self.collection.query(
            query_embeddings=[self.embedding_provider.embed_query(query)],
            n_results=k,
            where={"tenant_id": tenant_id},
            include=["documents", "metadatas", "distances"],
        )
        documents = self._first_result_list(result, "documents")
        metadatas = self._first_result_list(result, "metadatas")
        distances = self._first_result_list(result, "distances")

        matches: list[tuple[Chunk, float]] = []
        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances,
            strict=False,
        ):
            if not isinstance(document, str) or not isinstance(metadata, dict):
                continue
            page_value = int(metadata.get("page", -1))
            chunk = Chunk(
                document_id=str(metadata["document_id"]),
                tenant_id=str(metadata["tenant_id"]),
                title=str(metadata["title"]),
                page=None if page_value < 0 else page_value,
                text=document,
                tokens=tokenize(document),
            )
            score = max(0.0, min(1.0, 1.0 - float(distance)))
            matches.append((chunk, score))
        return matches

    def count(self, tenant_id: str | None = None) -> int:
        if tenant_id is None:
            return int(self.collection.count())
        result = self.collection.get(
            where={"tenant_id": tenant_id},
            include=["metadatas"],
        )
        return len(result.get("ids", []))

    @staticmethod
    def _first_result_list(
        result: dict[str, Any],
        key: str,
    ) -> list[Any]:
        values = result.get(key) or []
        if not values or not isinstance(values[0], list):
            return []
        return values[0]
