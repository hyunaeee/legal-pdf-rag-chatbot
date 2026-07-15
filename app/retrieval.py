from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from threading import RLock


_TOKEN_RE = re.compile(r"[\w가-힣]+", re.UNICODE)
_KOREAN_RE = re.compile(r"[가-힣]+")


@dataclass(frozen=True)
class Chunk:
    document_id: str
    tenant_id: str
    title: str
    page: int | None
    text: str
    tokens: frozenset[str]


class InMemoryRetriever:
    """Deterministic tenant-aware retrieval for local development and tests."""

    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._lock = RLock()

    @staticmethod
    def _tokenize(text: str) -> frozenset[str]:
        tokens = {token.lower() for token in _TOKEN_RE.findall(text)}
        for korean_word in _KOREAN_RE.findall(text):
            for width in (2, 3):
                tokens.update(
                    korean_word[index : index + width]
                    for index in range(max(0, len(korean_word) - width + 1))
                )
        return frozenset(tokens)

    @staticmethod
    def _chunk_text(
        text: str,
        size: int = 900,
        overlap: int = 120,
    ) -> list[str]:
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

    def ingest(
        self,
        *,
        tenant_id: str,
        title: str,
        text: str,
        page: int | None = None,
    ) -> tuple[str, int]:
        content_key = f"{tenant_id}:{title}:{text}"
        digest = hashlib.sha256(content_key.encode()).hexdigest()[:16]
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
                if not (
                    chunk.tenant_id == tenant_id
                    and chunk.document_id == digest
                )
            ]
            self._chunks.extend(new_chunks)
        return digest, len(new_chunks)

    def search(
        self,
        *,
        tenant_id: str,
        query: str,
        k: int,
    ) -> list[tuple[Chunk, float]]:
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scored: list[tuple[Chunk, float]] = []
        with self._lock:
            candidates = [
                chunk
                for chunk in self._chunks
                if chunk.tenant_id == tenant_id
            ]

        for chunk in candidates:
            intersection = len(query_tokens & chunk.tokens)
            if intersection == 0:
                continue
            denominator = math.sqrt(
                len(query_tokens) * max(len(chunk.tokens), 1)
            )
            cosine_like = intersection / denominator
            scored.append((chunk, min(cosine_like, 1.0)))

        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:k]

    def count(self, tenant_id: str | None = None) -> int:
        with self._lock:
            if tenant_id is None:
                return len(self._chunks)
            return sum(
                chunk.tenant_id == tenant_id for chunk in self._chunks
            )
