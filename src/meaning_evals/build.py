"""build: nine items per approved passage, written by the generator model.

For each passage: the faithful answer; then, for each of the question's four mechanisms,
a divergent rewrite of the faithful answer and a near-miss twin that rewords the same place
without changing its meaning. Nine generation calls per passage. The faithful answers can
be written first, on their own, so they are checked before the other items are made.

No two items of a passage may share an answer: identical answers would show the labeller
which items are twins. Each twin's prompt lists the rewordings already in use, and a reply
that repeats any answer of its passage stops the build. `replace_duplicate_twins` repairs
items built before that rule, regenerating only the repeated twins.

Item ids are opaque: a digest of the passage, the slot and the answer. A rebuilt passage
therefore gets new ids, so gold labels and judge results for its old answers can never
attach to the new ones.
"""

from __future__ import annotations

import hashlib
import logging
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from meaning_evals.config import ModelSettings
from meaning_evals.errors import DataError, GenerationError
from meaning_evals.prompts import PromptSet, render
from meaning_evals.providers import CompletionRequest, Provider
from meaning_evals.schema import (
    MECHANISM_TEXT,
    Item,
    ItemId,
    ItemKind,
    Mechanism,
    Passage,
    PassageId,
    Question,
)

log = logging.getLogger(__name__)

ANSWER_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {"answer": {"type": "string"}},
    "required": ["answer"],
    "additionalProperties": False,
}


class _Answer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str = Field(min_length=1)


@dataclass(frozen=True)
class Generator:
    provider: Provider
    settings: ModelSettings
    prompts: PromptSet
    now: Callable[[], datetime]


@dataclass(frozen=True)
class _Slot:
    passage: Passage
    question: Question
    kind: ItemKind
    mechanism: Mechanism | None = None
    paired: ItemId | None = None


def item_id_for(passage_id: PassageId, slot: str, answer: str) -> ItemId:
    digest = hashlib.sha256(f"{passage_id}\x1f{slot}\x1f{answer}".encode()).hexdigest()
    return ItemId(f"{passage_id}-{digest[:10]}")


def _generate(generator: Generator, slot: _Slot, prompt: str) -> Item:
    settings = generator.settings
    request = CompletionRequest(
        model=settings.model,
        system=render(generator.prompts.generator_system),
        prompt=prompt,
        json_schema=ANSWER_SCHEMA,
        schema_name="answer",
        max_output_tokens=settings.max_output_tokens,
        temperature=settings.temperature,
        effort=settings.effort,
    )
    generated_at = generator.now()
    completion = generator.provider.complete_json(request)
    try:
        answer = _Answer.model_validate_json(completion.text).answer.strip()
    except ValidationError as exc:
        raise GenerationError(
            f"passage {slot.passage.id}: the {slot.kind} reply is not the requested JSON "
            f"(finish_reason={completion.finish_reason}): {completion.text[:200]!r}"
        ) from exc
    slot_name = slot.kind.value if slot.mechanism is None else f"{slot.kind}:{slot.mechanism}"
    return Item(
        id=item_id_for(slot.passage.id, slot_name, answer),
        passage_id=slot.passage.id,
        question=slot.question.question,
        answer=answer,
        kind=slot.kind,
        intended_mechanism=slot.mechanism if slot.kind is ItemKind.DIVERGENT else None,
        paired_item=slot.paired,
        requested_model=settings.model,
        returned_model_id=completion.model_id,
        generated_at=generated_at,
    )


NO_REWORDINGS_YET = "None yet."


def _require_change(item: Item, *others: Item) -> None:
    for other in others:
        if item.answer == other.answer:
            raise GenerationError(
                f"passage {item.passage_id}: the {item.kind} answer is identical to the "
                f"{other.kind} answer; rebuild the passage with --passage {item.passage_id}"
            )


def _rewordings_in_use(twins: Sequence[Item]) -> str:
    if not twins:
        return NO_REWORDINGS_YET
    return "\n\n".join(f"{n}. {twin.answer}" for n, twin in enumerate(twins, start=1))


