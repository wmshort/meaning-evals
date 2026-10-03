from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import BaseModel, ValidationError

from meaning_evals.schema import (
    OGL_ATTRIBUTION,
    GoldLabel,
    Item,
    ItemKind,
    JudgeResult,
    Mechanism,
    Passage,
    Question,
    quote_found,
)

from .builders import (
    FAITHFUL_ANSWER,
    make_gold,
    make_item,
    make_passage,
    make_question,
    make_result,
)


def _round_trip(record: BaseModel) -> None:
    first = record.model_dump_json()
    parsed = type(record).model_validate_json(first)
    second = parsed.model_dump_json()
    assert second == first
    assert parsed == record


@pytest.mark.parametrize(
    "record",
    [
        make_passage(),
        make_question(),
        make_item("p01-a", ItemKind.FAITHFUL),
        make_item("p01-b", ItemKind.DIVERGENT, intended=Mechanism.SCOPE_SHIFT),
        make_item("p01-c", ItemKind.NEAR_MISS, paired="p01-b"),
        make_gold("p01-b", True, Mechanism.SCOPE_SHIFT, "You must register"),
        make_gold("p01-a", False),
        make_result("p01-b", "claude", 1, True, Mechanism.SCOPE_SHIFT, "You must register"),
        make_result("p01-a", "claude", 2, None),
    ],
    ids=lambda record: type(record).__name__,
)
def test_records_round_trip_through_json_unchanged(record: BaseModel) -> None:
    _round_trip(record)


def test_mechanisms_are_exactly_the_six_in_the_specification() -> None:
    assert [m.value for m in Mechanism] == [
        "deontic_reversal",
        "condition_omission",
        "temporal_condition_reversal",
        "scope_shift",
        "quantitative_divergence",
        "polarity_reversal",
    ]


def test_passage_carries_the_fixed_ogl_statement() -> None:
    assert make_passage().ogl_attribution == (
        "Contains public sector information licensed under the Open Government Licence v3.0."
    )
    assert make_passage().ogl_attribution == OGL_ATTRIBUTION


def test_passage_defaults_to_an_unbroken_excerpt_of_settled_guidance() -> None:
    passage = make_passage()
    assert passage.section_title == ""
    assert passage.elided is False
    assert passage.recent_change is False


def test_passage_records_its_section_an_elision_and_a_recent_change() -> None:
    data = {**make_passage().model_dump(), "section_title": "Eligibility"}
    passage = Passage.model_validate({**data, "elided": True, "recent_change": True})
    assert (passage.section_title, passage.elided, passage.recent_change) == (
        "Eligibility",
        True,
        True,
    )


def test_passage_rejects_a_different_attribution() -> None:
    data = make_passage().model_dump(mode="json")
    data["ogl_attribution"] = "Crown copyright"
    with pytest.raises(ValidationError):
        Passage.model_validate(data)


def test_passage_rejects_a_page_outside_gov_uk() -> None:
    data = make_passage().model_dump(mode="json")
    data["source_url"] = "https://example.com/guidance"
    with pytest.raises(ValidationError, match=r"www\.gov\.uk"):
        Passage.model_validate(data)


def test_passage_rejects_text_shorter_than_eighty_words() -> None:
    data = make_passage().model_dump(mode="json")
    data["text"] = "Too short to be a passage."
    with pytest.raises(ValidationError, match="80"):
        Passage.model_validate(data)


def test_question_requires_four_distinct_mechanisms() -> None:
    with pytest.raises(ValidationError, match="four distinct"):
        make_question(mechanisms=(Mechanism.SCOPE_SHIFT,) * 4)
    with pytest.raises(ValidationError, match="four distinct"):
        make_question(mechanisms=(Mechanism.SCOPE_SHIFT, Mechanism.POLARITY_REVERSAL))


def test_divergent_item_requires_its_intended_mechanism() -> None:
    with pytest.raises(ValidationError, match="intended_mechanism"):
        make_item("x", ItemKind.DIVERGENT)


def test_near_miss_item_requires_its_paired_item() -> None:
    with pytest.raises(ValidationError, match="paired_item"):
        make_item("x", ItemKind.NEAR_MISS)


def test_faithful_item_carries_no_mechanism_or_pair() -> None:
    with pytest.raises(ValidationError):
        make_item("x", ItemKind.FAITHFUL, intended=Mechanism.SCOPE_SHIFT)


def test_divergent_gold_label_requires_mechanism_span_and_rationale() -> None:
    with pytest.raises(ValidationError, match="mechanism"):
        make_gold("x", True, None, "You must register")
    with pytest.raises(ValidationError, match="quoted_span"):
        make_gold("x", True, Mechanism.SCOPE_SHIFT, None)
    data = make_gold("x", True, Mechanism.SCOPE_SHIFT, "You must").model_dump(mode="json")
    data["rationale"] = "  "
    with pytest.raises(ValidationError, match="rationale"):
        GoldLabel.model_validate(data)


def test_non_divergent_gold_label_carries_no_mechanism_or_span() -> None:
    with pytest.raises(ValidationError):
        make_gold("x", False, Mechanism.SCOPE_SHIFT)
    with pytest.raises(ValidationError):
        make_gold("x", False, None, "You must register")


def test_judge_result_rejects_a_naive_timestamp() -> None:
    data = make_result("x", "claude", 1, False).model_dump(mode="json")
    data["called_at"] = datetime(2026, 9, 25, 12, 0).isoformat()
    with pytest.raises(ValidationError):
        JudgeResult.model_validate(data)


def test_malformed_judge_result_has_an_error_and_no_verdict() -> None:
    result = make_result("x", "claude", 1, None)
    assert result.parse_error is not None
    assert result.diverges is None
    data = result.model_dump(mode="json")
    data["parse_error"] = None
    with pytest.raises(ValidationError, match="parse_error"):
        JudgeResult.model_validate(data)


def test_judge_result_saying_diverges_must_name_a_mechanism() -> None:
    with pytest.raises(ValidationError, match="mechanism"):
        make_result("x", "claude", 1, True, None, "You must register")


def test_item_requires_a_timezone_aware_generation_time() -> None:
    data = make_item("x", ItemKind.FAITHFUL).model_dump(mode="json")
    data["generated_at"] = "2026-09-25T12:00:00"
    with pytest.raises(ValidationError):
        Item.model_validate(data)


def test_quote_found_requires_a_verbatim_occurrence_in_the_answer() -> None:
    assert quote_found("register the boat", FAITHFUL_ANSWER) is True
    assert quote_found("  register the boat  ", FAITHFUL_ANSWER) is True
    assert quote_found("Register The Boat", FAITHFUL_ANSWER) is False
    assert quote_found("register your boat", FAITHFUL_ANSWER) is False
    assert quote_found(None, FAITHFUL_ANSWER) is None
    assert quote_found("   ", FAITHFUL_ANSWER) is None


def test_question_record_keeps_mechanism_order() -> None:
    question = make_question()
    assert Question.model_validate_json(question.model_dump_json()).mechanisms == (
        question.mechanisms
    )
