"""import-gold: the worksheet's exported JSON, validated, as gold labels.

Every problem in the export is collected and reported together, so one pass fixes them all.
A quoted span must occur verbatim in the answer it quotes. The imported labels replace the
contents of `gold.jsonl`.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, StrictBool, ValidationError

from meaning_evals.errors import DataError
from meaning_evals.schema import GoldLabel, Item, ItemId, Mechanism, quote_found


class _Exported(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ExportedLabel(_Exported):
    item_id: ItemId
    diverges: StrictBool
    mechanism: Mechanism | None
    quoted_span: str | None
    rationale: str
    labelled_at: AwareDatetime


class WorksheetExport(_Exported):
    format: Literal["meaning-evals-gold"]
    version: Literal[1]
    seed: int
    labels: tuple[ExportedLabel, ...]


def _parse(text: str) -> WorksheetExport:
    try:
        return WorksheetExport.model_validate_json(text)
    except ValidationError as exc:
        first = exc.errors(include_url=False)[0]
        where = ".".join(str(part) for part in first["loc"]) or "document"
        raise DataError(
            f"the file is not a meaning-evals worksheet export ({where}: {first['msg']})"
        ) from exc


def _gold(label: ExportedLabel, item: Item) -> GoldLabel:
    span = label.quoted_span.strip() if label.quoted_span is not None else None
    gold = GoldLabel(
        item_id=label.item_id,
        diverges=label.diverges,
        mechanism=label.mechanism,
        quoted_span=span,
        rationale=label.rationale.strip(),
        labelled_on=label.labelled_at.astimezone(UTC).date(),
    )
    if gold.quoted_span is not None and not quote_found(gold.quoted_span, item.answer):
        raise ValueError("the quoted span does not occur verbatim in the answer")
    return gold


def import_gold(text: str, items: Sequence[Item]) -> list[GoldLabel]:
    """Validate a worksheet export against the current items and return its gold labels."""
    export = _parse(text)
    by_id = {item.id: item for item in items}
    labels: list[GoldLabel] = []
    problems: list[str] = []
    seen: set[ItemId] = set()
    for label in export.labels:
        if label.item_id in seen:
            problems.append(f"{label.item_id}: labelled twice")
            continue
        seen.add(label.item_id)
        if label.item_id not in by_id:
            problems.append(f"{label.item_id}: not in items.jsonl")
            continue
        try:
            labels.append(_gold(label, by_id[label.item_id]))
        except ValidationError as exc:
            reasons = "; ".join(str(e["msg"]) for e in exc.errors(include_url=False))
            problems.append(f"{label.item_id}: {reasons}")
        except ValueError as exc:
            problems.append(f"{label.item_id}: {exc}")
    if problems:
        listed = "\n".join(f"- {problem}" for problem in problems)
        raise DataError(f"the export has {len(problems)} problem(s):\n{listed}")
    return sorted(labels, key=lambda gold: gold.item_id)