def _twin(
    passage: Passage,
    question: Question,
    faithful: Item,
    divergent: Item,
    in_use: Sequence[Item],
    generator: Generator,
) -> Item:
    """The near-miss twin of `divergent`, told which rewordings `in_use` it must not repeat."""
    prompt = render(
        generator.prompts.near_miss,
        passage=passage.text,
        question=question.question,
        faithful_answer=faithful.answer,
        altered_answer=divergent.answer,
        rewordings_in_use=_rewordings_in_use(in_use),
    )
    slot = _Slot(passage, question, ItemKind.NEAR_MISS, divergent.intended_mechanism, divergent.id)
    return _generate(generator, slot, prompt)


def _faithful(passage: Passage, question: Question, generator: Generator) -> Item:
    prompt = render(generator.prompts.faithful, passage=passage.text, question=question.question)
    return _generate(generator, _Slot(passage, question, ItemKind.FAITHFUL), prompt)


def _variants(
    passage: Passage, question: Question, faithful: Item, generator: Generator
) -> list[Item]:
    """For each of the question's mechanisms, a divergent answer and its near-miss twin."""
    prompts = generator.prompts
    context = {"passage": passage.text, "question": question.question}
    items: list[Item] = []
    twins: list[Item] = []
    for mechanism in question.mechanisms:
        text = MECHANISM_TEXT[mechanism]
        divergent_prompt = render(
            prompts.divergent,
            **context,
            faithful_answer=faithful.answer,
            mechanism_label=text.label,
            mechanism_definition=text.definition,
        )
        slot = _Slot(passage, question, ItemKind.DIVERGENT, mechanism)
        divergent = _generate(generator, slot, divergent_prompt)
        _require_change(divergent, faithful, *items)
        twin = _twin(passage, question, faithful, divergent, twins, generator)
        _require_change(twin, faithful, *items, divergent)
        items += [divergent, twin]
        twins.append(twin)
    return items


def _reviewed_faithful(current: Sequence[Item]) -> Item | None:
    """A passage's faithful answer, when it was built alone for review and awaits the rest."""
    if len(current) == 1 and current[0].kind is ItemKind.FAITHFUL:
        return current[0]
    return None


def _targets(
    asked: Iterable[PassageId],
    current: Mapping[PassageId, Sequence[Item]],
    selected: set[PassageId] | None,
    faithful_only: bool,
) -> list[PassageId]:
    if selected is not None:
        return sorted(selected)
    return sorted(
        passage_id
        for passage_id in asked
        if not current.get(passage_id)
        or (not faithful_only and _reviewed_faithful(current[passage_id]) is not None)
    )


def _index_inputs(
    passages: Iterable[Passage], questions: Iterable[Question]
) -> tuple[dict[PassageId, Passage], dict[PassageId, Question]]:
    by_id: dict[PassageId, Passage] = {}
    for passage in passages:
        if passage.id in by_id:
            raise DataError(f"passage {passage.id} appears twice in the passages file")
        by_id[passage.id] = passage
    asked: dict[PassageId, Question] = {}
    for question in questions:
        if question.passage_id not in by_id:
            raise DataError(f"a question refers to passage {question.passage_id}, which is absent")
        if question.passage_id in asked:
            raise DataError(f"passage {question.passage_id} has more than one question")
        asked[question.passage_id] = question
    return by_id, asked


