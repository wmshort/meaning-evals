"""Scoring on a hand-checkable fixture: six labelled items, two judges, two runs."""

from __future__ import annotations

import pytest

from meaning_evals.errors import DataError
from meaning_evals.schema import GoldLabel, Item, ItemKind, JudgeResult, Mechanism, PassageId
from meaning_evals.scoring import Figure, Rater, ScoreSet, score

from .builders import FIXED_NOW, make_gold, make_item, make_result

SCOPE, POLARITY = Mechanism.SCOPE_SHIFT, Mechanism.POLARITY_REVERSAL
SPAN = "You must register"

# d1, d2 divergent (scope shift, polarity reversal); n1, n2 their near-miss twins;
# f1 faithful; d3 meant to diverge by scope shift, but the expert says it does not.
ITEMS = [
    make_item("d1", ItemKind.DIVERGENT, intended=SCOPE),
    make_item("d2", ItemKind.DIVERGENT, intended=POLARITY),
    make_item("d3", ItemKind.DIVERGENT, intended=SCOPE),
    make_item("n1", ItemKind.NEAR_MISS, paired="d1"),
    make_item("n2", ItemKind.NEAR_MISS, paired="d2"),
    make_item("f1", ItemKind.FAITHFUL),
]
GOLD = [
    make_gold("d1", True, SCOPE, SPAN),
    make_gold("d2", True, POLARITY, SPAN),
    make_gold("d3", False),
    make_gold("n1", False),
    make_gold("n2", False),
    make_gold("f1", False),
]


def _verdicts(judge: str, run: int, calls: dict[str, Mechanism | None]) -> list[JudgeResult]:
    return [
        make_result(item, judge, run, mechanism is not None, mechanism, SPAN if mechanism else None)
        for item, mechanism in calls.items()
    ]


# Judge "a" run 1: finds d1 (right mechanism) and d2 (wrong mechanism), false alarm on n1.
A1 = {"d1": SCOPE, "d2": SCOPE, "d3": None, "n1": SCOPE, "n2": None, "f1": None}
# Judge "a" run 2 agrees with run 1 except on n1.
A2 = {**A1, "n1": None}
# Judge "b" run 1 misses d2 and raises no false alarms.
B1 = {"d1": SCOPE, "d2": None, "d3": None, "n1": None, "n2": None, "f1": None}
RESULTS = _verdicts("a", 1, A1) + _verdicts("a", 2, A2) + _verdicts("b", 1, B1)


GOLD_FILE = "data/gold.jsonl"


def _score(
    items: list[Item] = ITEMS,
    gold: list[GoldLabel] = GOLD,
    results: list[JudgeResult] = RESULTS,
    resamples: int = 200,
    raters: tuple[Rater, ...] = (),
) -> ScoreSet:
    return score(
        items,
        gold,
        results,
        resamples=resamples,
        seed=7,
        now=lambda: FIXED_NOW,
        gold_file=GOLD_FILE,
        raters=raters,
    )


def _figure(scores: ScoreSet, **key: object) -> Figure:
    matches = [f for f in scores.figures if all(getattr(f, k) == v for k, v in key.items())]
    assert len(matches) == 1, f"{len(matches)} figures match {key}"
    return matches[0]


def test_detection_figures_match_the_hand_count() -> None:
    scores = _score()
    run = {"section": "detection", "judge": "a", "run": 1}
    # Flags d1, d2, n1; the gold positives are d1 and d2.
    assert _figure(scores, **run, metric="precision").value == pytest.approx(2 / 3)
    assert _figure(scores, **run, metric="precision").n == 3
    assert _figure(scores, **run, metric="recall").value == pytest.approx(1.0)
    # Gold negatives: d3, n1, n2, f1. Near-miss twins n1, n2; faithful f1.
    assert _figure(scores, **run, metric="false_alarm_near_miss").value == pytest.approx(0.5)
    assert _figure(scores, **run, metric="false_alarm_near_miss").n == 2
    assert _figure(scores, **run, metric="false_alarm_faithful").value == pytest.approx(0.0)
    assert _figure(scores, **run, metric="false_alarm_all").value == pytest.approx(1 / 4)
    assert _figure(scores, **run, metric="quote_found_rate").value == pytest.approx(1.0)


def test_false_alarms_on_recently_changed_guidance_are_reported_apart() -> None:
    # n1 and f1 come from a passage whose rules changed recently; d3 and n2 do not.
    recent = PassageId("p02")
    items = [
        i.model_copy(update={"passage_id": recent}) if i.id in {"n1", "f1"} else i for i in ITEMS
    ]
    scores = score(
        items,
        GOLD,
        RESULTS,
        resamples=200,
        seed=7,
        now=lambda: FIXED_NOW,
        gold_file=GOLD_FILE,
        recent_change_passages=frozenset({recent}),
    )
    run = {"section": "detection", "judge": "a", "run": 1}
    # Judge a run 1 raised a false alarm on n1 only.
    assert _figure(scores, **run, metric="false_alarm_recent_change").value == pytest.approx(0.5)
    assert _figure(scores, **run, metric="false_alarm_recent_change").n == 2
    assert _figure(scores, **run, metric="false_alarm_other_passages").value == pytest.approx(0.0)
    assert _figure(scores, **run, metric="false_alarm_other_passages").n == 2


