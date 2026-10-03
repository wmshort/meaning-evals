"""GPT through the official OpenAI SDK's Responses API."""

from __future__ import annotations

import openai
from openai.types.responses import Response

from meaning_evals.errors import ProviderError

from .base import ClientSettings, Completion, CompletionRequest


class OpenAIProvider:
    """Strict JSON-schema output, not stored on OpenAI's side, with bounded SDK retries."""

    def __init__(self, client: openai.OpenAI) -> None:
        self._client = client

    @classmethod
    def from_key(cls, api_key: str, settings: ClientSettings) -> OpenAIProvider:
        # The SDK retries connection errors, 408, 409, 429 and 5xx with exponential backoff.
        client = openai.OpenAI(
            api_key=api_key,
            timeout=settings.timeout_seconds,
            max_retries=settings.max_attempts - 1,
        )
        return cls(client)

    def complete_json(self, request: CompletionRequest) -> Completion:
        try:
            response = self._client.responses.create(
                model=request.model,
                instructions=request.system,
                input=request.prompt,
                max_output_tokens=request.max_output_tokens,
                temperature=openai.omit if request.temperature is None else request.temperature,
                reasoning=openai.omit if request.effort is None else {"effort": request.effort},
                text={
                    "format": {
                        "type": "json_schema",
                        "name": request.schema_name,
                        "schema": dict(request.json_schema),
                        "strict": True,
                    }
                },
                store=False,
            )
        except openai.APIError as exc:
            raise ProviderError(
                f"openai call to {request.model} failed ({type(exc).__name__}): {exc}"
            ) from exc
        return Completion(
            text=response.output_text,
            model_id=response.model,
            finish_reason=_finish_reason(response),
        )


def _finish_reason(response: Response) -> str | None:
    if response.incomplete_details is not None and response.incomplete_details.reason:
        return f"{response.status}: {response.incomplete_details.reason}"
    return response.status
