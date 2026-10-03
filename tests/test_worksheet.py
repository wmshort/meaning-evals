from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from meaning_evals.errors import DataError
from meaning_evals.schema import Item, ItemKind, Mechanism
from meaning_evals.worksheet import render_worksheet, worksheet_payload, write_worksheet

from .builders import FAITHFUL_ANSWER, PASSAGE_TEXT, make_item, make_passage

MECHANISMS = list(Mechanism)
SHOWN_FIELDS = {"id", "passage_id", "question", "answer"}
HIDDEN_WORDS = ("intended_mechanism", "paired_item", "near_miss", "faithful", "divergent")


def _items() -> list[Item]:
    items = [make_item("p01-f", ItemKind.FAITHFUL)]
    for i, mechanism in enumerate(MECHANISMS[:4]):
        items.append(
            make_item(
                f"p01-d{i}",
                ItemKind.DIVERGENT,
                intended=mechanism,
                answer=FAITHFUL_ANSWER.replace("40", str(50 + i)),
            )
        )
        items.append(make_item(f"p01-n{i}", ItemKind.NEAR_MISS, paired=f"p01-d{i}"))
    return items


def _embedded(html: str) -> dict[str, Any]:
    found = re.search(
        r'<script id="worksheet-data" type="application/json">(.*?)</script>', html, re.S
    )
    assert found is not None
    data: dict[str, Any] = json.loads(found.group(1))
    return data


def assert_blind(html: str, items: list[Item]) -> None:
    """The worksheet shows passage, question and answer only: no generation intent."""
    for word in HIDDEN_WORDS:
        assert word not in html, f"{word!r} appears in the worksheet"
    shown = _embedded(html)["items"]
    assert all(set(record) == SHOWN_FIELDS for record in shown)
    by_id = {item.id: item for item in items}
    for record in shown:
        intended = by_id[record["id"]].intended_mechanism
        if intended is not None:
            assert intended.value not in json.dumps(record)


def test_worksheet_hides_every_trace_of_generation_intent() -> None:
    items = _items()
    html = render_worksheet(worksheet_payload([make_passage()], items, seed=5))
    assert_blind(html, items)
    assert FAITHFUL_ANSWER in json.dumps(_embedded(html), ensure_ascii=False)


def test_the_blindness_check_catches_a_leaked_intended_mechanism() -> None:
    items = _items()
    html = render_worksheet(worksheet_payload([make_passage()], items, seed=5))
    leaked = html.replace('"passage_id":', '"note":"scope_shift","passage_id":')
    with pytest.raises(AssertionError):
        assert_blind(leaked, items)
    named = html.replace('"passage_id":', '"intended_mechanism":"x","passage_id":', 1)
    with pytest.raises(AssertionError):
        assert_blind(named, items)


def test_items_are_shuffled_with_a_fixed_seed() -> None:
    items = _items()
    order = [r.id for r in worksheet_payload([make_passage()], items, seed=5).items]
    again = [r.id for r in worksheet_payload([make_passage()], items[::-1], seed=5).items]
    other = [r.id for r in worksheet_payload([make_passage()], items, seed=6).items]
    assert order == again
    assert order != other
    assert sorted(order) == sorted(item.id for item in items)
    assert order != sorted(order)


def test_payload_carries_the_passage_once_and_every_mechanism_to_choose_from() -> None:
    payload = worksheet_payload([make_passage()], _items(), seed=5).model_dump(mode="json")
    assert payload["passages"] == {"p01": {"title": "Invented fixture page", "text": PASSAGE_TEXT}}
    assert [m["id"] for m in payload["mechanisms"]] == [m.value for m in Mechanism]
    assert payload["format"] == "meaning-evals-gold"


def test_text_that_could_close_the_script_tag_is_escaped() -> None:
    hostile = make_item(
        "p01-x", ItemKind.FAITHFUL, answer="Fine </script><script>alert(1)</script>"
    )
    html = render_worksheet(worksheet_payload([make_passage()], [hostile], seed=1))
    assert "<script>alert(1)" not in html
    assert _embedded(html)["items"][0]["answer"] == hostile.answer


def test_every_local_storage_access_is_guarded() -> None:
    html = render_worksheet(worksheet_payload([make_passage()], _items(), seed=1))
    accesses = [line for line in html.splitlines() if "localStorage" in line]
    assert accesses
    assert all("try {" in line for line in accesses)


def test_storage_key_changes_when_the_items_change() -> None:
    first = worksheet_payload([make_passage()], _items(), seed=1).storage_key
    second = worksheet_payload([make_passage()], _items()[:-1], seed=1).storage_key
    assert first != second


def test_worksheet_is_written_as_one_self_contained_file(tmp_path: Path) -> None:
    path = tmp_path / "labels" / "gold-worksheet.html"
    write_worksheet(path, [make_passage()], _items(), seed=1)
    html = path.read_text(encoding="utf-8")
    assert html.startswith("<!doctype html>")
    assert not re.search(r"""(src|href)=["']https?://""", html)


def test_an_item_whose_passage_is_missing_is_a_data_error() -> None:
    with pytest.raises(DataError, match="p02"):
        orphan = make_item("p02-a", ItemKind.FAITHFUL, passage_id="p02")
        worksheet_payload([make_passage()], [orphan], seed=1)
