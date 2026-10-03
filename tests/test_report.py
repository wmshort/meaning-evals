from __future__ import annotations

import re

from meaning_evals.report import format_cell, render_report
from meaning_evals.scoring import Figure

from .test_scoring import FIRST_PASS, _score


def _cells(markdown: str) -> list[str]:
    return [cell.strip() for line in markdown.splitlines() for cell in line.split("|")[1:-1]]


def test_every_figure_cell_carries_its_n() -> None:
    markdown = render_report(_score())
    figure_cells = [c for c in _cells(markdown) if re.match(r"^(-?\d\.\d\d \[|n/a)", c)]
    assert figure_cells
    assert all(re.search(r"n=\d+$", cell) for cell in figure_cells)


def test_results_are_reported_under_the_model_the_responses_reported() -> None:
    markdown = render_report(_score())
    assert "a (a-model-2026)" in markdown
    assert "| a | a-model | a-model-2026 | 0.0 | not set | 1 | 6 | 0 |" in markdown


def test_false_alarms_on_recently_changed_guidance_have_their_own_column() -> None:
    markdown = render_report(_score())
    assert "False alarms: recently changed guidance" in markdown
    assert "False alarms: other guidance" in markdown


def test_a_known_figure_appears_with_its_interval() -> None:
    scores = _score()
    kappa = next(
        f
        for f in scores.figures
        if f.section == "detection" and f.judge == "a" and f.run == 1 and f.metric == "kappa_binary"
    )
    assert format_cell(kappa).startswith("0.67 [")
    assert format_cell(kappa) in render_report(scores)


def test_undefined_figures_read_as_not_available() -> None:
    undefined = Figure(
        section="detection",
        judge="a",
        metric="precision",
        value=None,
        low=None,
        high=None,
        n=0,
        interval="exact",
    )
    assert format_cell(undefined) == "n/a n=0"
    no_interval = undefined.model_copy(update={"value": 0.5, "n": 2})
    assert format_cell(no_interval) == "0.50 [no interval] n=2"


def test_disagreements_between_intent_and_gold_are_listed() -> None:
    markdown = render_report(_score())
    assert "| d3 | divergent | scope_shift | no | none |" in markdown


def test_report_names_every_section() -> None:
    markdown = render_report(_score())
    for heading in (
        "## Judges and the models their responses reported",
        "## Detection against the expert's labels",
        "## By mechanism",
        "### Scope shift",
        "## Self-agreement: run 1 against run 2",
        "## Judge against judge",
        "## Where the expert and the generation intent disagree",
    ):
        assert heading in markdown


def test_the_report_names_the_gold_file_it_was_scored_against() -> None:
    assert "against the gold labels in `data/gold.jsonl`" in render_report(_score())


def test_raters_are_listed_with_the_file_their_labels_came_from() -> None:
    markdown = render_report(_score(raters=(FIRST_PASS,)))
    assert "## Other raters" in markdown
    assert "| first-pass | data/first-pass.jsonl | 4 | 1 |" in markdown
    assert "first-pass (labels from data/first-pass.jsonl)" in markdown


def test_without_raters_there_is_no_raters_section() -> None:
    assert "## Other raters" not in render_report(_score())


def test_the_report_says_which_figures_carry_which_interval() -> None:
    markdown = render_report(_score())
    assert "exact Clopper-Pearson interval" in markdown
    assert "percentile bootstrap interval" in markdown
