"""Reading and writing validated records as JSON Lines, one record per line.

Whole-file writes go through a temporary file and an atomic rename, so an interrupted
command never leaves a half-written file behind. Appends are flushed and synced per record.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel, ValidationError

from meaning_evals.errors import DataError


def _describe(exc: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc']) or 'record'}: {error['msg']}"
        for error in exc.errors(include_url=False)
    )


def read_records[R: BaseModel](path: Path, model: type[R]) -> list[R]:
    """Parse every non-blank line of `path` as `model`; the first invalid line is an error."""
    if not path.exists():
        raise DataError(f"{path} does not exist")
    records: list[R] = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(model.model_validate_json(line))
            except ValidationError as exc:
                raise DataError(f"{path}:{number}: {_describe(exc)}") from exc
    return records


def read_records_if_present[R: BaseModel](path: Path, model: type[R]) -> list[R]:
    return read_records(path, model) if path.exists() else []


def write_text_atomically(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError:
        Path(temporary).unlink(missing_ok=True)
        raise


def write_records(path: Path, records: Iterable[BaseModel]) -> None:
    write_text_atomically(path, "".join(record.model_dump_json() + "\n" for record in records))


def append_record(path: Path, record: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(record.model_dump_json() + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def read_model[R: BaseModel](path: Path, model: type[R]) -> R:
    """Parse a whole file holding one JSON document."""
    if not path.exists():
        raise DataError(f"{path} does not exist")
    try:
        return model.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        raise DataError(f"{path}: {_describe(exc)}") from exc
