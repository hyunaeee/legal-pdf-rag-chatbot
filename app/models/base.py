from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class GenerationRequest:
    query: str
    evidence: list[str]
    system_instruction: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationResult:
    text: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    finish_reason: str | None = None


class ModelProvider(Protocol):
    name: str

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate an answer grounded in the supplied evidence."""
        ...
