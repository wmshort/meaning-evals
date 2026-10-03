from __future__ import annotations

import json
from datetime import date
from typing import Any

import pytest

from meaning_evals.errors import DataError
from meaning_evals.gold import import_gold
from meaning_evals.schema import ItemKind, Mechanism

from .builders import make_item

ITEMS = [
    make_item("p01-a", ItemKind.FAITHFUL),
    make_item("p01-b", ItemKind.DIVERGENT, intended=Mechanism.SCOPE_SHIFT),
]


def _label(item_id: str, diverges: bool, **overrides: Any) -> dict[str, Any]:
    label: dict[str, Any] = {
        "item_id": item_id,
        "diverges": diverges,
        "mechanism": "scope_shift" if diverges else None,
        "quoted_span": "register the boat" if diverges else None,
        "rationale": "Widens who must register." if diverges else "",
        "labelled_at": "2026-09-27T21:30:00.000Z",
    }
    return {**label, **overrides}


def _export(*labels: dict[str, Any], **overrides: Any) -> str:
    document = {"format": "meaning-evals-gold", "version": 1, "seed": 5, "labels": list(labels)}
    return json.dumps({**document, **overrides})


def test_a_valid_export_becomes_gold_labels_sorted_by_item() -> None:
    gold = import_gold(_export(_label("p01-b", True), _label("p01-a", False)), ITEMS)
    assert [g.item_id for g in gold] == ["p01-a", "p01-b"]
    assert gold[1].mechanism is Mechanism.SCOPE_SHIFT
    assert gold[1].quoted_span == "register the boat"
    assert gold[1].labelled_on == date(2026, 9, 27)
    assert gold[0].quoted_span is None


def test_every_problem_in_the_export_is_reported_at_once() -> None:
    export = _export(
        _label("p01-zz", False),
        _label("p01-b", True, quoted_span="all boats must register"),
    )
    with pytest.raises(DataError) as raised:
        import_gold(export, ITEMS)
    message = str(raised.value)
    assert "2 problem" in message
    assert "p01-zz: not in items.jsonl" in message
    assert "p01-b: the quoted span does not occur verbatim in the answer" in message


def test_a_divergent_label_without_a_rationale_is_rejected() -> None:
    with pytest.raises(DataError, match="rationale"):
        import_gold(_export(_label("p01-b", True, rationale=" ")), ITEMS)


def test_a_non_divergent_label_with_a_mechanism_is_rejected() -> None:
    with pytest.raises(DataError, match="p01-a"):
        import_gold(_export(_label("p01-a", False, mechanism="scope_shift")), ITEMS)


def test_an_item_labelled_twice_is_rejected() -> None:
    with pytest.raises(DataError, match="twice"):
        import_gold(_export(_label("p01-a", False), _label("p01-a", False)), ITEMS)


@pytest.mark.parametrize(
    "text",
    [
        "not json",
        _export(_label("p01-a", False), format="other-worksheet"),
        _export({**_label("p01-a", False), "diverges": "no"}),
        _export(_label("p01-a", False, labelled_at="2026-09-27T21:30:00")),
    ],
)
def test_an_export_that_is_not_a_worksheet_export_is_rejected(text: str) -> None:
    with pytest.raises(DataError, match="not a meaning-evals worksheet export"):
        import_gold(text, ITEMS)