def test_without_recently_changed_guidance_that_group_is_empty() -> None:
    run = {"section": "detection", "judge": "a", "run": 1}
    assert _figure(_score(), **run, metric="false_alarm_recent_change").n == 0
    assert _figure(_score(), **run, metric="false_alarm_other_passages").n == 4


def test_binary_kappa_against_the_gold_matches_the_hand_count() -> None:
    # Judge a run 1 vs gold on six items: agree on 5 of 6 (all but n1).
    # Judge says yes 3 times, gold 2: chance = (3*2 + 3*4) / 36 = 0.5; kappa = (5/6 - 0.5) / 0.5.
    figure = _figure(_score(), section="detection", judge="a", run=1, metric="kappa_binary")
    assert figure.value == pytest.approx(2 / 3)
    assert figure.n == 6
    assert figure.low is not None and figure.high is not None


def test_per_mechanism_figures_treat_the_mechanism_as_the_class() -> None:
    scores = _score()
    scope = {"section": "mechanism", "judge": "a", "run": 1, "mechanism": SCOPE}
    # Judge a run 1 names scope shift on d1, d2, n1; only d1 is a gold scope shift.
    assert _figure(scores, **scope, metric="precision").value == pytest.approx(1 / 3)
    assert _figure(scores, **scope, metric="recall").value == pytest.approx(1.0)
    polarity = {**scope, "mechanism": POLARITY}
    # d2 is a gold polarity reversal: detected (flagged), but misnamed.
    assert _figure(scores, **polarity, metric="recall").value == pytest.approx(0.0)
    assert _figure(scores, **polarity, metric="detection_recall").value == pytest.approx(1.0)
    assert _figure(scores, **polarity, metric="precision").value is None
    assert _figure(scores, **polarity, metric="precision").n == 0


def test_self_agreement_compares_the_two_runs_with_each_other_and_with_the_gold() -> None:
    scores = _score()
    self_binary = {"section": "self_agreement", "judge": "a", "view": "binary"}
    # Runs 1 and 2 differ only on n1: agree 5/6; run 1 says yes 3 times, run 2 twice.
    # chance = (3*2 + 3*4) / 36 = 0.5, so kappa = 2/3. Run 2 agrees with the gold on all six.
    assert _figure(scores, **self_binary, metric="kappa_run1_run2").value == pytest.approx(2 / 3)
    assert _figure(scores, **self_binary, metric="kappa_run2_gold").value == pytest.approx(1.0)
    delta = _figure(scores, **self_binary, metric="run_agreement_minus_gold_agreement")
    assert delta.value == pytest.approx(2 / 3 - (2 / 3 + 1.0) / 2)


def test_judge_agreement_is_reported_beside_each_judges_gold_agreement() -> None:
    scores = _score()
    pair = {"section": "judge_agreement", "judge": "a", "other_judge": "b", "run": 1}
    # a1 vs b1 on yes/no: a says yes on d1, d2, n1; b only on d1. Agree on 4/6.
    # chance = (3*1 + 3*5) / 36 = 0.5, kappa = (4/6 - 0.5) / 0.5 = 1/3.
    kappa = _figure(scores, **pair, view="binary", metric="kappa_judges")
    assert kappa.value == pytest.approx(1 / 3)
    assert _figure(scores, **pair, view="binary", metric="kappa_first_gold").value == (
        pytest.approx(2 / 3)
    )
    assert not [f for f in scores.figures if f.section == "judge_agreement" and f.run == 2]


def test_malformed_results_are_counted_and_left_out_of_the_figures() -> None:
    broken = make_result("f1", "b", 2, None)
    scores = _score(results=[*RESULTS, broken])
    summary = next(s for s in scores.judges if s.judge == "b")
    assert [(r.run, r.calls, r.malformed) for r in summary.runs] == [(1, 6, 0), (2, 1, 1)]
    run2 = _figure(scores, section="detection", judge="b", run=2, metric="kappa_binary")
    assert run2.n == 0
    assert run2.value is None


def test_records_for_items_no_longer_built_are_excluded_and_counted() -> None:
    orphan_gold = make_gold("gone", False)
    orphan_result = make_result("gone", "a", 1, False)
    scores = _score(gold=[*GOLD, orphan_gold], results=[*RESULTS, orphan_result])
    assert scores.excluded_gold_labels == 1
    assert scores.excluded_judge_results == 1
    assert scores.units == 6


