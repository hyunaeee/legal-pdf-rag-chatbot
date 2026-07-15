from __future__ import annotations

import json
from pathlib import Path

from app.agent import PolicyAgent
from app.retrieval import InMemoryRetriever


def load_cases() -> list[dict[str, object]]:
    cases_path = Path(__file__).with_name("cases.jsonl")
    lines = cases_path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line]


def main() -> None:
    cases = load_cases()
    passed = 0

    for case in cases:
        retriever = InMemoryRetriever()
        retriever.ingest(
            tenant_id=str(case["tenant_id"]),
            title=f"{case['id']}.txt",
            text=str(case["document"]),
        )
        if case.get("other_tenant_id"):
            retriever.ingest(
                tenant_id=str(case["other_tenant_id"]),
                title="other-tenant.txt",
                text=str(case["other_document"]),
            )

        response = PolicyAgent(retriever).answer(
            tenant_id=str(case["tenant_id"]),
            query=str(case["query"]),
            session_id=None,
        )
        checks: list[bool] = []
        if expected := case.get("expected_contains"):
            checks.append(str(expected) in response.answer)
        if forbidden := case.get("forbidden_contains"):
            checks.append(str(forbidden) not in response.answer)
        if expected_flag := case.get("expected_flag"):
            checks.append(str(expected_flag) in response.safety_flags)

        ok = all(checks)
        passed += int(ok)
        print(json.dumps({"id": case["id"], "passed": ok}, ensure_ascii=False))

    rate = passed / len(cases) if cases else 0
    summary = {"total": len(cases), "passed": passed, "pass_rate": rate}
    print(json.dumps(summary))
    if passed != len(cases):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
