from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass

from app.retrieval import InMemoryRetriever
from app.schemas import ChatResponse, Source


_INJECTION_PATTERNS = (
    r"ignore (all|any|the) previous instructions",
    r"system prompt",
    r"developer message",
    r"지시사항을 무시",
    r"시스템 프롬프트",
)


@dataclass
class AgentMetrics:
    requests: int = 0
    failures: int = 0
    total_latency_ms: float = 0
    retrieval_calls: int = 0

    def snapshot(self) -> dict[str, float | int]:
        average = self.total_latency_ms / self.requests if self.requests else 0.0
        return {
            "requests": self.requests,
            "failures": self.failures,
            "average_latency_ms": round(average, 2),
            "retrieval_calls": self.retrieval_calls,
        }


class PolicyAgent:
    """Deterministic orchestration with production-oriented extension points.

    The coordinator, retrieval, and reviewer stages are explicit so they can be
    replaced with Google ADK sub-agents without changing the HTTP contract.
    """

    def __init__(self, retriever: InMemoryRetriever, retrieval_k: int = 5) -> None:
        self.retriever = retriever
        self.retrieval_k = retrieval_k
        self.metrics = AgentMetrics()

    @staticmethod
    def _detect_injection(text: str) -> list[str]:
        lowered = text.lower()
        matched = any(re.search(pattern, lowered) for pattern in _INJECTION_PATTERNS)
        return ["prompt_injection"] if matched else []

    @staticmethod
    def _route(query: str) -> str:
        structured_terms = (
            "상태",
            "담당",
            "갱신일",
            "승인자",
            "status",
            "owner",
            "renewal",
        )
        if any(term in query.lower() for term in structured_terms):
            return "structured_data_then_retrieval"
        return "policy_retrieval"

    def answer(
        self,
        *,
        tenant_id: str,
        query: str,
        session_id: str | None,
    ) -> ChatResponse:
        started = time.perf_counter()
        self.metrics.requests += 1
        route = self._route(query)
        flags = self._detect_injection(query)
        active_session = session_id or str(uuid.uuid4())

        if flags:
            latency = (time.perf_counter() - started) * 1000
            self.metrics.total_latency_ms += latency
            return ChatResponse(
                answer=(
                    "보안 정책상 지시사항 우회 또는 시스템 정보 요청은 "
                    "처리할 수 없습니다."
                ),
                session_id=active_session,
                route="safety_review",
                safety_flags=flags,
                metrics={"latency_ms": round(latency, 2), "retrieval_count": 0},
            )

        try:
            self.metrics.retrieval_calls += 1
            matches = self.retriever.search(
                tenant_id=tenant_id,
                query=query,
                k=self.retrieval_k,
            )
            sources = [
                Source(
                    document_id=chunk.document_id,
                    title=chunk.title,
                    page=chunk.page,
                    excerpt=chunk.text[:280],
                    score=round(score, 4),
                )
                for chunk, score in matches
            ]
            if not sources:
                answer = (
                    "현재 접근 가능한 문서에서 근거를 찾지 못했습니다. "
                    "문서를 추가하거나 질문을 더 구체적으로 작성해 주세요."
                )
            else:
                evidence = " ".join(source.excerpt for source in sources[:3])
                answer = (
                    "접근 권한이 있는 문서에서 다음 근거를 확인했습니다. "
                    f"{evidence[:900]}"
                    "\n\n이 응답은 로컬 검증 모드의 추출형 답변입니다. "
                    "실제 배포에서는 Vertex AI 생성 모델과 평가 파이프라인을 연결합니다."
                )
            latency = (time.perf_counter() - started) * 1000
            self.metrics.total_latency_ms += latency
            return ChatResponse(
                answer=answer,
                session_id=active_session,
                route=route,
                sources=sources,
                safety_flags=flags,
                metrics={
                    "latency_ms": round(latency, 2),
                    "retrieval_count": len(sources),
                },
            )
        except Exception:
            self.metrics.failures += 1
            raise
