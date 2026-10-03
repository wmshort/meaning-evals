from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from meaning_evals.config import JudgeSettings
from meaning_evals.errors import DataError
from meaning_evals.judge import Judge, judge_item, run_judging
from meaning_evals.prompts import load_prompts
from meaning_evals.providers import CompletionRequest, Provider
from meaning_evals.providers.anthropic_provider import AnthropicProvider
from meaning_evals.providers.google_provider import GoogleProvider
from meaning_evals.providers.openai_provider import OpenAIProvider
from meaning_evals.schema import ItemKind, JudgeResult, Mechanism

from .builders import (
    FAITHFUL_ANSWER,
    FIXED_NOW,
    PASSAGE_TEXT,
    ScriptedProvider,
    make_item,
    make_passage,
    make_result,
)
from .test_providers import _claude_message, _gemini_response, _openai_response

PROMPTS = load_prompts(Path(__file__).resolve().parents[1] / "prompts")
CLAUDE = JudgeSettings(name="claude", provider="anthropic", model="claude-model", temperature=None)
ITEM = make_item("p01-a", ItemKind.FAITHFUL)
PASSAGES = {make_passage().id: make_passage()}


def _verdict(diverges: bool, mechanism: str = "none", span: str = "") -> str:
    return json.dumps({"diverges": diverges, "mechanism": mechanism, "quoted_span": span})


def _judge_once(
    text: str, provider: Provider | None = None, finish: str = "end_turn"
) -> JudgeResult:
    judge = Judge(CLAUDE, provider or ScriptedProvider(lambda _: text, finish_reason=finish))
    return judge_item(judge, ITEM, make_passage(), PROMPTS, run=1, now=lambda: FIXED_NOW)


def test_a_divergence_verdict_is_recorded_with_its_provenance() -> None:
    result = _judge_once(_verdict(True, "scope_shift", "You must register the boat"))
    assert result.diverges is True
    assert result.mechanism is Mechanism.SCOPE_SHIFT
    assert result.quoted_span == "You must register the boat"
    assert result.quote_found is True
    assert result.requested_model == "claude-model"
    assert result.returned_model_id == "returned-model-2026"
    assert result.temperature is None
    assert result.called_at == FIXED_NOW
    assert result.parse_error is None


def test_the_configured_effort_is_sent_and_recorded() -> None:
    provider = ScriptedProvider(lambda _: _verdict(False))
    judge = Judge(CLAUDE.model_copy(update={"effort": "high"}), provider)
    result = judge_item(judge, ITEM, make_passage(), PROMPTS, run=1, now=lambda: FIXED_NOW)
    assert [request.effort for request in provider.requests] == ["high"]
    assert result.effort == "high"


def test_a_span_the_answer_does_not_contain_is_recorded_as_not_found() -> None:
    result = _judge_once(_verdict(True, "scope_shift", "all boats must register"))
    assert result.quote_found is False


def test_a_divergence_without_a_span_counts_as_quote_not_found() -> None:
    result = _judge_once(_verdict(True, "polarity_reversal", ""))
    assert result.quoted_span is None
    assert result.quote_found is False


def test_a_no_divergence_verdict_has_no_mechanism_span_or_quote_check() -> None:
    result = _judge_once(_verdict(False))
    assert (result.diverges, result.mechanism, result.quoted_span, result.quote_found) == (
        False,
        None,
        None,
        None,
    )


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("The answer diverges.", "not valid JSON"),
        ('{"diverges": true, "mechanism": "tone_shift", "quoted_span": "x"}', "mechanism"),
        ('{"diverges": true, "mechanism": "scope_shift"}', "quoted_span"),
        (_verdict(True, "none", "x"), "names no mechanism"),
        (_verdict(False, "scope_shift"), "does not diverge"),
    ],
)
def test_a_malformed_response_is_recorded_not_dropped(text: str, reason: str) -> None:
    result = _judge_once(text)
    assert result.diverges is None
    assert result.raw == text
    assert result.parse_error is not None
    assert reason in result.parse_error


def test_an_empty_response_records_why_the_model_stopped() -> None:
    result = _judge_once("", finish="refusal")
    assert result.parse_error is not None
    assert "refusal" in result.parse_error


