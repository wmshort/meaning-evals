"""The prompt templates in `prompts/`, loaded and checked for their placeholders.

Templates use `string.Template` placeholders (`$passage`), so JSON braces in a prompt need no
escaping. Each template must use exactly the placeholders listed for it below: a template
that drops `$passage` would otherwise send the model a prompt without the guidance.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from string import Template

from meaning_evals.errors import ConfigError
from meaning_evals.schema import MECHANISM_TEXT

PLACEHOLDERS: dict[str, frozenset[str]] = {
    "generator_system": frozenset(),
    "faithful": frozenset({"passage", "question"}),
    "divergent": frozenset(
        {"passage", "question", "faithful_answer", "mechanism_label", "mechanism_definition"}
    ),
    "near_miss": frozenset(
        {"passage", "question", "faithful_answer", "altered_answer", "rewordings_in_use"}
    ),
    "judge_system": frozenset(),
    "judge": frozenset({"mechanisms", "passage", "question", "answer"}),
}


@dataclass(frozen=True)
class PromptSet:
    generator_system: Template
    faithful: Template
    divergent: Template
    near_miss: Template
    judge_system: Template
    judge: Template


def _load(directory: Path, name: str) -> Template:
    path = directory / f"{name}.txt"
    try:
        template = Template(path.read_text(encoding="utf-8").strip())
    except FileNotFoundError as exc:
        raise ConfigError(f"prompt template {path} does not exist") from exc
    if not template.is_valid():
        raise ConfigError(f"prompt template {path} has a malformed placeholder")
    found, expected = set(template.get_identifiers()), PLACEHOLDERS[name]
    if found != expected:
        raise ConfigError(
            f"prompt template {path} must use exactly {sorted(expected)}; it uses {sorted(found)}"
        )
    return template


def load_prompts(directory: Path) -> PromptSet:
    return PromptSet(**{name: _load(directory, name) for name in PLACEHOLDERS})


def render(template: Template, **values: str) -> str:
    return template.substitute(**values)


def mechanism_catalogue() -> str:
    """The six mechanisms as the judge sees them: identifier, then definition."""
    return "\n".join(
        f"- {mechanism.value}: {text.definition}" for mechanism, text in MECHANISM_TEXT.items()
    )
