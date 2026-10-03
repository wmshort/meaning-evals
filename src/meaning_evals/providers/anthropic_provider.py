"""Claude through the official Anthropic SDK."""

from __future__ import annotations

import anthropic
from anthropic.types import OutputConfigParam, TextBlock

from meaning_evals.errors import ProviderError

from .base import ClientSettings, Completion, CompletionRequest


class AnthropicProvider:
    """Structured JSON through `output_config.format`, with the SDK's bounded retries.

    Anthropic SDK 1.x has no `temperature` argument, and current Claude models (Opus 4.7
    onwards, Sonnet 5) reject sampling parameters with a 400 error. A configured temperature
    is therefore sent in `extra_body`, which only older models accept; leave it unset for
    current models. A configured effort goes in `output_config` beside the format.
    """

    def __init__(self, client: anthropic.Anthropic) -> None:
        self._client = client

    @classmethod
    def from_key(cls, api_key: str, settings: ClientSettings) -> AnthropicProvider:
        # The SDK retries connection errors, 408, 409, 429 and 5xx with exponential backoff.
        client = anthropic.Anthropic(
            api_key=api_key,
            timeout=settings.timeout_seconds,
            max_retries=settings.max_attempts - 1,
        )
        return cls(client)

    def complete_json(self, request: CompletionRequest) -> Completion:
        extra_body = None if request.temperature is None else {"temperature": request.temperature}
        output_config: OutputConfigParam = {
            "format": {"type": "json_schema", "schema": dict(request.json_schema)}
        }
        if request.effort is not None:
            output_config["effort"] = request.effort
        try:
            message = self._client.messages.create(
                model=request.model,
                max_tokens=request.max_output_tokens,
                system=request.system,
                messages=[{"role": "user", "content": request.prompt}],
                output_config=output_config,
                extra_body=extra_body,
            )
        except anthropic.APIError as exc:
            raise ProviderError(
                f"anthropic call to {request.model} failed ({type(exc).__name__}): {exc}"
            ) from exc
        text = "".join(block.text for block in message.content if isinstance(block, TextBlock))
        return Completion(text=text, model_id=message.model, finish_reason=message.stop_reason)
