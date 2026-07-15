from __future__ import annotations

import hashlib
import math
from typing import Protocol

from app.retrieval import tokenize


class EmbeddingProvider(Protocol):
    name: str

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class HashEmbeddingProvider:
    """Deterministic dependency-free embeddings for local vector-store tests."""

    name = "hash-embedding"

    def __init__(self, dimension: int = 256) -> None:
        if dimension < 32:
            raise ValueError("Embedding dimension must be at least 32.")
        self.dimension = dimension

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for token in tokenize(text):
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


class VertexEmbeddingProvider:
    """Vertex AI embedding provider using the Google Gen AI SDK."""

    name = "vertex-embedding"

    def __init__(
        self,
        *,
        project: str,
        location: str,
        model: str,
    ) -> None:
        if not project:
            raise ValueError("A Google Cloud project is required for Vertex embeddings.")

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError(
                "Install the AI dependencies with `pip install -e '.[ai]'`."
            ) from exc

        self._types = types
        self._client = genai.Client(
            vertexai=True,
            project=project,
            location=location,
            http_options=types.HttpOptions(api_version="v1"),
        )
        self.model = model

    def _embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        response = self._client.models.embed_content(
            model=self.model,
            contents=texts,
            config=self._types.EmbedContentConfig(task_type=task_type),
        )
        embeddings = getattr(response, "embeddings", None) or []
        return [list(item.values) for item in embeddings]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts, "RETRIEVAL_DOCUMENT")

    def embed_query(self, text: str) -> list[float]:
        embeddings = self._embed([text], "RETRIEVAL_QUERY")
        if not embeddings:
            raise RuntimeError("Vertex AI did not return a query embedding.")
        return embeddings[0]
