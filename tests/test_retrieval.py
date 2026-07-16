from app.retrieval import InMemoryRetriever


def test_retrieval_is_tenant_isolated() -> None:
    retriever = InMemoryRetriever()
    retriever.ingest(tenant_id="alpha", title="policy.pdf", text="휴가는 연 15일입니다.")
    retriever.ingest(tenant_id="beta", title="policy.pdf", text="휴가는 연 20일입니다.")

    alpha = retriever.search(tenant_id="alpha", query="휴가", k=5)
    beta = retriever.search(tenant_id="beta", query="휴가", k=5)

    assert len(alpha) == 1
    assert len(beta) == 1
    assert "15일" in alpha[0][0].text
    assert "20일" in beta[0][0].text


def test_ingestion_is_idempotent_for_identical_content() -> None:
    retriever = InMemoryRetriever()
    first_id, first_count = retriever.ingest(
        tenant_id="alpha", title="policy.pdf", text="동일한 문서 내용"
    )
    second_id, second_count = retriever.ingest(
        tenant_id="alpha", title="policy.pdf", text="동일한 문서 내용"
    )

    assert first_id == second_id
    assert first_count == second_count
    assert retriever.count("alpha") == first_count
