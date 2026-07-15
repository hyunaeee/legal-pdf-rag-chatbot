from __future__ import annotations

from typing import Any

from app.models.base import GenerationRequest, GenerationResult


class VertexGeminiProvider:
    """Vertex AI Gemini provider using the Google Gen AI SDK.

    The dependency is imported lazily so the base API and tests remain
    credential-free. Application Default Credentials are used at runtime.
    """

    name = "vertex-gemini"

    def __init__(
        self,
        *,
        project: str,
        location: str,
        model: str,
        temperature: float = 0.1,
        max_output_tokens: int = 1024,
    ) -> None:
        if not project:
            raise ValueError("A Google Cloud project is required for Vertex AI.")

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError(
                "Install the AI dependencies with `pip install -e '.[ai]'`."
            ) from exc

        self._types = types
        self._client = genai.Client(
            vertexai=True,
            project=project,
            location=location,
            http_options=types.HttpOptions(api_version="v1"),
        )
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    @staticmethod
    def _usage_value(usage: Any, attribute: str) -> int | None:
        value = getattr(usage, attribute, None) if usage is not None else None
        return int(value) if value is not None else None

    def generate(self, request: GenerationRequest) -> GenerationResult:
        evidence = "\n\n".join(
            f"[Evidence {index}] {text}"
            for index, text in enumerate(request.evidence, start=1)
        )
        prompt = (
            "Answer the user using only the supplied evidence. "
            "If the evidence is insufficient, explicitly say so. "
            "Preserve policy dates, quantities, and exceptions exactly.\n\n"
            f"User question:\n{request.query}\n\n"
            f"Evidence:\n{evidence}"
        )
        response = self._client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=self._types.GenerateContentConfig(
                system_instruction=request.system_instruction,
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
            ),
        )

        text = response.text or ""
        usage = getattr(response, "usage_metadata", None)
        candidates = getattr(response, "candidates", None) or []
        finish_reason = None
        if candidates:
            reason = getattr(candidates[0], "finish_reason", None)
            finish_reason = str(reason) if reason is not None else None

        return GenerationResult(
            text=text,
            model=self.model,
            input_tokens=self._usage_value(usage, "prompt_token_count"),
            output_tokens=self._usage_value(usage, "candidates_token_count"),
            finish_reason=finish_reason,
        )
