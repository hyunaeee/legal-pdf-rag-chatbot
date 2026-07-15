from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from threading import RLock


_TOKEN_RE = re.compile(r"[\w가-힣]+", re.UNICODE)


@dataclass(frozen=True)
class Chunk:
    document_id: str
    tenant_id: str
    title: str
    page: int | None
    text: str
    tokens: frozenset[str]


class InMemoryRetriever:
    """Deterministic local retrieval backend used for development and tests.

    The interface is intentionally small so it can later be replaced by Vertex AI
    Vector Search, AlloyDB, or another enterprise retrieval backend.
    """

    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._lock = RLock()

    @staticmethod
    def _tokenize(text: str) -> frozenset[str]:
        return frozenset(token.lower() for token in _TOKEN_RE.findall(text))

    @staticmethod
    def _chunk_text(text: str, size: int = 900, overlap: int = 120) -> list[str]:
        normalized = " ".join(text.split())
        if not normalized:
            return []
        chunks: list[str] = []
        start = 0
        while start < len(normalized):
            end = min(len(normalized), start + size)
            chunks.append(normalized[start:end])
            if end == len(normalized):
                break
            start = max(start + 1, end - overlap)
        return chunks

    def ingest(self, *, tenant_id: str, title: str, text: str, page: int | None = None) -> tuple[str, int]:
        digest = hashlib.sha256(f"{tenant_id}:{title}:{text}".encode()).hexdigest()[:16]
        new_chunks = [
            Chunk(
                document_id=digest,
                tenant_id=tenant_id,
                title=title,
                page=page,
                text=chunk,
                tokens=self._tokenize(chunk),
            )
            for chunk in self._chunk_text(text)
        ]
        with self._lock:
            self._chunks = [
                chunk
                for chunk in self._chunks
                if not (chunk.tenant_id == tenant_id and chunk.document_id == digest)
            ]
            self._chunks.extend(new_chunks)
        return digest, len(new_chunks)

    def search(self, *, tenant_id: str, query: str, k: int) -> list[tuple[Chunk, float]]:
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        scored: list[tuple[Chunk, float]] = []
        with self._lock:
            candidates = [chunk for chunk in self._chunks if chunk.tenant_id == tenant_id]
        for chunk in candidates:
            intersection = len(query_tokens & chunk.tokens)
            if intersection == 0:
                continue
            cosine_like = intersection / math.sqrt(len(query_tokens) * max(len(chunk.tokens), 1))
            scored.append((chunk, min(cosine_like, 1.0)))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:k]

    def count(self, tenant_id: str | None = None) -> int:
        with self._lock:
            if tenant_id is None:
                return len(self._chunks)
            return sum(chunk.tenant_id == tenant_id for chunk in self._chunks)
