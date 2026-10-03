from __future__ import annotations

from pathlib import Path

import pytest

from meaning_evals.config import Layout, load_settings
from meaning_evals.errors import ConfigError, DataError
from meaning_evals.jsonl import append_record, read_records, write_records
from meaning_evals.schema import ItemKind, Passage

from .builders import make_item, make_passage

REPOSITORY = Path(__file__).resolve().parents[1]

MINIMAL = """
[generator]
provider = "google"
model = "generator-model"

[[judges]]
name = "claude"
provider = "anthropic"
model = "judge-model"

[worksheet]
seed = 1

[scoring]
seed = 2
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_shipped_configuration_is_valid_and_names_four_judges() -> None:
    settings = load_settings(REPOSITORY / "config.toml")
    assert [(judge.name, judge.provider) for judge in settings.judges] == [
        ("claude", "anthropic"),
        ("gpt", "openai"),
        ("gpt-astra", "openai"),
        ("gemini", "google"),
    ]
    assert settings.generator.provider == "google"
    assert settings.judging.runs == 2
    assert settings.scoring.bootstrap_resamples == 10_000


def test_minimal_configuration_takes_the_documented_defaults(tmp_path: Path) -> None:
    settings = load_settings(_write(tmp_path, MINIMAL))
    assert settings.judges[0].temperature is None
    assert settings.requests.timeout_seconds == 120.0
    assert settings.requests.max_attempts == 4
    layout = Layout.resolve(settings.paths, tmp_path)
    assert layout.items == tmp_path / "data" / "items.jsonl"
    assert layout.judge_results == tmp_path / "data" / "runs" / "judge-results.jsonl"
    assert layout.worksheet == tmp_path / "labels" / "gold-worksheet.html"


def test_missing_configuration_is_a_config_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="does not exist"):
        load_settings(tmp_path / "absent.toml")


def test_invalid_toml_is_a_config_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not valid TOML"):
        load_settings(_write(tmp_path, "[generator"))


def test_duplicate_judge_names_are_rejected(tmp_path: Path) -> None:
    doubled = MINIMAL + '\n[[judges]]\nname = "claude"\nprovider = "openai"\nmodel = "m"\n'
    with pytest.raises(ConfigError, match="unique"):
        load_settings(_write(tmp_path, doubled))


def test_unknown_provider_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="provider"):
        load_settings(_write(tmp_path, MINIMAL.replace('"anthropic"', '"mistral"')))


def test_minimal_configuration_sets_no_effort(tmp_path: Path) -> None:
    assert load_settings(_write(tmp_path, MINIMAL)).judges[0].effort is None


def test_an_unknown_effort_level_is_rejected(tmp_path: Path) -> None:
    text = MINIMAL.replace('model = "judge-model"', 'model = "judge-model"\neffort = "extreme"')
    with pytest.raises(ConfigError, match="effort"):
        load_settings(_write(tmp_path, text))


def test_effort_on_a_google_model_is_rejected(tmp_path: Path) -> None:
    text = MINIMAL.replace(
        'model = "generator-model"', 'model = "generator-model"\neffort = "high"'
    )
    with pytest.raises(ConfigError, match="effort is not supported for google"):
        load_settings(_write(tmp_path, text))


def test_records_round_trip_through_a_jsonl_file(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "items.jsonl"
    items = [make_item("a", ItemKind.FAITHFUL), make_item("b", ItemKind.FAITHFUL)]
    write_records(path, items)
    assert read_records(path, type(items[0])) == items
    append_record(path, make_item("c", ItemKind.FAITHFUL))
    assert [item.id for item in read_records(path, type(items[0]))] == ["a", "b", "c"]
    assert not [p for p in path.parent.iterdir() if p.name.startswith(".")]


def test_an_invalid_line_is_reported_with_its_line_number(tmp_path: Path) -> None:
    path = tmp_path / "passages.jsonl"
    good = make_passage().model_dump_json()
    path.write_text(good + "\n" + '{"id": "p02"}\n', encoding="utf-8")
    with pytest.raises(DataError, match=r"passages.jsonl:2: "):
        read_records(path, Passage)


def test_a_missing_data_file_is_a_data_error(tmp_path: Path) -> None:
    with pytest.raises(DataError, match="does not exist"):
        read_records(tmp_path / "absent.jsonl", Passage)
