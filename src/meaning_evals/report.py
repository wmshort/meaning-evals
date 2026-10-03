"""report: the scores as Markdown tables, every figure with its interval and its n.

Each judge is labelled with the model ids its responses reported, not the ids requested;
each rater with the file its labels came from.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from meaning_evals.schema import MECHANISM_TEXT, Mechanism
from meaning_evals.scoring import AGREEMENT_METRICS, RATER_RUN, Figure, ScoreSet, Section

DETECTION_COLUMNS = (
    ("precision", "Precision"),
    ("recall", "Recall"),
    ("false_alarm_near_miss", "False alarms: near-miss twins"),
    ("false_alarm_faithful", "False alarms: faithful answers"),
    ("false_alarm_all", "False alarms: all non-divergent"),
    ("false_alarm_recent_change", "False alarms: recently changed guidance"),
    ("false_alarm_other_passages", "False alarms: other guidance"),
    ("kappa_binary", "κ, diverges or not"),
    ("kappa_mechanism", "κ, mechanism"),
    ("quote_found_rate", "Quote found"),
)
MECHANISM_COLUMNS = (
    ("precision", "Precision"),
    ("recall", "Recall"),
    ("detection_recall", "Detected, any mechanism"),
    ("false_alarm_near_miss", "False alarms: near-miss twins"),
    ("false_alarm_faithful", "False alarms: faithful answers"),
    ("false_alarm_all", "False alarms: all non-divergent"),
    ("kappa", "κ, this mechanism or not"),
    ("quote_found_rate", "Quote found"),
)
VIEW_NAMES = {"binary": "diverges or not", "mechanism": "mechanism (seven labels)"}
DIFFERENCE_NOTE = (
    "Difference is the agreement between the two raters minus the mean of their agreements "
    "with the expert, on the same items and resamples. A positive difference means they agree "
    "with each other more than with the expert."
)


def format_cell(figure: Figure) -> str:
    if figure.value is None:
        return f"n/a n={figure.n}"
    if figure.low is None or figure.high is None:
        return f"{figure.value:.2f} [no interval] n={figure.n}"
    return f"{figure.value:.2f} [{figure.low:.2f}, {figure.high:.2f}] n={figure.n}"


def _table(header: Sequence[str], rows: Iterable[Sequence[str]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return lines


def _lookup(figures: Iterable[Figure]) -> dict[tuple[object, ...], Figure]:
    return {
        (f.section, f.judge, f.run, f.other_judge, f.mechanism, f.view, f.metric): f
        for f in figures
    }


def _provenance(scores: ScoreSet) -> list[str]:
    rows = []
    for summary in scores.judges:
        for run in summary.runs:
            rows.append(
                [
                    summary.judge,
                    ", ".join(summary.requested_models),
                    ", ".join(summary.returned_model_ids),
                    ", ".join("not set" if t is None else str(t) for t in summary.temperatures),
                    ", ".join("not set" if e is None else e for e in summary.efforts),
                    str(run.run),
                    str(run.calls),
                    str(run.malformed),
                ]
            )
    header = [
        "Judge",
        "Requested model",
        "Model id reported by the responses",
        "Temperature",
        "Effort",
        "Run",
        "Calls",
        "Malformed",
    ]
    return ["## Judges and the models their responses reported", "", *_table(header, rows)]


def _raters(scores: ScoreSet) -> list[str]:
    if not scores.raters:
        return []
    rows = [[r.rater, r.source, str(r.units), str(RATER_RUN)] for r in scores.raters]
    note = (
        "Labels in the gold format, scored against the gold labels as one more rater with a "
        "single run. Labels counts the scored items each rater labelled."
    )
    return [
        "",
        "## Other raters",
        "",
        note,
        "",
        *_table(["Rater", "Labels from", "Labels", "Run"], rows),
    ]


def _judge_label(scores: ScoreSet) -> dict[str, str]:
    labels = {s.judge: f"{s.judge} ({', '.join(s.returned_model_ids)})" for s in scores.judges}
    labels.update({r.rater: f"{r.rater} (labels from {r.source})" for r in scores.raters})
    return labels


def _run_rows(
    scores: ScoreSet,
    section: str,
    columns: Sequence[tuple[str, str]],
    mechanism: Mechanism | None = None,
) -> list[str]:
    figures, labels = _lookup(scores.figures), _judge_label(scores)
    view = "one_vs_rest" if mechanism is not None else None
    keys = sorted({(f.judge, f.run) for f in scores.figures if f.section == section})
    rows = []
    for judge, run in keys:
        cells = [
            figures.get((section, judge, run, None, mechanism, view, metric))
            for metric, _ in columns
        ]
        row = [labels.get(judge, judge), str(run)]
        rows.append(row + [format_cell(c) if c else "" for c in cells])
    return _table(["Judge (reported model)", "Run", *(title for _, title in columns)], rows)


def _view_name(view: str | None, mechanism: Mechanism | None) -> str:
    if mechanism is not None:
        return f"{MECHANISM_TEXT[mechanism].label} or not"
    return VIEW_NAMES.get(view or "", view or "")


def _agreement(
    scores: ScoreSet, section: Section, heading: str, metric_titles: Sequence[str]
) -> list[str]:
    chosen = [f for f in scores.figures if f.section == section]
    figures, labels = _lookup(chosen), _judge_label(scores)
    groups = sorted({(f.judge, f.other_judge, f.run) for f in chosen}, key=repr)
    views = list(dict.fromkeys((f.view, f.mechanism) for f in chosen))
    metrics = AGREEMENT_METRICS[section]
    rows = []
    for judge, other, run in groups:
        for view, mechanism in views:
            name = labels.get(judge, judge) + (f" / {labels.get(other, other)}" if other else "")
            cells = [figures.get((section, judge, run, other, mechanism, view, m)) for m in metrics]
            row = [name, "" if run is None else str(run), _view_name(view, mechanism)]
            rows.append(row + [format_cell(c) if c else "" for c in cells])
    if not rows:
        return [heading, "", "No pairs of runs to compare."]
    header = ["Judges", "Run", "Labels compared", *metric_titles]
    return [heading, "", DIFFERENCE_NOTE, "", *_table(header, rows)]


def _disagreements(scores: ScoreSet) -> list[str]:
    heading = ["## Where the expert and the generation intent disagree", ""]
    if not scores.intent_disagreements:
        return [*heading, "None: every labelled item's gold label matches its generation intent."]
    rows = [
        [
            d.item_id,
            d.kind.value,
            d.intended_mechanism.value if d.intended_mechanism else "none",
            "yes" if d.gold_diverges else "no",
            d.gold_mechanism.value if d.gold_mechanism else "none",
        ]
        for d in scores.intent_disagreements
    ]
    header = ["Item", "Built as", "Intended mechanism", "Expert: diverges", "Expert: mechanism"]
    note = "The expert's label stands in every figure above."
    return [*heading, note, "", *_table(header, rows)]


def _preamble(scores: ScoreSet) -> list[str]:
    lines = [
        "# meaning-evals results",
        "",
        f"Scored {scores.scored_at.isoformat()} on {scores.units} items with a gold label "
        f"({scores.items} items built, {scores.gold_labels} gold labels), against the gold "
        f"labels in `{scores.gold_file}`.",
        "",
        "Each cell reads `estimate [low, high] n=N`, where N is the number of items the "
        "figure is computed on. A proportion (precision, recall, a false-alarm or quote "
        "rate) carries an exact Clopper-Pearson interval; κ and the agreement differences "
        "carry a percentile bootstrap interval over items "
        f"({scores.bootstrap_resamples} resamples, seed {scores.bootstrap_seed}). Both are "
        "95% intervals. `n/a` marks a figure that is undefined at that N. Malformed judge "
        "responses are counted, not scored.",
    ]
    excluded = (
        scores.excluded_gold_labels,
        scores.excluded_judge_results,
        scores.unlabelled_judge_results,
    )
    if any(excluded):
        lines += [
            "",
            f"Left out: {excluded[0]} gold labels and {excluded[1]} judge results for items "
            f"no longer built, and {excluded[2]} judge results for items without a gold label.",
        ]
    return lines


def render_report(scores: ScoreSet) -> str:
    lines = [*_preamble(scores), "", *_provenance(scores), *_raters(scores), ""]
    lines += ["## Detection against the expert's labels", ""]
    lines += [*_run_rows(scores, "detection", DETECTION_COLUMNS), "", "## By mechanism", ""]
    for mechanism in Mechanism:
        lines += [f"### {MECHANISM_TEXT[mechanism].label}", ""]
        lines += [*_run_rows(scores, "mechanism", MECHANISM_COLUMNS, mechanism), ""]
    lines += _agreement(
        scores,
        "self_agreement",
        "## Self-agreement: run 1 against run 2",
        ["κ, run 1 and run 2", "κ, run 1 and gold", "κ, run 2 and gold", "Difference"],
    )
    lines += [""]
    lines += _agreement(
        scores,
        "judge_agreement",
        "## Judge against judge",
        ["κ, the two judges", "κ, first judge and gold", "κ, second judge and gold", "Difference"],
    )
    lines += ["", *_disagreements(scores)]
    return "\n".join(lines) + "\n"
