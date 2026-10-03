"""The TOML configuration: which models play which role, request limits, seeds and paths.

Model names live here and nowhere in the code. Paths are resolved against the directory
that holds the configuration file.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from meaning_evals.errors import ConfigError
from meaning_evals.providers import ClientSettings, ProviderName
from meaning_evals.schema import Effort


class _Section(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ModelSettings(_Section):
    provider: ProviderName
    model: str = Field(min_length=1)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    effort: Effort | None = None
    max_output_tokens: int = Field(default=16_000, gt=0)

    @model_validator(mode="after")
    def _effort_where_supported(self) -> Self:
        # Gemini sets thinking depth through its own `thinking_level`, which this harness
        # does not send; a Gemini model runs at its default.
        if self.provider == "google" and self.effort is not None:
            raise ValueError("effort is not supported for google models; leave it unset")
        return self


class JudgeSettings(ModelSettings):
    name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")


class RequestSettings(_Section):
    timeout_seconds: float = Field(default=120.0, gt=0)
    max_attempts: int = Field(default=4, ge=1, le=10)

    def client_settings(self) -> ClientSettings:
        return ClientSettings(timeout_seconds=self.timeout_seconds, max_attempts=self.max_attempts)


class JudgingSettings(_Section):
    runs: int = Field(default=2, ge=1)


class WorksheetSettings(_Section):
    seed: int


class ScoringSettings(_Section):
    bootstrap_resamples: int = Field(default=10_000, ge=1)
    seed: int


class PathSettings(_Section):
    data_dir: Path = Path("data")
    prompts_dir: Path = Path("prompts")
    results_dir: Path = Path("results")
    labels_dir: Path = Path("labels")


class Settings(_Section):
    generator: ModelSettings
    judges: tuple[JudgeSettings, ...] = Field(min_length=1)
    requests: RequestSettings = RequestSettings()
    judging: JudgingSettings = JudgingSettings()
    worksheet: WorksheetSettings
    scoring: ScoringSettings
    paths: PathSettings = PathSettings()

    @model_validator(mode="after")
    def _judge_names_unique(self) -> Self:
        names = [judge.name for judge in self.judges]
        if len(set(names)) != len(names):
            raise ValueError(f"judge names must be unique; got {names}")
        return self


@dataclass(frozen=True)
class Layout:
    """Where every file the commands read or write lives."""

    passages: Path
    questions: Path
    items: Path
    gold: Path
    judge_results: Path
    prompts_dir: Path
    worksheet: Path
    scores: Path
    report: Path

    @classmethod
    def resolve(cls, paths: PathSettings, base_dir: Path) -> Layout:
        data, results = base_dir / paths.data_dir, base_dir / paths.results_dir
        return cls(
            passages=data / "passages.jsonl",
            questions=data / "questions.jsonl",
            items=data / "items.jsonl",
            gold=data / "gold.jsonl",
            judge_results=data / "runs" / "judge-results.jsonl",
            prompts_dir=base_dir / paths.prompts_dir,
            worksheet=base_dir / paths.labels_dir / "gold-worksheet.html",
            scores=results / "scores.json",
            report=results / "report.md",
        )


def load_settings(path: Path) -> Settings:
    """Read and validate the configuration file, or raise `ConfigError` saying why not."""
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"configuration file {path} does not exist") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path} is not valid TOML: {exc}") from exc
    try:
        return Settings.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(f"{path} is invalid:\n{exc}") from exc
