"""Gemini through Google's official Gen AI SDK (`google-genai`), on the Gemini Developer API."""

from __future__ import annotations

from google import genai
from google.genai import errors, types

from meaning_evals.errors import ProviderError

from .base import ClientSettings, Completion, CompletionRequest

MILLISECONDS_PER_SECOND = 1000


class GoogleProvider:
    """JSON-schema output through `response_json_schema`, with the SDK's bounded retries.

    The SDK retries nothing unless given retry options; with them it retries 408, 429 and
    5xx responses and transport timeouts, backing off exponentially with jitter.
    """

    def __init__(self, client: genai.Client) -> None:
        self._client = client

    @classmethod
    def from_key(cls, api_key: str, settings: ClientSettings) -> GoogleProvider:
        options = types.HttpOptions(
            timeout=round(settings.timeout_seconds * MILLISECONDS_PER_SECOND),
            retry_options=types.HttpRetryOptions(attempts=settings.max_attempts),
        )
        return cls(genai.Client(api_key=api_key, vertexai=False, http_options=options))

    def complete_json(self, request: CompletionRequest) -> Completion:
        config = types.GenerateContentConfig(
            system_instruction=request.system,
            temperature=request.temperature,
            max_output_tokens=request.max_output_tokens,
            response_mime_type="application/json",
            response_json_schema=dict(request.json_schema),
        )
        try:
            response = self._client.models.generate_content(
                model=request.model, contents=request.prompt, config=config
            )
        except errors.APIError as exc:
            raise ProviderError(
                f"google call to {request.model} failed ({type(exc).__name__}): {exc}"
            ) from exc
        if not response.model_version:
            raise ProviderError(
                f"google call to {request.model} returned no model_version, so the result "
                "could not be reported under the model that produced it"
            )
        return Completion(
            text=response.text or "",
            model_id=response.model_version,
            finish_reason=_finish_reason(response),
        )


def _finish_reason(response: types.GenerateContentResponse) -> str | None:
    if not response.candidates or response.candidates[0].finish_reason is None:
        return None
    return str(response.candidates[0].finish_reason.value)