def build_items(
    passages: Iterable[Passage],
    questions: Iterable[Question],
    existing: list[Item],
    generator: Generator,
    selected: set[PassageId] | None,
    save: Callable[[list[Item]], None],
    faithful_only: bool = False,
) -> list[Item]:
    """Build `selected` passages, or every passage with a question and no complete item set.

    With `faithful_only`, only each passage's faithful answer is written, so it can be
    checked before any other item exists. A later build without it keeps that faithful
    answer and adds the eight others. A passage named in `selected` is built again from a
    new faithful answer. `save` receives the complete item list after each passage, so an
    interruption loses at most the passage in progress.
    """
    by_id, asked = _index_inputs(passages, questions)
    if selected is not None and (unknown := sorted(selected - asked.keys())):
        raise DataError(f"no approved question for passage(s) {', '.join(unknown)}")
    current: dict[PassageId, list[Item]] = defaultdict(list)
    for item in existing:
        current[item.passage_id].append(item)
    items = list(existing)
    for passage_id in _targets(asked, current, selected, faithful_only):
        passage, question = by_id[passage_id], asked[passage_id]
        reviewed = None if selected is not None else _reviewed_faithful(current[passage_id])
        faithful = reviewed or _faithful(passage, question, generator)
        fresh = [faithful]
        if not faithful_only:
            fresh += _variants(passage, question, faithful, generator)
        items = [item for item in items if item.passage_id != passage_id] + fresh
        items.sort(key=lambda item: (item.passage_id, item.id))
        log.info("event=build_passage passage_id=%s items=%d", passage_id, len(fresh))
        save(items)
    return items


def _repeated_twins(
    question: Question, items: Sequence[Item]
) -> tuple[Item, list[Item], list[Item]] | None:
    """The passage's faithful answer, its twins in question order, and the twins to replace.

    A twin is replaced when its answer repeats an answer that comes before it: the faithful
    answer, any divergent answer, or a twin earlier in the question's mechanism order.
    """
    faithful = next((i for i in items if i.kind is ItemKind.FAITHFUL), None)
    if faithful is None:
        return None
    divergents = {i.id: i for i in items if i.kind is ItemKind.DIVERGENT}
    order = {mechanism: n for n, mechanism in enumerate(question.mechanisms)}
    twins = [i for i in items if i.kind is ItemKind.NEAR_MISS]
    for twin in twins:
        if twin.paired_item not in divergents:
            raise DataError(f"twin {twin.id} is paired to {twin.paired_item}, which is absent")

    def position(twin: Item) -> int:
        mechanism = divergents[ItemId(str(twin.paired_item))].intended_mechanism
        return order.get(mechanism, len(order)) if mechanism else len(order)

    twins.sort(key=position)
    seen = {faithful.answer, *(d.answer for d in divergents.values())}
    repeated = []
    for twin in twins:
        if twin.answer in seen:
            repeated.append(twin)
        seen.add(twin.answer)
    return faithful, twins, repeated


def replace_duplicate_twins(
    passages: Iterable[Passage],
    questions: Iterable[Question],
    existing: list[Item],
    generator: Generator,
    save: Callable[[list[Item]], None],
) -> list[Item]:
    """Regenerate each near-miss twin whose answer repeats an earlier answer of its passage.

    Faithful and divergent answers, and every twin that is not a repeat, are kept as they
    are. A replacement is told every other twin of its passage, and one that still repeats
    an answer stops the run before anything is saved for that passage.
    """
    by_id, asked = _index_inputs(passages, questions)
    items = list(existing)
    for passage_id in sorted(asked):
        own = [i for i in items if i.passage_id == passage_id]
        found = _repeated_twins(asked[passage_id], own)
        if found is None or not found[2]:
            continue
        faithful, twins, repeated = found
        divergents = {i.id: i for i in own if i.kind is ItemKind.DIVERGENT}
        for old in repeated:
            others = [t for t in twins if t.id != old.id]
            divergent = divergents[ItemId(str(old.paired_item))]
            passage, question = by_id[passage_id], asked[passage_id]
            new = _twin(passage, question, faithful, divergent, others, generator)
            _require_change(new, faithful, *divergents.values(), *others)
            twins = [new if t.id == old.id else t for t in twins]
            items = [new if i.id == old.id else i for i in items]
            log.info(
                "event=twin_replaced passage_id=%s old_item_id=%s new_item_id=%s",
                passage_id,
                old.id,
                new.id,
            )
        items.sort(key=lambda item: (item.passage_id, item.id))
        save(items)
    return items
