from __future__ import annotations

import json
from pathlib import Path

import pytest

from meaning_evals.build import Generator, build_items, replace_duplicate_twins
from meaning_evals.config import ModelSettings
from meaning_evals.errors import DataError, GenerationError
from meaning_evals.prompts import load_prompts
from meaning_evals.providers import CompletionRequest
from meaning_evals.schema import MECHANISM_TEXT, Item, ItemKind, Mechanism, PassageId

from .builders import (
    FAITHFUL_ANSWER,
    FIXED_NOW,
    FOUR_MECHANISMS,
    PASSAGE_TEXT,
    ScriptedProvider,
    divergent_answer,
    generation_reply,
    make_passage,
    make_question,
    twin_of,
)

PROMPTS = load_prompts(Path(__file__).resolve().parents[1] / "prompts")
SETTINGS = ModelSettings(provider="google", model="generator-model", temperature=0.7)


def _generator(provider: ScriptedProvider) -> Generator:
    return Generator(provider=provider, settings=SETTINGS, prompts=PROMPTS, now=lambda: FIXED_NOW)


def _build(
    provider: ScriptedProvider,
    passage_ids: tuple[str, ...] = ("p01",),
    existing: list[Item] | None = None,
    selected: set[PassageId] | None = None,
) -> tuple[list[Item], list[list[Item]]]:
    saved: list[list[Item]] = []
    items = build_items(
        passages=[make_passage(p) for p in passage_ids],
        questions=[make_question(p) for p in passage_ids],
        existing=existing or [],
        generator=_generator(provider),
        selected=selected,
        save=saved.append,
    )
    return items, saved


def test_build_writes_nine_items_per_passage_with_their_provenance() -> None:
    provider = ScriptedProvider(generation_reply)
    items, _ = _build(provider)
    assert len(provider.requests) == 9
    kinds = [item.kind for item in items]
    assert kinds.count(ItemKind.FAITHFUL) == 1
    assert kinds.count(ItemKind.DIVERGENT) == 4
    assert kinds.count(ItemKind.NEAR_MISS) == 4
    divergent = {i.intended_mechanism: i for i in items if i.kind is ItemKind.DIVERGENT}
    assert set(divergent) == set(FOUR_MECHANISMS)
    assert divergent[FOUR_MECHANISMS[1]].answer == divergent_answer(4)
    near = [i for i in items if i.kind is ItemKind.NEAR_MISS]
    assert {i.paired_item for i in near} == {i.id for i in divergent.values()}
    assert {i.answer for i in near} == {twin_of(m) for m in FOUR_MECHANISMS}
    assert all(i.requested_model == "generator-model" for i in items)
    assert all(i.returned_model_id == "returned-model-2026" for i in items)
    assert all(i.generated_at == FIXED_NOW for i in items)


def test_item_ids_are_unique_and_reveal_neither_kind_nor_mechanism() -> None:
    items, _ = _build(ScriptedProvider(generation_reply))
    ids = [item.id for item in items]
    assert len(set(ids)) == 9
    tells = [kind.value for kind in ItemKind] + [m.value for m in Mechanism] + ["near", "div"]
    assert not [i for i in ids for tell in tells if tell in i]


def test_generation_prompts_carry_the_passage_question_and_mechanism() -> None:
    provider = ScriptedProvider(generation_reply)
    _build(provider)
    faithful, divergent, near = provider.requests[0], provider.requests[1], provider.requests[2]
    assert PASSAGE_TEXT in faithful.prompt
    assert "register my boat" in faithful.prompt
    assert MECHANISM_TEXT[FOUR_MECHANISMS[0]].definition in divergent.prompt
    assert FAITHFUL_ANSWER in divergent.prompt
    assert divergent_answer(0) in near.prompt
    assert {r.temperature for r in provider.requests} == {0.7}
    assert {r.model for r in provider.requests} == {"generator-model"}


def test_a_generator_reply_that_is_not_the_requested_json_stops_the_build() -> None:
    with pytest.raises(GenerationError, match="p01"):
        _build(ScriptedProvider(lambda _: "Here is the answer you asked for."))