def test_intent_and_gold_disagreements_are_listed() -> None:
    disagreements = _score().intent_disagreements
    assert [(d.item_id, d.gold_diverges) for d in disagreements] == [("d3", False)]


def test_every_figure_reports_n_and_intervals_are_reproducible() -> None:
    first, second = _score(), _score()
    assert all(isinstance(f.n, int) for f in first.figures)
    assert first.figures == second.figures
    for figure in first.figures:
        if figure.value is not None and figure.low is not None and figure.high is not None:
            assert figure.low <= figure.high


def test_scoring_needs_gold_labels() -> None:
    with pytest.raises(DataError, match="gold"):
        _score(gold=[])


def test_scoring_rejects_two_results_for_one_call() -> None:
    with pytest.raises(DataError, match="twice"):
        _score(results=[*RESULTS, RESULTS[0]])


def test_provenance_lists_the_models_the_responses_reported() -> None:
    summary = next(s for s in _score().judges if s.judge == "a")
    assert summary.requested_models == ("a-model",)
    assert summary.returned_model_ids == ("a-model-2026",)
    assert summary.temperatures == (0.0,)


# A first pass that missed d2 and called n2 a scope shift, labelled on four items only.
FIRST_PASS = Rater(
    "first-pass",
    "data/first-pass.jsonl",
    (
        make_gold("d1", True, SCOPE, SPAN),
        make_gold("d2", False),
        make_gold("n1", False),
        make_gold("n2", True, SCOPE, "not in the answer"),
    ),
)


def test_the_gold_file_is_recorded_with_the_scores() -> None:
    assert _score().gold_file == GOLD_FILE


def test_a_rater_is_scored_against_the_gold_like_a_judge_with_one_run() -> None:
    scores = _score(raters=(FIRST_PASS,))
    run = {"section": "detection", "judge": "first-pass", "run": 1}
    # Rated d1, d2, n1, n2. Flags d1 and n2; the gold positives among them are d1 and d2.
    assert _figure(scores, **run, metric="precision").value == pytest.approx(1 / 2)
    assert _figure(scores, **run, metric="recall").value == pytest.approx(1 / 2)
    assert _figure(scores, **run, metric="recall").n == 2
    assert _figure(scores, **run, metric="false_alarm_near_miss").value == pytest.approx(1 / 2)
    # Its quoted spans are checked against the answers: d1's occurs, n2's does not.
    assert _figure(scores, **run, metric="quote_found_rate").value == pytest.approx(1 / 2)
    assert _figure(scores, **run, metric="kappa_binary").n == 4


def test_a_rater_is_compared_with_each_judge_but_has_no_second_run() -> None:
    scores = _score(raters=(FIRST_PASS,))
    pairs = {
        (f.judge, f.other_judge, f.run) for f in scores.figures if f.section == "judge_agreement"
    }
    assert ("a", "first-pass", 1) in pairs
    assert ("b", "first-pass", 1) in pairs
    assert not [
        f for f in scores.figures if f.section == "self_agreement" and f.judge == "first-pass"
    ]
    # Judge b run 1 and the first pass, on the four items both rated: b flags d1 only.
    pair = {"section": "judge_agreement", "judge": "b", "other_judge": "first-pass", "run": 1}
    assert _figure(scores, **pair, view="binary", metric="kappa_judges").n == 4


def test_raters_are_summarised_apart_from_the_judges() -> None:
    scores = _score(raters=(FIRST_PASS,))
    assert [(r.rater, r.source, r.labels, r.units) for r in scores.raters] == [
        ("first-pass", "data/first-pass.jsonl", 4, 4)
    ]
    assert "first-pass" not in {s.judge for s in scores.judges}


def test_a_rater_may_not_take_a_judges_name() -> None:
    with pytest.raises(DataError, match="name"):
        _score(raters=(Rater("a", "x.jsonl", ()),))


def test_a_rater_that_labels_an_item_twice_is_refused() -> None:
    twice = Rater("twice", "x.jsonl", (make_gold("d1", False), make_gold("d1", False)))
    with pytest.raises(DataError, match="twice"):
        _score(raters=(twice,))


def test_proportions_carry_exact_intervals_and_kappas_bootstrap_ones() -> None:
    scores = _score()
    run = {"section": "detection", "judge": "a", "run": 1}
    recall = _figure(scores, **run, metric="recall")
    # Judge a run 1 finds both gold positives: 2 of 2, so the exact lower end is 0.025 ** (1/2).
    assert recall.interval == "exact"
    assert recall.low == pytest.approx(0.025**0.5)
    assert recall.high == pytest.approx(1.0)
    assert _figure(scores, **run, metric="kappa_binary").interval == "bootstrap"
