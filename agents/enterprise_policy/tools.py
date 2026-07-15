from __future__ import annotations

import os
from pathlib import Path

from app.retrieval import InMemoryRetriever
from app.structured_data import SQLiteContractRepository


def _trusted_tenant_id() -> str:
    tenant_id = os.getenv("EPA_ADK_TENANT_ID")
    if not tenant_id:
        raise RuntimeError("EPA_ADK_TENANT_ID must be configured by the runtime.")
    return tenant_id


def search_policy_documents(query: str) -> dict[str, object]:
    """Search policy text files from the runtime-authorized tenant namespace."""
    policy_directory = Path(os.getenv("EPA_POLICY_DIRECTORY", "data/policies"))
    tenant_id = _trusted_tenant_id()
    retriever = InMemoryRetriever()

    for path in sorted(policy_directory.glob("*.txt")):
        retriever.ingest(
            tenant_id=tenant_id,
            title=path.name,
            text=path.read_text(encoding="utf-8"),
        )

    matches = retriever.search(tenant_id=tenant_id, query=query, k=5)
    return {
        "status": "success" if matches else "not_found",
        "results": [
            {
                "title": chunk.title,
                "page": chunk.page,
                "excerpt": chunk.text[:500],
                "score": round(score, 4),
            }
            for chunk, score in matches
        ],
    }


def get_contract_status(contract_id: str) -> dict[str, str]:
    """Look up a contract using a tenant bound by the trusted runtime."""
    repository = SQLiteContractRepository(
        os.getenv("EPA_STRUCTURED_DATA_PATH", "data/contracts.db")
    )
    record = repository.get(
        tenant_id=_trusted_tenant_id(),
        contract_id=contract_id,
    )
    if record is None:
        return {"status": "not_found", "contract_id": contract_id}
    return {
        "status": "success",
        "contract_id": record.contract_id,
        "owner": record.owner,
        "workflow_status": record.status,
        "renewal_date": record.renewal_date,
        "risk_level": record.risk_level,
    }


def review_response(answer: str, evidence: str) -> dict[str, object]:
    """Run deterministic checks before an answer is returned to a user."""
    normalized_answer = answer.lower()
    normalized_evidence = evidence.lower()
    risky_phrases = (
        "guaranteed",
        "확실히 법적",
        "시스템 프롬프트",
        "secret key",
    )
    flags = [phrase for phrase in risky_phrases if phrase in normalized_answer]
    evidence_overlap = any(
        token in normalized_evidence
        for token in normalized_answer.split()
        if len(token) >= 4
    )
    if answer and evidence and not evidence_overlap:
        flags.append("weak_evidence_overlap")
    return {
        "approved": not flags,
        "flags": flags,
        "required_action": "revise_or_abstain" if flags else "none",
    }