def test_the_judge_prompt_depends_only_on_passage_question_and_answer() -> None:
    prompts: list[str] = []

    def reply(request: CompletionRequest) -> str:
        prompts.append(request.prompt)
        return _verdict(False)

    judge = Judge(CLAUDE, ScriptedProvider(reply))
    twin = make_item("p01-z", ItemKind.NEAR_MISS, paired="p01-y")
    divergent = make_item("p01-y", ItemKind.DIVERGENT, intended=Mechanism.SCOPE_SHIFT)
    for item in (ITEM, twin, divergent):
        judge_item(judge, item, make_passage(), PROMPTS, run=1, now=lambda: FIXED_NOW)
    assert prompts[0] == prompts[1] == prompts[2]
    assert PASSAGE_TEXT in prompts[0]
    assert FAITHFUL_ANSWER in prompts[0]
    assert "p01-y" not in prompts[0]


def _mocked_adapter(provider: str, text: str) -> Provider:
    client = MagicMock()
    if provider == "anthropic":
        client.messages.create.return_value = _claude_message(text)
        return AnthropicProvider(client)
    if provider == "openai":
        client.responses.create.return_value = _openai_response(text)
        return OpenAIProvider(client)
    client.models.generate_content.return_value = _gemini_response(text)
    return GoogleProvider(client)


@pytest.mark.parametrize("provider", ["anthropic", "openai", "google"])
def test_each_adapter_passes_a_malformed_json_reply_through_to_the_record(provider: str) -> None:
    result = _judge_once('{"diverges": tru', provider=_mocked_adapter(provider, '{"diverges": tru'))
    assert result.diverges is None
    assert result.raw == '{"diverges": tru'
    assert result.parse_error is not None and "not valid JSON" in result.parse_error


@pytest.mark.parametrize("provider", ["anthropic", "openai", "google"])
def test_each_adapter_records_the_model_its_response_reports(provider: str) -> None:
    result = _judge_once(_verdict(False), provider=_mocked_adapter(provider, _verdict(False)))
    assert result.diverges is False
    assert result.returned_model_id not in ("", "claude-model")


def _run(existing: list[JudgeResult], provider: ScriptedProvider) -> list[JudgeResult]:
    items = [make_item("p01-a", ItemKind.FAITHFUL), make_item("p01-b", ItemKind.FAITHFUL)]
    written: list[JudgeResult] = []
    run_judging(
        items=items,
        passages=PASSAGES,
        judges=[Judge(CLAUDE, provider)],
        runs=2,
        existing=existing,
        prompts=PROMPTS,
        now=lambda: FIXED_NOW,
        sink=written.append,
    )
    return written


def test_every_judge_runs_twice_over_every_item() -> None:
    written = _run([], ScriptedProvider(lambda _: _verdict(False)))
    assert sorted((r.item_id, r.run) for r in written) == [
        ("p01-a", 1),
        ("p01-a", 2),
        ("p01-b", 1),
        ("p01-b", 2),
    ]


def test_judging_resumes_without_repeating_recorded_calls() -> None:
    done = make_result("p01-a", "claude", 1, False)
    assert done.requested_model == CLAUDE.model
    provider = ScriptedProvider(lambda _: _verdict(False))
    written = _run([done], provider)
    assert len(provider.requests) == 3
    assert ("p01-a", 1) not in {(r.item_id, r.run) for r in written}


def test_results_recorded_under_another_model_stop_the_run() -> None:
    stale = make_result("p01-a", "claude", 1, False).model_copy(
        update={"requested_model": "an-older-model"}
    )
    with pytest.raises(DataError, match="claude-model"):
        _run([stale], ScriptedProvider(lambda _: _verdict(False)))


def test_an_item_whose_passage_is_missing_is_a_data_error() -> None:
    with pytest.raises(DataError, match="p07"):
        run_judging(
            items=[make_item("p07-a", ItemKind.FAITHFUL, passage_id="p07")],
            passages=PASSAGES,
            judges=[Judge(CLAUDE, ScriptedProvider(lambda _: _verdict(False)))],
            runs=1,
            existing=[],
            prompts=PROMPTS,
            now=lambda: FIXED_NOW,
            sink=lambda _: None,
        )
