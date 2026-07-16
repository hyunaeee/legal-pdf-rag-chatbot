from app.agent import PolicyAgent
from app.models.base import GenerationRequest, GenerationResult
from app.retrieval import InMemoryRetriever


class TokenReportingProvider:
    name = "token-reporting-test"

    def generate(self, request: GenerationRequest) -> GenerationResult:
        return GenerationResult(
            text=f"Grounded answer from {len(request.evidence)} evidence item.",
            model=self.name,
            input_tokens=1000,
            output_tokens=500,
            finish_reason="STOP",
        )


def test_agent_calculates_configured_request_cost() -> None:
    retriever = InMemoryRetriever()
    retriever.ingest(
        tenant_id="alpha",
        title="policy.pdf",
        text="보안 교육은 매년 실시합니다.",
    )
    agent = PolicyAgent(
        retriever,
        model_provider=TokenReportingProvider(),
        input_cost_per_million_usd=2.0,
        output_cost_per_million_usd=8.0,
    )

    response = agent.answer(
        tenant_id="alpha",
        query="보안 교육 주기는?",
        session_id=None,
    )

    assert response.metrics["estimated_cost_usd"] == 0.006
    assert response.metrics["tokens_per_second"] > 0
    assert agent.metrics.snapshot()["estimated_cost_usd"] == 0.006
