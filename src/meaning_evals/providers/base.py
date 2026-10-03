"""The interface every provider adapter implements, and the environment-only key rule."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Literal, Protocol

from meaning_evals.errors import MissingKeyError
from meaning_evals.schema import Effort

ProviderName = Literal["anthropic", "openai", "google"]

KEY_VARIABLES: dict[ProviderName, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GEMINI_API_KEY",
}


@dataclass(frozen=True)
class ClientSettings:
    """Per-request timeout and the total number of attempts, including the first."""

    timeout_seconds: float
    max_attempts: int


@dataclass(frozen=True)
class CompletionRequest:
    """One call that must return a JSON object matching `json_schema`."""

    model: str
    system: str
    prompt: str
    json_schema: Mapping[str, object]
    schema_name: str
    max_output_tokens: int
    temperature: float | None = None
    effort: Effort | None = None


@dataclass(frozen=True)
class Completion:
    """The response text and the model id the response itself reports."""

    text: str
    model_id: str
    finish_reason: str | None


class Provider(Protocol):
    def complete_json(self, request: CompletionRequest) -> Completion:
        """Send `request`; raise `ProviderError` once the bounded retries are spent."""
        ...


def read_keys(
    providers: Iterable[ProviderName], environ: Mapping[str, str]
) -> dict[ProviderName, str]:
    """Return the key for each provider, or fail naming every variable that is missing.

    Keys come from the environment only. The error names variables, never values.
    """
    wanted = sorted(set(providers))
    missing = [KEY_VARIABLES[p] for p in wanted if not environ.get(KEY_VARIABLES[p], "").strip()]
    if missing:
        raise MissingKeyError(
            f"missing API key: {', '.join(missing)} is not set. Export it in the environment "
            "before running this command (see .env.example); keys are never read from files."
        )
    return {p: environ[KEY_VARIABLES[p]].strip() for p in wanted}
