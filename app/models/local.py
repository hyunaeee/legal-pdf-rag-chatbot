from __future__ import annotations

from app.models.base import GenerationRequest, GenerationResult


class LocalExtractiveProvider:
    """Credential-free provider used for tests and local demonstrations."""

    name = "local-extractive"

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not request.evidence:
            return GenerationResult(
                text=(
                    "현재 접근 가능한 문서에서 근거를 찾지 못했습니다. "
                    "문서를 추가하거나 질문을 더 구체적으로 작성해 주세요."
                ),
                model=self.name,
            )

        evidence = " ".join(request.evidence[:3])
        return GenerationResult(
            text=(
                "접근 권한이 있는 문서에서 다음 근거를 확인했습니다. "
                f"{evidence[:900]}"
                "\n\n이 응답은 로컬 검증 모드의 추출형 답변입니다."
            ),
            model=self.name,
        )
