from app.agent import PolicyAgent
from app.models.base import GenerationRequest
from app.models.factory import create_model_provider
from app.models.local import LocalExtractiveProvider
from app.retrieval import InMemoryRetriever
from app.settings import Settings


def test_local_provider_is_default() -> None:
    provider = create_model_provider(Settings())
    assert isinstance(provider, LocalExtractiveProvider)


def test_local_provider_abstains_without_evidence() -> None:
    result = LocalExtractiveProvider().generate(
        GenerationRequest(
            query="규정은 무엇입니까?",
            evidence=[],
            system_instruction="Use evidence only.",
        )
    )
    assert "근거를 찾지 못했습니다" in result.text
    assert result.model == "local-extractive"


def test_agent_reports_selected_model() -> None:
    retriever = InMemoryRetriever()
    retriever.ingest(
        tenant_id="alpha",
        title="leave-policy.pdf",
        text="연차 휴가는 연 15일입니다.",
    )
    response = PolicyAgent(retriever).answer(
        tenant_id="alpha",
        query="연차 휴가는 며칠입니까?",
        session_id="session-1",
    )
    assert response.model == "local-extractive"
    assert response.metrics["retrieval_count"] == 1
