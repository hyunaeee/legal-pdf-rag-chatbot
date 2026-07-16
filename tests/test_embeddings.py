import math

from app.embeddings import HashEmbeddingProvider


def test_hash_embeddings_are_deterministic_and_normalized() -> None:
    provider = HashEmbeddingProvider(dimension=64)

    first = provider.embed_query("보안 교육은 매년 실시합니다")
    second = provider.embed_query("보안 교육은 매년 실시합니다")

    assert first == second
    assert len(first) == 64
    assert math.isclose(
        math.sqrt(sum(value * value for value in first)),
        1.0,
        rel_tol=1e-9,
    )


def test_hash_embeddings_keep_document_batch_order() -> None:
    provider = HashEmbeddingProvider(dimension=64)
    texts = ["휴가 규정", "계약 상태"]

    embeddings = provider.embed_documents(texts)

    assert embeddings[0] == provider.embed_query(texts[0])
    assert embeddings[1] == provider.embed_query(texts[1])
    assert embeddings[0] != embeddings[1]
