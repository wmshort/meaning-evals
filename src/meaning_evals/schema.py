"""The records the harness reads and writes, one JSON object per line under `data/`.

Every record is validated on the way in; a file that does not parse is rejected, never
coerced. Identifiers are distinct types so an item id cannot be passed where a passage id
is expected.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Final, Literal, NewType, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

PassageId = NewType("PassageId", str)
ItemId = NewType("ItemId", str)

OGL_ATTRIBUTION: Final = (
    "Contains public sector information licensed under the Open Government Licence v3.0."
)
GOV_UK_PREFIX = "https://www.gov.uk/"
PASSAGE_MIN_WORDS = 80
PASSAGE_MAX_WORDS = 250
MECHANISMS_PER_PASSAGE = 4


# Reasoning effort, as Anthropic's `output_config.effort` and OpenAI's `reasoning.effort`
# take it.
Effort = Literal["low", "medium", "high", "xhigh", "max"]


class Mechanism(StrEnum):
    """The six mechanisms of meaning-level divergence the repository measures."""

    DEONTIC_REVERSAL = "deontic_reversal"
    CONDITION_OMISSION = "condition_omission"
    TEMPORAL_CONDITION_REVERSAL = "temporal_condition_reversal"
    SCOPE_SHIFT = "scope_shift"
    QUANTITATIVE_DIVERGENCE = "quantitative_divergence"
    POLARITY_REVERSAL = "polarity_reversal"


class ItemKind(StrEnum):
    """What the generator was asked to produce; never shown to the labeller."""

    FAITHFUL = "faithful"
    DIVERGENT = "divergent"
    NEAR_MISS = "near_miss"


@dataclass(frozen=True)
class MechanismText:
    label: str
    definition: str


MECHANISM_TEXT: dict[Mechanism, MechanismText] = {
    Mechanism.DEONTIC_REVERSAL: MechanismText(
        "Deontic reversal",
        "an obligation and a permission are swapped: a may becomes a must, or the reverse.",
    ),
    Mechanism.CONDITION_OMISSION: MechanismText(
        "Condition omission",
        "a condition the guidance attaches is dropped, so something the guidance makes "
        "conditional is stated without its condition.",
    ),
    Mechanism.TEMPORAL_CONDITION_REVERSAL: MechanismText(
        "Temporal-condition reversal",
        "the when is changed: the timing or order the guidance sets (before, after, within, "
        "until) is altered.",
    ),
    Mechanism.SCOPE_SHIFT: MechanismText(
        "Scope shift",
        "who or what the guidance covers is changed: a some is widened to an all.",
    ),
    Mechanism.QUANTITATIVE_DIVERGENCE: MechanismText(
        "Quantitative divergence",
        "a number, limit, amount or deadline differs from the one the guidance gives.",
    ),
    Mechanism.POLARITY_REVERSAL: MechanismText(
        "Polarity reversal",
        "what the guidance denies is asserted, or what it asserts is denied.",
    ),
}


class Record(BaseModel):
    """Base for every persisted record: unknown fields are rejected, records are immutable."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class Passage(Record):
    """A GOV.UK guidance excerpt, copied verbatim.

    `elided` marks an excerpt with a part left out, the gap shown in `text` as "[…]".
    `recent_change` marks guidance whose rules changed recently enough that a judge may not
    have seen the change in training; false alarms on its items are reported apart.
    """

    id: PassageId = Field(min_length=1)
    source_url: str
    page_title: str = Field(min_length=1)
    section_title: str = ""
    retrieved_on: date
    text: str
    elided: bool = False
    recent_change: bool = False
    ogl_attribution: Literal[
        "Contains public sector information licensed under the Open Government Licence v3.0."
    ] = OGL_ATTRIBUTION

    @field_validator("source_url")
    @classmethod
    def _on_gov_uk(cls, value: str) -> str:
        if not value.startswith(GOV_UK_PREFIX):
            raise ValueError(f"source_url must be a page on {GOV_UK_PREFIX}")
        return value

    @field_validator("text")
    @classmethod
    def _length_in_words(cls, value: str) -> str:
        words = len(value.split())
        if not PASSAGE_MIN_WORDS <= words <= PASSAGE_MAX_WORDS:
            raise ValueError(
                f"text has {words} words; a passage must have "
                f"{PASSAGE_MIN_WORDS} to {PASSAGE_MAX_WORDS}"
            )
        return value


