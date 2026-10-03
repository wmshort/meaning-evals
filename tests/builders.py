"""Shared builders for small, self-contained fixtures. No test touches the network."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from meaning_evals.providers import Completion, CompletionRequest
from meaning_evals.schema import (
    MECHANISM_TEXT,
    GoldLabel,
    Item,
    ItemId,
    ItemKind,
    JudgeResult,
    Mechanism,
    Passage,
    PassageId,
    Question,
    quote_found,
)

FIXED_NOW = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)

# Invented for tests; it is not GOV.UK guidance and is never published as an item.
PASSAGE_TEXT = (
    "This is invented guidance used only by the test suite. You must register your boat "
    "with the harbour office before you use it on the river. Registration costs 40 pounds "
    "and lasts for 12 months. You may apply online or by post. If you use the boat only on "
    "private lakes, you do not need to register it. You must display the registration "
    "number on both sides of the boat within 14 days of receiving it. Boats longer than "
    "10 metres also need a safety certificate, which you must renew every 4 years. Some "
    "owners qualify for a discount if they belong to a recognised club."
)

FAITHFUL_ANSWER = (
    "You must register the boat with the harbour office before using it on the river. "
    "Registration costs 40 pounds and lasts 12 months."
)

FOUR_MECHANISMS = (
    Mechanism.DEONTIC_REVERSAL,
    Mechanism.QUANTITATIVE_DIVERGENCE,
    Mechanism.SCOPE_SHIFT,
    Mechanism.CONDITION_OMISSION,
)


def make_passage(passage_id: str = "p01") -> Passage:
    return Passage(
        id=PassageId(passage_id),
        source_url=f"https://www.gov.uk/test-fixture-{passage_id}",
        page_title="Invented fixture page",
        retrieved_on=date(2026, 9, 25),
        text=PASSAGE_TEXT,
    )


def make_question(
    passage_id: str = "p01", mechanisms: tuple[Mechanism, ...] = FOUR_MECHANISMS
) -> Question:
    return Question(
        passage_id=PassageId(passage_id),
        question="Do I need to register my boat before using it on the river?",
        mechanisms=mechanisms,
    )


def make_item(
    item_id: str,
    kind: ItemKind,
    *,
    passage_id: str = "p01",
    intended: Mechanism | None = None,
    paired: str | None = None,
    answer: str = FAITHFUL_ANSWER,
) -> Item:
    return Item(
        id=ItemId(item_id),
        passage_id=PassageId(passage_id),
        question="Do I need to register my boat before using it on the river?",
        answer=answer,
        kind=kind,
        intended_mechanism=intended,
        paired_item=ItemId(paired) if paired else None,
        requested_model="generator-model",
        returned_model_id="generator-model-2026-09-01",
        generated_at=FIXED_NOW,
    )


def make_gold(
    item_id: str,
    diverges: bool,
    mechanism: Mechanism | None = None,
    span: str | None = None,
) -> GoldLabel:
    return GoldLabel(
        item_id=ItemId(item_id),
        diverges=diverges,
        mechanism=mechanism,
        quoted_span=span,
        rationale="Stated for the test." if diverges else "",
        labelled_on=date(2026, 9, 26),
    )


def make_result(
    item_id: str,
    judge: str,
    run: int,
    diverges: bool | None,
    mechanism: Mechanism | None = None,
    span: str | None = None,
    answer: str = FAITHFUL_ANSWER,
) -> JudgeResult:
    return JudgeResult(
        item_id=ItemId(item_id),
        judge=judge,
        run=run,
        requested_model=f"{judge}-model",
        returned_model_id=f"{judge}-model-2026",
        temperature=0.0,
        effort=None,
        diverges=diverges,
        mechanism=mechanism,
        quoted_span=span,
        quote_found=quote_found(span, answer),
        raw="{}",
        parse_error=None if diverges is not None else "response is not valid JSON",
        called_at=FIXED_NOW,
    )


@dataclass
class ScriptedProvider:
    """A provider double at the adapter interface; `respond` writes each reply's text."""

    respond: Callable[[CompletionRequest], str]
    model_id: str = "returned-model-2026"
    finish_reason: str | None = "stop"
    requests: list[CompletionRequest] = field(default_factory=list)

    def complete_json(self, request: CompletionRequest) -> Completion:
        self.requests.append(request)
        return Completion(
            text=self.respond(request), model_id=self.model_id, finish_reason=self.finish_reason
        )


# One meaning-preserving rewording per mechanism, in `MECHANISM_TEXT` order.
TWIN_OPENINGS = (
    "You are required to",
    "You have to",
    "You need to",
    "It is necessary that you",
    "You are obliged to",
    "You are bound to",
)
MECHANISM_POSITION = {mechanism: position for position, mechanism in enumerate(MECHANISM_TEXT)}


def near_miss_answer(position: int) -> str:
    """The twin of the divergent answer written for the mechanism at `position`."""
    return FAITHFUL_ANSWER.replace("You must", TWIN_OPENINGS[position])


def twin_of(mechanism: Mechanism) -> str:
    return near_miss_answer(MECHANISM_POSITION[mechanism])


def divergent_answer(position: int) -> str:
    """A distinct divergent answer per mechanism position, free of mechanism names."""
    return FAITHFUL_ANSWER.replace("40 pounds", f"{50 + 10 * position} pounds")


def generation_reply(request: CompletionRequest) -> str:
    return generation_answer(request.prompt)


def generation_answer(prompt: str) -> str:
    """Answers the build prompts: faithful, then divergent by mechanism, then near-miss."""
    if "<altered_answer>" in prompt:
        answer = near_miss_answer(
            next(
                i
                for i in range(len(TWIN_OPENINGS))
                if divergent_answer(i) in prompt.split("<altered_answer>")[1]
            )
        )
    elif "<faithful_answer>" in prompt:
        labels = [text.label for text in MECHANISM_TEXT.values()]
        answer = divergent_answer(next(i for i, label in enumerate(labels) if label in prompt))
    else:
        answer = FAITHFUL_ANSWER
    return json.dumps({"answer": answer})
