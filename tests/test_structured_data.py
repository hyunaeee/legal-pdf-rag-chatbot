from app.agent import PolicyAgent
from app.retrieval import InMemoryRetriever
from app.structured_data import ContractRecord, SQLiteContractRepository


def test_contract_repository_is_tenant_isolated() -> None:
    repository = SQLiteContractRepository()
    repository.upsert(
        ContractRecord(
            contract_id="C-100",
            tenant_id="alpha",
            owner="Legal",
            status="approved",
            renewal_date="2026-12-31",
            risk_level="low",
        )
    )
    repository.upsert(
        ContractRecord(
            contract_id="C-100",
            tenant_id="beta",
            owner="Finance",
            status="review",
            renewal_date="2027-01-31",
            risk_level="high",
        )
    )

    alpha = repository.get(tenant_id="alpha", contract_id="C-100")
    beta = repository.get(tenant_id="beta", contract_id="C-100")

    assert alpha is not None
    assert beta is not None
    assert alpha.owner == "Legal"
    assert beta.owner == "Finance"


def test_agent_combines_structured_evidence() -> None:
    repository = SQLiteContractRepository()
    repository.upsert(
        ContractRecord(
            contract_id="C-200",
            tenant_id="alpha",
            owner="Procurement",
            status="pending_review",
            renewal_date="2026-11-01",
            risk_level="medium",
        )
    )
    agent = PolicyAgent(
        InMemoryRetriever(),
        contract_repository=repository,
    )

    response = agent.answer(
        tenant_id="alpha",
        query="C-200 계약 상태와 담당자는?",
        session_id=None,
    )

    assert response.route == "structured_data_then_retrieval"
    assert "pending_review" in response.answer
    assert "Procurement" in response.answer
    assert response.metrics["structured_record_count"] == 1
