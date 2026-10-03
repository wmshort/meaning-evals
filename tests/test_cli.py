"""The command line end to end, on a one-passage fixture, with every SDK client mocked."""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from meaning_evals.cli import ProviderFactory, main
from meaning_evals.jsonl import read_model, read_records, write_records
from meaning_evals.providers import ClientSettings, Provider, ProviderName
from meaning_evals.providers.anthropic_provider import AnthropicProvider
from meaning_evals.providers.google_provider import GoogleProvider
from meaning_evals.providers.openai_provider import OpenAIProvider
from meaning_evals.schema import GoldLabel, Item, ItemKind, JudgeResult
from meaning_evals.scoring import ScoreSet

from .builders import FIXED_NOW, generation_answer, make_passage, make_question
from .test_build import twins_in_question_order
from .test_providers import _claude_message, _gemini_response, _openai_response
from .test_worksheet import assert_blind

REPOSITORY = Path(__file__).resolve().parents[1]
KEYS = {
    "ANTHROPIC_API_KEY": "sk-ant-TESTKEY-anthropic-0001",
    "OPENAI_API_KEY": "sk-TESTKEY-openai-0002",
    "GEMINI_API_KEY": "TESTKEY-gemini-0003",
}
CONFIG = """
[generator]
provider = "google"
model = "gemini-generator"

[[judges]]
name = "claude"
provider = "anthropic"
model = "claude-judge"

[[judges]]
name = "gpt"
provider = "openai"
model = "gpt-judge"
temperature = 0.0

[[judges]]
name = "gemini"
provider = "google"
model = "gemini-judge"
temperature = 0.0

[worksheet]
seed = 11

[scoring]
bootstrap_resamples = 200
seed = 12
"""


@pytest.fixture(autouse=True)
def _detach_harness_log_handler() -> Iterator[None]:
    yield
    root = logging.getLogger()
    for handler in [h for h in root.handlers if type(h).__name__ == "_HarnessHandler"]:
        root.removeHandler(handler)


@pytest.fixture
def config(tmp_path: Path) -> Path:
    shutil.copytree(REPOSITORY / "prompts", tmp_path / "prompts")
    write_records(tmp_path / "data" / "passages.jsonl", [make_passage()])
    write_records(tmp_path / "data" / "questions.jsonl", [make_question()])
    path = tmp_path / "config.toml"
    path.write_text(CONFIG, encoding="utf-8")
    return path


def _answer_in(prompt: str) -> str:
    return prompt.split("<answer>\n", 1)[1].split("\n</answer>", 1)[0]


def _verdict_for(prompt: str) -> str:
    """Flags any fee other than the passage's 40 pounds as a quantitative divergence."""
    fee = re.search(r"\d+ pounds", _answer_in(prompt))
    if fee and fee.group(0) != "40 pounds":
        verdict = {
            "diverges": True,
            "mechanism": "quantitative_divergence",
            "quoted_span": fee.group(0),
        }
    else:
        verdict = {"diverges": False, "mechanism": "none", "quoted_span": ""}
    return json.dumps(verdict)


def _openai_reply(**request: Any) -> Any:
    prompt = request["input"]
    # One malformed reply per run, so the record of malformed output is exercised.
    text = "I think it diverges." if "50 pounds" in _answer_in(prompt) else _verdict_for(prompt)
    return _openai_response(text)


def _gemini_reply(model: str, contents: str, config: Any) -> Any:
    text = _verdict_for(contents) if "<answer>" in contents else generation_answer(contents)
    return _gemini_response(text)


def _factory(made: list[str]) -> ProviderFactory:
    def make(name: ProviderName, key: str, settings: ClientSettings) -> Provider:
        made.append(name)
        client = MagicMock()
        if name == "anthropic":
            client.messages.create.side_effect = lambda **kw: _claude_message(
                _verdict_for(kw["messages"][0]["content"])
            )
            return AnthropicProvider(client)
        if name == "openai":
            client.responses.create.side_effect = _openai_reply
            return OpenAIProvider(client)
        client.models.generate_content.side_effect = _gemini_reply
        return GoogleProvider(client)

    return make


def _labels_for(items: list[Item]) -> str:
    """What a careful labeller would export: the generation intent, as gold."""
    labels = []
    for item in items:
        divergent = item.kind is ItemKind.DIVERGENT
        span = re.search(r"\d+ pounds", item.answer)
        labels.append(
            {
                "item_id": item.id,
                "diverges": divergent,
                "mechanism": item.intended_mechanism.value if item.intended_mechanism else None,
                "quoted_span": span.group(0) if divergent and span else None,
                "rationale": "The fee is changed." if divergent else "",
                "labelled_at": "2026-09-27T10:00:00.000Z",
            }
        )
    return json.dumps({"format": "meaning-evals-gold", "version": 1, "seed": 11, "labels": labels})


