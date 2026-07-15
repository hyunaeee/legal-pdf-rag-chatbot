from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.agent import PolicyAgent
from app.retrieval import InMemoryRetriever
from app.session_store import SQLiteSessionStore
from app.structured_data import ContractRecord, SQLiteContractRepository


Case = dict[str, Any]


def load_cases() -> list[Case]:
    cases_path = Path(__file__).with_name("cases.jsonl")
    lines = cases_path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line]


def add_contract(
    repository: SQLiteContractRepository,
    *,
    tenant_id: str,
    payload: dict[str, Any],
) -> None:
    repository.upsert(
        ContractRecord(
            contract_id=str(payload["contract_id"]),
            tenant_id=tenant_id,
            owner=str(payload["owner"]),
            status=str(payload["status"]),
            renewal_date=str(payload["renewal_date"]),
            risk_level=str(payload["risk_level"]),
        )
    )


def evaluate_case(case: Case) -> dict[str, Any]:
    tenant_id = str(case["tenant_id"])
    retriever = InMemoryRetriever()
    retriever.ingest(
        tenant_id=tenant_id,
        title=f"{case['id']}.txt",
        text=str(case["document"]),
    )
    if case.get("other_tenant_id"):
        retriever.ingest(
            tenant_id=str(case["other_tenant_id"]),
            title="other-tenant.txt",
            text=str(case["other_document"]),
        )

    contracts = SQLiteContractRepository()
    if contract := case.get("contract"):
        add_contract(contracts, tenant_id=tenant_id, payload=contract)
    if other_contract := case.get("other_contract"):
        add_contract(
            contracts,
            tenant_id=str(case["other_tenant_id"]),
            payload=other_contract,
        )

    sessions = SQLiteSessionStore()
    agent = PolicyAgent(
        retriever,
        contract_repository=contracts,
        session_store=sessions,
    )
    session_id = f"evaluation-{case['id']}"
    if prior_query := case.get("prior_query"):
        agent.answer(
            tenant_id=tenant_id,
            query=str(prior_query),
            session_id=session_id,
        )

    response = agent.answer(
        tenant_id=tenant_id,
        query=str(case["query"]),
        session_id=session_id,
    )
    checks: dict[str, bool] = {}
    if expected := case.get("expected_contains"):
        checks["expected_contains"] = str(expected) in response.answer
    if expected := case.get("expected_contains_additional"):
        checks["expected_contains_additional"] = str(expected) in response.answer
    if forbidden := case.get("forbidden_contains"):
        checks["forbidden_contains"] = str(forbidden) not in response.answer
    if expected_flag := case.get("expected_flag"):
        checks["expected_flag"] = str(expected_flag) in response.safety_flags
    if expected_route := case.get("expected_route"):
        checks["expected_route"] = response.route == str(expected_route)
    if expected_title := case.get("expected_source_title"):
        checks["expected_source_title"] = any(
            source.title == str(expected_title) for source in response.sources
        )
    for metric, expected_value in case.get("expected_metric", {}).items():
        checks[f"metric:{metric}"] = response.metrics.get(metric) == expected_value

    passed = all(checks.values())
    return {
        "id": case["id"],
        "category": case["category"],
        "passed": passed,
        "checks": checks,
        "route": response.route,
        "model": response.model,
        "safety_flags": response.safety_flags,
        "source_titles": [source.title for source in response.sources],
        "metrics": response.metrics,
    }


def main() -> None:
    results = [evaluate_case(case) for case in load_cases()]
    category_totals: dict[str, dict[str, int | float]] = defaultdict(
        lambda: {"total": 0, "passed": 0, "pass_rate": 0.0}
    )

    for result in results:
        category = str(result["category"])
        category_totals[category]["total"] += 1
        category_totals[category]["passed"] += int(bool(result["passed"]))
        print(
            json.dumps(
                {"id": result["id"], "passed": result["passed"]},
                ensure_ascii=False,
            )
        )

    for values in category_totals.values():
        total = int(values["total"])
        passed = int(values["passed"])
        values["pass_rate"] = passed / total if total else 0.0

    total = len(results)
    passed = sum(int(bool(result["passed"])) for result in results)
    report = {
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total else 0.0,
        },
        "categories": dict(category_totals),
        "results": results,
    }
    report_path = Path(__file__).with_name("report.json")
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report["summary"]))
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