def test_a_divergent_answer_identical_to_the_faithful_answer_stops_the_build() -> None:
    same = json.dumps({"answer": FAITHFUL_ANSWER})
    with pytest.raises(GenerationError, match="identical"):
        _build(ScriptedProvider(lambda _: same))


def test_build_skips_passages_that_already_have_items_and_saves_after_each() -> None:
    first, _ = _build(ScriptedProvider(generation_reply), ("p01",))
    provider = ScriptedProvider(generation_reply)
    items, saved = _build(provider, ("p01", "p02"), existing=first)
    assert len(provider.requests) == 9
    assert [i for i in items if i.passage_id == "p01"] == first
    assert len(saved) == 1
    assert saved[0] == items


def test_rebuilding_a_selected_passage_replaces_only_its_items() -> None:
    both, _ = _build(ScriptedProvider(generation_reply), ("p01", "p02"))
    rebuilt_answer = FAITHFUL_ANSWER + " Apply early."

    def reply(request: CompletionRequest) -> str:
        text = json.loads(generation_reply(request))
        return json.dumps({"answer": text["answer"] + " Apply early."})

    items, saved = _build(
        ScriptedProvider(reply), ("p01", "p02"), existing=both, selected={PassageId("p01")}
    )
    assert [i for i in items if i.passage_id == "p02"] == [i for i in both if i.passage_id == "p02"]
    rebuilt = [i for i in items if i.passage_id == "p01"]
    assert len(rebuilt) == 9
    assert next(i for i in rebuilt if i.kind is ItemKind.FAITHFUL).answer == rebuilt_answer
    assert not {i.id for i in rebuilt} & {i.id for i in both}
    assert len(saved) == 1


def test_a_question_for_an_unknown_passage_is_a_data_error() -> None:
    with pytest.raises(DataError, match="p09"):
        build_items(
            passages=[make_passage("p01")],
            questions=[make_question("p09")],
            existing=[],
            generator=_generator(ScriptedProvider(generation_reply)),
            selected=None,
            save=lambda _: None,
        )


def test_selecting_a_passage_without_a_question_is_a_data_error() -> None:
    with pytest.raises(DataError, match="p02"):
        _build(ScriptedProvider(generation_reply), ("p01",), selected={PassageId("p02")})


def test_faithful_only_writes_just_the_faithful_answer_for_review() -> None:
    provider = ScriptedProvider(generation_reply)
    items = build_items(
        passages=[make_passage()],
        questions=[make_question()],
        existing=[],
        generator=_generator(provider),
        selected=None,
        save=lambda _: None,
        faithful_only=True,
    )
    assert [item.kind for item in items] == [ItemKind.FAITHFUL]
    assert len(provider.requests) == 1


def test_a_later_build_keeps_the_reviewed_faithful_answer_and_adds_the_other_eight() -> None:
    reviewed = build_items(
        passages=[make_passage()],
        questions=[make_question()],
        existing=[],
        generator=_generator(ScriptedProvider(generation_reply)),
        selected=None,
        save=lambda _: None,
        faithful_only=True,
    )
    provider = ScriptedProvider(generation_reply)
    items, _ = _build(provider, existing=reviewed)
    assert len(provider.requests) == 8
    assert len(items) == 9
    assert [i for i in items if i.kind is ItemKind.FAITHFUL] == reviewed
    assert all(FAITHFUL_ANSWER in r.prompt for r in provider.requests)


def test_regenerating_a_rejected_faithful_answer_drops_nothing_else() -> None:
    reviewed, _ = _build(ScriptedProvider(generation_reply), ("p01", "p02"))
    provider = ScriptedProvider(generation_reply)
    items = build_items(
        passages=[make_passage("p01"), make_passage("p02")],
        questions=[make_question("p01"), make_question("p02")],
        existing=[i for i in reviewed if i.kind is ItemKind.FAITHFUL],
        generator=_generator(provider),
        selected={PassageId("p01")},
        save=lambda _: None,
        faithful_only=True,
    )
    assert len(provider.requests) == 1
    assert sorted(i.passage_id for i in items) == ["p01", "p02"]