class Question(Record):
    """An approved user question, and the four mechanisms its divergent answers will use."""

    passage_id: PassageId = Field(min_length=1)
    question: str = Field(min_length=1)
    mechanisms: tuple[Mechanism, ...]

    @field_validator("mechanisms")
    @classmethod
    def _four_distinct(cls, value: tuple[Mechanism, ...]) -> tuple[Mechanism, ...]:
        if len(value) != MECHANISMS_PER_PASSAGE or len(set(value)) != MECHANISMS_PER_PASSAGE:
            raise ValueError("a question needs exactly four distinct mechanisms")
        return value


class Item(Record):
    """One answer to be labelled and judged, with the provenance of the call that wrote it.

    `kind`, `intended_mechanism` and `paired_item` record generation intent. They are kept
    out of the labelling worksheet and out of every judge prompt.
    """

    id: ItemId = Field(min_length=1)
    passage_id: PassageId = Field(min_length=1)
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    kind: ItemKind
    intended_mechanism: Mechanism | None = None
    paired_item: ItemId | None = None
    requested_model: str = Field(min_length=1)
    returned_model_id: str = Field(min_length=1)
    generated_at: AwareDatetime

    @model_validator(mode="after")
    def _intent_matches_kind(self) -> Self:
        if self.kind is ItemKind.DIVERGENT and self.intended_mechanism is None:
            raise ValueError("a divergent item needs its intended_mechanism")
        if self.kind is not ItemKind.DIVERGENT and self.intended_mechanism is not None:
            raise ValueError("only a divergent item carries an intended_mechanism")
        if (self.kind is ItemKind.NEAR_MISS) != (self.paired_item is not None):
            raise ValueError("a near-miss item, and only a near-miss item, has a paired_item")
        return self


class GoldLabel(Record):
    """The expert's blind label for one item."""

    item_id: ItemId = Field(min_length=1)
    diverges: bool
    mechanism: Mechanism | None
    quoted_span: str | None
    rationale: str = ""
    labelled_on: date

    @model_validator(mode="after")
    def _complete_for_its_verdict(self) -> Self:
        if self.diverges:
            if self.mechanism is None:
                raise ValueError("a divergent label needs a mechanism")
            if not (self.quoted_span or "").strip():
                raise ValueError("a divergent label needs a quoted_span")
            if not self.rationale.strip():
                raise ValueError("a divergent label needs a rationale")
        elif self.mechanism is not None or self.quoted_span is not None:
            raise ValueError("a non-divergent label has no mechanism and no quoted_span")
        return self


class JudgeResult(Record):
    """One judge call on one item. A malformed response is kept, with `parse_error` set."""

    item_id: ItemId = Field(min_length=1)
    judge: str = Field(min_length=1)
    run: int = Field(ge=1)
    requested_model: str = Field(min_length=1)
    returned_model_id: str = Field(min_length=1)
    temperature: float | None
    effort: Effort | None
    diverges: bool | None
    mechanism: Mechanism | None
    quoted_span: str | None
    quote_found: bool | None
    raw: str
    parse_error: str | None
    called_at: AwareDatetime

    @model_validator(mode="after")
    def _verdict_is_consistent(self) -> Self:
        if (self.parse_error is None) == (self.diverges is None):
            raise ValueError("exactly one of parse_error and diverges must be set")
        if self.diverges and self.mechanism is None:
            raise ValueError("a result that diverges must name a mechanism")
        if not self.diverges and (self.mechanism is not None or self.quoted_span is not None):
            raise ValueError("a result that does not diverge has no mechanism or quoted_span")
        if (self.diverges is True) != (self.quote_found is not None):
            raise ValueError("quote_found is set exactly when the result diverges")
        return self


def quote_found(span: str | None, answer: str) -> bool | None:
    """Whether `span`, trimmed of surrounding whitespace, occurs verbatim in `answer`.

    Returns None when there is no span to look for.
    """
    if span is None or not span.strip():
        return None
    return span.strip() in answer
