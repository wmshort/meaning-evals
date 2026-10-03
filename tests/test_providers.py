"""Provider adapters, each with its SDK client mocked at the boundary. No network."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import anthropic
import httpx2
import openai
import pytest
from anthropic.types import Message
from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types
from openai.types.responses import Response

from meaning_evals.errors import MissingKeyError, ProviderError
from meaning_evals.providers import (
    ClientSettings,
    Completion,
    CompletionRequest,
    ProviderName,
    read_keys,
)
from meaning_evals.providers.anthropic_provider import AnthropicProvider
from meaning_evals.providers.google_provider import GoogleProvider
from meaning_evals.providers.openai_provider import OpenAIProvider

SCHEMA: dict[str, object] = {"type": "object", "properties": {"answer": {"type": "string"}}}
REQUEST = CompletionRequest(
    model="requested-model",
    system="system text",
    prompt="prompt text",
    json_schema=SCHEMA,
    schema_name="verdict",
    max_output_tokens=512,
)
HOT_REQUEST = CompletionRequest(**{**REQUEST.__dict__, "temperature": 0.0})
EFFORT_REQUEST = CompletionRequest(**{**REQUEST.__dict__, "effort": "high"})
SETTINGS = ClientSettings(timeout_seconds=30.0, max_attempts=3)


# The environment-only key rule.


def test_read_keys_names_every_missing_variable_and_never_a_value() -> None:
    environ = {"OPENAI_API_KEY": "sk-test-secret-value", "ANTHROPIC_API_KEY": "   "}
    with pytest.raises(MissingKeyError) as raised:
        read_keys(["anthropic", "openai", "google"], environ)
    message = str(raised.value)
    assert "ANTHROPIC_API_KEY" in message
    assert "GEMINI_API_KEY" in message
    assert "OPENAI_API_KEY" not in message
    assert "sk-test-secret-value" not in message


@pytest.mark.parametrize(
    ("provider", "variable"),
    [
        ("anthropic", "ANTHROPIC_API_KEY"),
        ("openai", "OPENAI_API_KEY"),
        ("google", "GEMINI_API_KEY"),
    ],
)
def test_each_provider_fails_fast_without_its_key(provider: ProviderName, variable: str) -> None:
    with pytest.raises(MissingKeyError, match=variable):
        read_keys([provider], {"UNRELATED": "x"})


def test_read_keys_returns_only_the_keys_asked_for() -> None:
    environ = {"GEMINI_API_KEY": " g-key ", "OPENAI_API_KEY": "o-key"}
    assert read_keys(["google"], environ) == {"google": "g-key"}


# Anthropic.


def _claude_message(text: str, model: str = "claude-opus-5-20260901") -> Message:
    return Message.model_validate(
        {
            "id": "msg_1",
            "type": "message",
            "role": "assistant",
            "model": model,
            "content": [
                {"type": "thinking", "thinking": "", "signature": "sig"},
                {"type": "text", "text": text},
            ],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
    )


def _capture_constructor(monkeypatch: pytest.MonkeyPatch, owner: Any, name: str) -> dict[str, Any]:
    captured: dict[str, Any] = {}

    def fake(**kwargs: Any) -> MagicMock:
        captured.update(kwargs)
        return MagicMock()

    monkeypatch.setattr(owner, name, fake)
    return captured


def test_anthropic_client_gets_the_timeout_and_bounded_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_constructor(monkeypatch, anthropic, "Anthropic")
    AnthropicProvider.from_key("key-value", SETTINGS)
    assert captured == {"api_key": "key-value", "timeout": 30.0, "max_retries": 2}


def test_anthropic_returns_the_text_blocks_and_the_reported_model() -> None:
    client = MagicMock()
    client.messages.create.return_value = _claude_message('{"answer": "yes"}')
    completion = AnthropicProvider(client).complete_json(REQUEST)
    assert completion == Completion(
        text='{"answer": "yes"}', model_id="claude-opus-5-20260901", finish_reason="end_turn"
    )
    kwargs = client.messages.create.call_args.kwargs
    assert kwargs["model"] == "requested-model"
    assert kwargs["system"] == "system text"
    assert kwargs["messages"] == [{"role": "user", "content": "prompt text"}]
    assert kwargs["output_config"] == {"format": {"type": "json_schema", "schema": SCHEMA}}
    assert kwargs["extra_body"] is None
    assert "temperature" not in kwargs


def test_anthropic_sends_a_configured_temperature_in_the_request_body() -> None:
    client = MagicMock()
    client.messages.create.return_value = _claude_message("{}")
    AnthropicProvider(client).complete_json(HOT_REQUEST)
    assert client.messages.create.call_args.kwargs["extra_body"] == {"temperature": 0.0}


def test_anthropic_sends_a_configured_effort_beside_the_output_format() -> None:
    client = MagicMock()
    client.messages.create.return_value = _claude_message("{}")
    AnthropicProvider(client).complete_json(EFFORT_REQUEST)
    assert client.messages.create.call_args.kwargs["output_config"] == {
        "format": {"type": "json_schema", "schema": SCHEMA},
        "effort": "high",
    }


def test_anthropic_api_error_becomes_a_provider_error() -> None:
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    client = MagicMock()
    client.messages.create.side_effect = anthropic.BadRequestError(
        "temperature is not supported", response=httpx2.Response(400, request=request), body=None
    )
    with pytest.raises(ProviderError, match="BadRequestError"):
        AnthropicProvider(client).complete_json(REQUEST)


def _anthropic_through_transport(
    monkeypatch: pytest.MonkeyPatch, statuses: list[int], max_attempts: int
) -> tuple[AnthropicProvider, list[httpx2.Request]]:
    """A provider built by `from_key` whose HTTP layer replays `statuses`, then succeeds."""
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        if len(seen) <= len(statuses):
            return httpx2.Response(
                statuses[len(seen) - 1],
                headers={"retry-after-ms": "1"},
                json={"type": "error", "error": {"type": "overloaded_error", "message": "busy"}},
            )
        return httpx2.Response(200, json=_claude_message("{}").model_dump(mode="json"))

    real = anthropic.Anthropic
    transport = httpx2.Client(transport=httpx2.MockTransport(handler))
    monkeypatch.setattr(anthropic, "Anthropic", lambda **kw: real(**kw, http_client=transport))
    settings = ClientSettings(timeout_seconds=5.0, max_attempts=max_attempts)
    return AnthropicProvider.from_key("key-value", settings), seen


def test_anthropic_retries_a_transient_error_within_the_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider, seen = _anthropic_through_transport(monkeypatch, [529, 503], max_attempts=3)
    assert provider.complete_json(REQUEST).model_id == "claude-opus-5-20260901"
    assert len(seen) == 3


def test_anthropic_gives_up_when_the_attempts_are_spent(monkeypatch: pytest.MonkeyPatch) -> None:
    provider, seen = _anthropic_through_transport(monkeypatch, [529, 529, 529], max_attempts=2)
    with pytest.raises(ProviderError, match="OverloadedError"):
        provider.complete_json(REQUEST)
    assert len(seen) == 2


def test_anthropic_never_sends_the_key_anywhere_but_its_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider, seen = _anthropic_through_transport(monkeypatch, [], max_attempts=1)
    provider.complete_json(REQUEST)
    assert seen[0].headers["x-api-key"] == "key-value"
    assert "key-value" not in str(seen[0].url)
    assert b"key-value" not in seen[0].content


# OpenAI.


def _openai_response(
    text: str, status: str = "completed", incomplete: dict[str, str] | None = None
) -> Response:
    return Response.model_validate(
        {
            "id": "resp_1",
            "object": "response",
            "created_at": 0,
            "model": "gpt-6-astra-2026-08-01",
            "status": status,
            "incomplete_details": incomplete,
            "output": [
                {
                    "id": "msg_1",
                    "type": "message",
                    "role": "assistant",
                    "status": "completed",
                    "content": [{"type": "output_text", "text": text, "annotations": []}],
                }
            ],
            "parallel_tool_calls": False,
            "tool_choice": "auto",
            "tools": [],
        }
    )


def test_openai_client_gets_the_timeout_and_bounded_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_constructor(monkeypatch, openai, "OpenAI")
    OpenAIProvider.from_key("key-value", SETTINGS)
    assert captured == {"api_key": "key-value", "timeout": 30.0, "max_retries": 2}


def test_openai_returns_the_output_text_and_the_reported_model() -> None:
    client = MagicMock()
    client.responses.create.return_value = _openai_response('{"answer": "yes"}')
    completion = OpenAIProvider(client).complete_json(HOT_REQUEST)
    assert completion == Completion(
        text='{"answer": "yes"}', model_id="gpt-6-astra-2026-08-01", finish_reason="completed"
    )
    kwargs = client.responses.create.call_args.kwargs
    assert kwargs["instructions"] == "system text"
    assert kwargs["input"] == "prompt text"
    assert kwargs["temperature"] == 0.0
    assert kwargs["store"] is False
    assert kwargs["text"] == {
        "format": {"type": "json_schema", "name": "verdict", "schema": SCHEMA, "strict": True}
    }


def test_openai_omits_temperature_when_none_is_configured() -> None:
    client = MagicMock()
    client.responses.create.return_value = _openai_response("{}")
    OpenAIProvider(client).complete_json(REQUEST)
    assert client.responses.create.call_args.kwargs["temperature"] is openai.omit


def test_openai_sends_a_configured_reasoning_effort() -> None:
    client = MagicMock()
    client.responses.create.return_value = _openai_response("{}")
    OpenAIProvider(client).complete_json(EFFORT_REQUEST)
    assert client.responses.create.call_args.kwargs["reasoning"] == {"effort": "high"}


def test_openai_omits_reasoning_when_no_effort_is_configured() -> None:
    client = MagicMock()
    client.responses.create.return_value = _openai_response("{}")
    OpenAIProvider(client).complete_json(REQUEST)
    assert client.responses.create.call_args.kwargs["reasoning"] is openai.omit


def test_openai_reports_why_a_response_is_incomplete() -> None:
    client = MagicMock()
    client.responses.create.return_value = _openai_response(
        '{"answ', status="incomplete", incomplete={"reason": "max_output_tokens"}
    )
    completion = OpenAIProvider(client).complete_json(REQUEST)
    assert completion.finish_reason == "incomplete: max_output_tokens"
    assert completion.text == '{"answ'


def test_openai_api_error_becomes_a_provider_error() -> None:
    request = httpx2.Request("POST", "https://api.openai.com/v1/responses")
    client = MagicMock()
    client.responses.create.side_effect = openai.APIConnectionError(request=request)
    with pytest.raises(ProviderError, match="APIConnectionError"):
        OpenAIProvider(client).complete_json(REQUEST)


# Google.


def _gemini_response(text: str | None, model: str | None = "gemini-model-001") -> Any:
    return genai_types.GenerateContentResponse(
        candidates=[
            genai_types.Candidate(
                content=genai_types.Content(role="model", parts=[genai_types.Part(text=text)]),
                finish_reason=genai_types.FinishReason.STOP,
            )
        ],
        model_version=model,
    )


def test_google_client_gets_the_timeout_in_milliseconds_and_bounded_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_constructor(monkeypatch, genai, "Client")
    GoogleProvider.from_key("key-value", SETTINGS)
    assert captured["api_key"] == "key-value"
    assert captured["vertexai"] is False
    options = captured["http_options"]
    assert options.timeout == 30_000
    assert options.retry_options.attempts == 3


def test_google_returns_the_text_and_the_reported_model_version() -> None:
    client = MagicMock()
    client.models.generate_content.return_value = _gemini_response('{"answer": "yes"}')
    completion = GoogleProvider(client).complete_json(HOT_REQUEST)
    assert completion == Completion(
        text='{"answer": "yes"}', model_id="gemini-model-001", finish_reason="STOP"
    )
    kwargs = client.models.generate_content.call_args.kwargs
    assert kwargs["model"] == "requested-model"
    assert kwargs["contents"] == "prompt text"
    config = kwargs["config"]
    assert config.system_instruction == "system text"
    assert config.temperature == 0.0
    assert config.response_mime_type == "application/json"
    assert config.response_json_schema == SCHEMA


def test_google_requires_the_response_to_report_its_model() -> None:
    client = MagicMock()
    client.models.generate_content.return_value = _gemini_response("{}", model=None)
    with pytest.raises(ProviderError, match="model_version"):
        GoogleProvider(client).complete_json(REQUEST)


def test_google_api_error_becomes_a_provider_error() -> None:
    client = MagicMock()
    client.models.generate_content.side_effect = genai_errors.ServerError(
        503, {"error": {"code": 503, "message": "overloaded", "status": "UNAVAILABLE"}}
    )
    with pytest.raises(ProviderError, match="ServerError"):
        GoogleProvider(client).complete_json(REQUEST)
