"""worksheet: one self-contained HTML file for labelling every item blind.

The page shows each item's passage, question and answer, in an order shuffled with a fixed
seed, and nothing else about the item: no kind, no intended mechanism, no pairing, no
generator. Labels are kept in the browser's localStorage and exported as JSON for
`import-gold`.
"""

from __future__ import annotations

import hashlib
import random
from collections.abc import Sequence
from importlib import resources
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from meaning_evals.errors import DataError
from meaning_evals.jsonl import write_text_atomically
from meaning_evals.schema import MECHANISM_TEXT, Item, Passage

EXPORT_FORMAT = "meaning-evals-gold"
EXPORT_VERSION = 1
PLACEHOLDER = "__WORKSHEET_DATA__"
# Characters that could end the <script> element or open markup inside it.
SCRIPT_ESCAPES = {"<": "\\u003c", ">": "\\u003e", "&": "\\u0026"}


class _Shown(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ShownItem(_Shown):
    id: str
    passage_id: str
    question: str
    answer: str


class ShownPassage(_Shown):
    title: str
    text: str


class ShownMechanism(_Shown):
    id: str
    label: str
    definition: str


class WorksheetPayload(_Shown):
    format: Literal["meaning-evals-gold"]
    version: Literal[1]
    seed: int
    storage_key: str
    mechanisms: tuple[ShownMechanism, ...]
    passages: dict[str, ShownPassage]
    items: tuple[ShownItem, ...]


def worksheet_payload(
    passages: Sequence[Passage], items: Sequence[Item], seed: int
) -> WorksheetPayload:
    by_id = {passage.id: passage for passage in passages}
    used = sorted({item.passage_id for item in items})
    if missing := [p for p in used if p not in by_id]:
        raise DataError(f"items refer to passage(s) not in the passages file: {', '.join(missing)}")
    ordered = sorted(items, key=lambda item: item.id)
    random.Random(seed).shuffle(ordered)  # noqa: S311 - a reproducible order, not a secret
    digest = hashlib.sha256("\n".join(sorted(item.id for item in items)).encode()).hexdigest()
    return WorksheetPayload(
        format=EXPORT_FORMAT,
        version=EXPORT_VERSION,
        seed=seed,
        storage_key=f"{EXPORT_FORMAT}:{digest[:16]}",
        mechanisms=tuple(
            ShownMechanism(id=m.value, label=t.label, definition=t.definition)
            for m, t in MECHANISM_TEXT.items()
        ),
        passages={p: ShownPassage(title=by_id[p].page_title, text=by_id[p].text) for p in used},
        items=tuple(
            ShownItem(id=i.id, passage_id=i.passage_id, question=i.question, answer=i.answer)
            for i in ordered
        ),
    )


def render_worksheet(payload: WorksheetPayload) -> str:
    template = (
        resources.files("meaning_evals")
        .joinpath("templates/worksheet.html")
        .read_text(encoding="utf-8")
    )
    if template.count(PLACEHOLDER) != 1:
        raise DataError(f"the worksheet template must contain {PLACEHOLDER} exactly once")
    data = payload.model_dump_json()
    for character, escape in SCRIPT_ESCAPES.items():
        data = data.replace(character, escape)
    return template.replace(PLACEHOLDER, data)


def write_worksheet(
    path: Path, passages: Sequence[Passage], items: Sequence[Item], seed: int
) -> int:
    """Write the worksheet to `path`; returns the number of items on it."""
    if not items:
        raise DataError("there are no items to label; run build first")
    write_text_atomically(path, render_worksheet(worksheet_payload(passages, items, seed)))
    return len(items)