def test_every_command_runs_end_to_end_against_mocked_providers(
    config: Path, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    base, made = config.parent, []

    def run(*args: str) -> int:
        argv = ["--config", str(config), *args]
        return main(argv, environ=KEYS, provider_factory=_factory(made), now=lambda: FIXED_NOW)

    assert run("build", "--faithful-only") == 0
    reviewed = read_records(base / "data" / "items.jsonl", Item)
    assert [item.kind for item in reviewed] == [ItemKind.FAITHFUL]
    assert run("build") == 0
    items = read_records(base / "data" / "items.jsonl", Item)
    assert len(items) == 9
    assert reviewed[0] in items
    assert run("worksheet") == 0
    assert_blind((base / "labels" / "gold-worksheet.html").read_text(encoding="utf-8"), items)
    (base / "export.json").write_text(_labels_for(items), encoding="utf-8")
    assert run("import-gold", str(base / "export.json")) == 0
    assert len(read_records(base / "data" / "gold.jsonl", GoldLabel)) == 9
    assert run("judge") == 0
    results_path = base / "data" / "runs" / "judge-results.jsonl"
    results = read_records(results_path, JudgeResult)
    assert len(results) == 3 * 2 * 9
    assert sorted((r.judge, r.run) for r in results if r.parse_error) == [("gpt", 1), ("gpt", 2)]
    assert run("judge") == 0
    assert len(read_records(results_path, JudgeResult)) == 54
    assert run("score") == 0
    scores = read_model(base / "results" / "scores.json", ScoreSet)
    assert scores.units == 9
    assert {s.judge for s in scores.judges} == {"claude", "gpt", "gemini"}
    assert run("report") == 0
    assert "## Detection against the expert's labels" in (base / "results" / "report.md").read_text(
        encoding="utf-8"
    )
    gold, other = base / "data" / "gold.jsonl", base / "results" / "other"
    rater = f"first-pass={gold}"
    assert run("score", "--gold", str(gold), "--rater", rater, "--out", str(other / "s.json")) == 0
    rescored = read_model(other / "s.json", ScoreSet)
    assert rescored.gold_file == "data/gold.jsonl"
    assert [(r.rater, r.units) for r in rescored.raters] == [("first-pass", 9)]
    assert run("report", "--scores", str(other / "s.json"), "--out", str(other / "r.md")) == 0
    assert "## Other raters" in (other / "r.md").read_text(encoding="utf-8")
    logged = caplog.text + capsys.readouterr().err
    assert all(key not in logged for key in KEYS.values())


def test_a_missing_key_stops_the_command_before_any_client_is_made(
    config: Path, caplog: pytest.LogCaptureFixture
) -> None:
    made: list[str] = []
    environ = {"ANTHROPIC_API_KEY": KEYS["ANTHROPIC_API_KEY"]}
    status = main(
        ["--config", str(config), "judge"], environ=environ, provider_factory=_factory(made)
    )
    assert status == 2
    assert made == []
    assert "OPENAI_API_KEY" in caplog.text and "GEMINI_API_KEY" in caplog.text
    assert KEYS["ANTHROPIC_API_KEY"] not in caplog.text


def test_build_without_the_generator_key_fails_before_reading_data(
    config: Path, caplog: pytest.LogCaptureFixture
) -> None:
    (config.parent / "data" / "passages.jsonl").unlink()
    status = main(["--config", str(config), "build"], environ={}, provider_factory=_factory([]))
    assert status == 2
    assert "GEMINI_API_KEY" in caplog.text


def test_an_unknown_judge_name_is_a_configuration_error(
    config: Path, caplog: pytest.LogCaptureFixture
) -> None:
    status = main(["--config", str(config), "judge", "--judge", "llama"], environ=KEYS)
    assert status == 2
    assert "llama" in caplog.text


def test_a_rater_without_a_path_is_refused(
    config: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit):
        main(["--config", str(config), "score", "--rater", "first-pass"], environ={})
    assert "NAME=PATH" in capsys.readouterr().err


def test_a_missing_configuration_is_reported_without_a_traceback(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    assert main(["--config", str(tmp_path / "absent.toml"), "score"], environ={}) == 2
    assert "does not exist" in caplog.text


def test_the_module_entry_point_lists_every_command() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "meaning_evals", "--help"],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    for command in ("build", "worksheet", "import-gold", "judge", "score", "report"):
        assert command in completed.stdout


def test_build_replaces_a_duplicate_twin_on_request(config: Path) -> None:
    base, made = config.parent, []

    def run(*args: str) -> int:
        argv = ["--config", str(config), *args]
        return main(argv, environ=KEYS, provider_factory=_factory(made), now=lambda: FIXED_NOW)

    assert run("build") == 0
    path = base / "data" / "items.jsonl"
    items = read_records(path, Item)
    twins = twins_in_question_order(items)
    repeat = twins[1].model_copy(update={"answer": twins[0].answer})
    write_records(path, [repeat if i.id == twins[1].id else i for i in items])
    assert run("build", "--replace-duplicate-twins") == 0
    repaired = read_records(path, Item)
    assert len(repaired) == 9
    assert len({i.answer for i in repaired}) == 9
    assert [i for i in repaired if i.id != twins[1].id and i.kind is not ItemKind.NEAR_MISS] == [
        i for i in items if i.kind is not ItemKind.NEAR_MISS
    ]


def test_replacing_duplicate_twins_cannot_be_combined_with_a_passage_rebuild(
    config: Path,
) -> None:
    argv = ["--config", str(config), "build", "--replace-duplicate-twins", "--passage", "p01"]
    assert main(argv, environ=KEYS, provider_factory=_factory([]), now=lambda: FIXED_NOW) != 0
