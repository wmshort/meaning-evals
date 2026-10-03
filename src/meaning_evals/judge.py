"""judge: every configured judge over every item, `runs` times, with a structured verdict.

A judge sees the passage, the question and the answer, and nothing about how the answer was
made. It returns JSON with `diverges`, `mechanism` (one of the six, or "none") and
`quoted_span`. A reply that does not meet that contract is recorded as malformed, with the
raw text kept; it is never dropped and never retried into shape.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, StrictBool, ValidationError, model_validator

from meaning_evals.config import JudgeSettings
from meaning_evals.errors import DataError
from meaning_evals.prompts import PromptSet, mechanism_catalogue, render
from meaning_evals.providers import Completion, CompletionRequest, Provider
from meaning_evals.schema import Item, JudgeResult, Mechanism, Passage, PassageId, quote_found

log = logging.getLogger(__name__)

NO_MECHANISM = "none"
VERDICT_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "diverges": {"type": "boolean"},
        "mechanism": {"type": "string", "enum": [*(m.value for m in Mechanism), NO_MECHANISM]},
        "quoted_span": {"type": "string"},
    },
    "required": ["diverges", "mechanism", "quoted_span"],
    "additionalProperties": False,
}


class _MalformedError(ValueError):
    """The reply does not meet the verdict contract."""


class _Verdict(BaseModel):
    model_config = ConfigDict(extra="forbid")
    diverges: StrictBool
    mechanism: Mechanism | Literal["none"]
    quoted_span: str

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.diverges and self.mechanism == NO_MECHANISM:
            raise ValueError("response says the answer diverges but names no mechanism")
        if not self.diverges and self.mechanism != NO_MECHANISM:
            raise ValueError("response names a mechanism but says the answer does not diverge")
        return self


@dataclass(frozen=True)
class Judge:
    settings: JudgeSettings
    provider: Provider


def _read_verdict(text: str) -> _Verdict:
    try:
        return _Verdict.model_validate_json(text)
    except ValidationError as exc:
        errors = exc.errors(include_url=False)
        if any(error["type"] == "json_invalid" for error in errors):
            raise _MalformedError("response is not valid JSON") from exc
        detail = "; ".join(
            f"{'.'.join(str(p) for p in error['loc']) or 'response'}: {error['msg']}"
            for error in errors
        )
        raise _MalformedError(f"response does not meet the verdict schema: {detail}") from exc


def _record(
    judge: Judge,
    item: Item,
    run: int,
    completion: Completion,
    called_at: datetime,
    verdict: _Verdict | None,
    error: str | None,
) -> JudgeResult:
    diverges = None if verdict is None else verdict.diverges
    divergent = verdict if verdict is not None and verdict.diverges else None
    span = (divergent.quoted_span.strip() or None) if divergent is not None else None
    return JudgeResult(
        item_id=item.id,
        judge=judge.settings.name,
        run=run,
        requested_model=judge.settings.model,
        returned_model_id=completion.model_id,
        temperature=judge.settings.temperature,
        effort=judge.settings.effort,
        diverges=diverges,
        mechanism=Mechanism(divergent.mechanism) if divergent is not None else None,
        quoted_span=span,
        quote_found=bool(quote_found(span, item.answer)) if diverges else None,
        raw=completion.text,
        parse_error=error,
        called_at=called_at,
    )


def judge_item(
    judge: Judge,
    item: Item,
    passage: Passage,
    prompts: PromptSet,
    run: int,
    now: Callable[[], datetime],
) -> JudgeResult:
    """One judge call on one item; only the passage, question and answer reach the prompt."""
    prompt = render(
        prompts.judge,
        mechanisms=mechanism_catalogue(),
        passage=passage.text,
        question=item.question,
        answer=item.answer,
    )
    request = CompletionRequest(
        model=judge.settings.model,
        system=render(prompts.judge_system),
        prompt=prompt,
        json_schema=VERDICT_SCHEMA,
        schema_name="verdict",
        max_output_tokens=judge.settings.max_output_tokens,
        temperature=judge.settings.temperature,
        effort=judge.settings.effort,
    )
    called_at = now()
    completion = judge.provider.complete_json(request)
    try:
        verdict = _read_verdict(completion.text)
    except _MalformedError as exc:
        reason = f"{exc} (finish_reason={completion.finish_reason})"
        return _record(judge, item, run, completion, called_at, None, reason)
    return _record(judge, item, run, completion, called_at, verdict, None)


def _check_recorded_models(judges: Sequence[Judge], existing: Iterable[JudgeResult]) -> None:
    configured = {judge.settings.name: judge.settings.model for judge in judges}
    for result in existing:
        model = configured.get(result.judge)
        if model is not None and result.requested_model != model:
            raise DataError(
                f"judge {result.judge} already has results requested from "
                f"{result.requested_model}, but the configuration now asks for {model}. "
                "Move the results file aside, or give the judge a new name."
            )


def run_judging(
    items: Sequence[Item],
    passages: Mapping[PassageId, Passage],
    judges: Sequence[Judge],
    runs: int,
    existing: Sequence[JudgeResult],
    prompts: PromptSet,
    now: Callable[[], datetime],
    sink: Callable[[JudgeResult], None],
) -> int:
    """Call each judge on each item for runs 1..`runs`, skipping calls already recorded.

    Each result goes to `sink` as soon as it exists. Returns the number of new calls.
    """
    _check_recorded_models(judges, existing)
    if absent := sorted({item.passage_id for item in items} - passages.keys()):
        raise DataError(f"items refer to passage(s) not in the passages file: {', '.join(absent)}")
    done = {(result.item_id, result.judge, result.run) for result in existing}
    calls = 0
    for judge in judges:
        for run in range(1, runs + 1):
            for item in sorted(items, key=lambda item: item.id):
                if (item.id, judge.settings.name, run) in done:
                    continue
                result = judge_item(judge, item, passages[item.passage_id], prompts, run, now)
                sink(result)
                calls += 1
                log.info(
                    "event=judge_call judge=%s run=%d item_id=%s returned_model=%s outcome=%s",
                    judge.settings.name,
                    run,
                    item.id,
                    result.returned_model_id,
                    "malformed" if result.parse_error else f"diverges={result.diverges}",
                )
    return calls
