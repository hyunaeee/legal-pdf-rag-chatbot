from __future__ import annotations

import json
from pathlib import Path

from app.agent import PolicyAgent
from app.retrieval import InMemoryRetriever


def main() -> None:
    cases_path = Path(__file__).with_name("cases.jsonl")
    cases = [json.loads(line) for line in cases_path.read_text(encoding="utf-8").splitlines() if line]
    passed = 0

    for case in cases:
        retriever = InMemoryRetriever()
        retriever.ingest(
            tenant_id=case["tenant_id"],
            title=f"{case['id']}.txt",
            text=case["document"],
        )
        if case.get("other_tenant_id"):
            retriever.ingest(
                tenant_id=case["other_tenant_id"],
                title="other-tenant.txt",
                text=case["other_document"],
            )
        response = PolicyAgent(retriever).answer(
            tenant_id=case["tenant_id"], query=case["query"], session_id=None
        )
        checks = []
        if expected := case.get("expected_contains"):
            checks.append(expected in response.answer)
        if forbidden := case.get("forbidden_contains"):
            checks.append(forbidden not in response.answer)
        if expected_flag := case.get("expected_flag"):
            checks.append(expected_flag in response.safety_flags)
        ok = all(checks)
        passed += int(ok)
        print(json.dumps({"id": case["id"], "passed": ok}, ensure_ascii=False))

    rate = passed / len(cases) if cases else 0
    print(json.dumps({"total": len(cases), "passed": passed, "pass_rate": rate}))
    if passed != len(cases):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