# Near-miss twins must differ from every other answer of their passage.


def _twin_prompts(provider: ScriptedProvider) -> list[str]:
    return [r.prompt for r in provider.requests if "<altered_answer>" in r.prompt]


def _in_use(prompt: str) -> str:
    return prompt.split("<rewordings_in_use>")[1].split("</rewordings_in_use>")[0]


def test_each_twin_prompt_lists_the_rewordings_already_in_use() -> None:
    provider = ScriptedProvider(generation_reply)
    _build(provider)
    prompts = _twin_prompts(provider)
    assert "None yet." in _in_use(prompts[0])
    earlier = [twin_of(m) for m in FOUR_MECHANISMS[:3]]
    assert all(answer in _in_use(prompts[3]) for answer in earlier)
    assert FAITHFUL_ANSWER not in _in_use(prompts[3])


def test_a_twin_identical_to_an_earlier_twin_stops_the_build() -> None:
    def reply(request: CompletionRequest) -> str:
        if "<altered_answer>" in request.prompt:
            return json.dumps({"answer": twin_of(FOUR_MECHANISMS[0])})
        return generation_reply(request)

    with pytest.raises(GenerationError, match="identical"):
        _build(ScriptedProvider(reply))


def _with_duplicate_twin() -> list[Item]:
    """A built passage whose second twin repeats the first twin's answer."""
    items, _ = _build(ScriptedProvider(generation_reply))
    twins = twins_in_question_order(items)
    copy = twins[1].model_copy(update={"answer": twins[0].answer})
    return [copy if i.id == twins[1].id else i for i in items]


def twins_in_question_order(items: list[Item]) -> list[Item]:
    """Near-miss twins ordered by their mechanism's place in the passage's question."""
    order = {twin_of(m): n for n, m in enumerate(FOUR_MECHANISMS)}
    return sorted((i for i in items if i.kind is ItemKind.NEAR_MISS), key=lambda i: order[i.answer])


def _replace(items: list[Item], provider: ScriptedProvider) -> tuple[list[Item], list[list[Item]]]:
    saved: list[list[Item]] = []
    result = replace_duplicate_twins(
        passages=[make_passage()],
        questions=[make_question()],
        existing=items,
        generator=_generator(provider),
        save=saved.append,
    )
    return result, saved


def test_replacing_duplicate_twins_regenerates_only_the_repeat() -> None:
    before = _with_duplicate_twin()
    fresh = FAITHFUL_ANSWER.replace("You must", "You are legally required to")
    provider = ScriptedProvider(lambda _: json.dumps({"answer": fresh}))
    after, saved = _replace(before, provider)
    assert len(provider.requests) == 1
    assert len(after) == 9
    gone = {i.id for i in before} - {i.id for i in after}
    added = [i for i in after if i.id not in {b.id for b in before}]
    assert len(gone) == 1 and len(added) == 1
    replaced = next(i for i in before if i.id in gone)
    assert added[0].answer == fresh
    assert added[0].kind is ItemKind.NEAR_MISS
    assert added[0].paired_item == replaced.paired_item
    assert len({i.answer for i in after}) == 9
    in_use = _in_use(provider.requests[0].prompt)
    assert twin_of(FOUR_MECHANISMS[0]) in in_use
    assert saved == [after]


def test_replacing_refuses_a_reply_that_repeats_an_answer_in_use() -> None:
    before = _with_duplicate_twin()
    provider = ScriptedProvider(lambda _: json.dumps({"answer": twin_of(FOUR_MECHANISMS[0])}))
    saved: list[list[Item]] = []
    with pytest.raises(GenerationError, match="identical"):
        replace_duplicate_twins(
            passages=[make_passage()],
            questions=[make_question()],
            existing=before,
            generator=_generator(provider),
            save=saved.append,
        )
    assert saved == []


def test_replacing_with_no_duplicates_makes_no_call() -> None:
    items, _ = _build(ScriptedProvider(generation_reply))
    provider = ScriptedProvider(generation_reply)
    after, saved = _replace(items, provider)
    assert provider.requests == []
    assert after == items
    assert saved == []
