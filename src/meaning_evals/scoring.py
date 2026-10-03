"""score: every figure per judge and per mechanism, each with a bootstrap 95% interval.

The unit of analysis is an item that carries a gold label. The expert's gold is the truth:
where it disagrees with generation intent, the gold stands and the disagreement is listed.
A malformed judge response contributes no verdict and is counted per run.

A rater is a set of labels in the gold format, such as a second annotator's, scored
against the gold exactly as a judge's run is: as one more rater with a single run, compared
with the gold and with every judge.

Intervals: a proportion (precision, recall, a false-alarm or quote rate) carries an exact
Clopper-Pearson interval. Kappa and the agreement differences carry a percentile bootstrap
interval: one set of item-level resamples (N items drawn with replacement, fixed seed) is
shared by every figure, so differences between figures are paired. A resample on which a
figure is undefined is left out of that figure's interval.

False alarms are also reported apart for guidance whose rules changed recently, since a
judge that answers from what it learned in training, not from the passage, would flag
faithful answers there.
"""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from itertools import combinations
from typing import Literal

from pydantic import AwareDatetime

from meaning_evals.errors import DataError
from meaning_evals.metrics import (
    Interval,
    Statistic,
    difference,
    estimate,
    kappa,
    mean_of,
    proportion,
    resample_weights,
)
from meaning_evals.schema import (
    Effort,
    GoldLabel,
    Item,
    ItemId,
    ItemKind,
    JudgeResult,
    Mechanism,
    PassageId,
    Record,
    quote_found,
)

Section = Literal["detection", "mechanism", "self_agreement", "judge_agreement"]
View = Literal["binary", "mechanism", "one_vs_rest"]
Label = str | None
YES, NO, NONE, OTHER = "yes", "no", "none", "other"
RATER_RUN = 1

AGREEMENT_METRICS: dict[Section, tuple[str, str, str, str]] = {
    "self_agreement": (
        "kappa_run1_run2",
        "kappa_run1_gold",
        "kappa_run2_gold",
        "run_agreement_minus_gold_agreement",
    ),
    "judge_agreement": (
        "kappa_judges",
        "kappa_first_gold",
        "kappa_second_gold",
        "judge_agreement_minus_gold_agreement",
    ),
}


class Figure(Record):
    section: Section
    judge: str
    metric: str
    run: int | None = None
    other_judge: str | None = None
    mechanism: Mechanism | None = None
    view: View | None = None
    value: float | None
    low: float | None
    high: float | None
    n: int
    interval: Interval


class RunSummary(Record):
    run: int
    calls: int
    malformed: int


class JudgeSummary(Record):
    judge: str
    requested_models: tuple[str, ...]
    returned_model_ids: tuple[str, ...]
    temperatures: tuple[float | None, ...]
    efforts: tuple[Effort | None, ...]
    runs: tuple[RunSummary, ...]


class RaterSummary(Record):
    rater: str
    source: str
    labels: int
    units: int


class IntentDisagreement(Record):
    item_id: ItemId
    kind: ItemKind
    intended_mechanism: Mechanism | None
    gold_diverges: bool
    gold_mechanism: Mechanism | None


class ScoreSet(Record):
    scored_at: AwareDatetime
    gold_file: str
    items: int
    gold_labels: int
    units: int
    excluded_gold_labels: int
    excluded_judge_results: int
    unlabelled_judge_results: int
    bootstrap_resamples: int
    bootstrap_seed: int
    judges: tuple[JudgeSummary, ...]
    raters: tuple[RaterSummary, ...]
    figures: tuple[Figure, ...]
    intent_disagreements: tuple[IntentDisagreement, ...]


@dataclass(frozen=True)
class Rater:
    """Labels in the gold format, scored as one more rater; `source` says where they came from."""

    name: str
    source: str
    labels: Sequence[GoldLabel]


@dataclass(frozen=True)
class _Labels:
    """One rater's labels per unit; None where the rater gave no usable verdict."""

    binary: tuple[Label, ...]
    category: tuple[Label, ...]
    found: tuple[bool | None, ...]

    def one_vs_rest(self, mechanism: Mechanism) -> tuple[Label, ...]:
        return tuple(
            None if c is None else (mechanism.value if c == mechanism.value else OTHER)
            for c in self.category
        )

    def restricted(self, keep: Sequence[bool]) -> _Labels:
        def mask[T](values: tuple[T | None, ...]) -> tuple[T | None, ...]:
            return tuple(v if k else None for v, k in zip(values, keep, strict=True))

        return _Labels(mask(self.binary), mask(self.category), mask(self.found))

    def views(self) -> dict[tuple[View, Mechanism | None], tuple[Label, ...]]:
        views: dict[tuple[View, Mechanism | None], tuple[Label, ...]] = {
            ("binary", None): self.binary,
            ("mechanism", None): self.category,
        }
        for mechanism in Mechanism:
            views["one_vs_rest", mechanism] = self.one_vs_rest(mechanism)
        return views


@dataclass(frozen=True)
class _Universe:
    items: tuple[Item, ...]
    gold_records: tuple[GoldLabel, ...]
    gold: _Labels
    recent: tuple[bool, ...]

    @property
    def n(self) -> int:
        return len(self.items)


@dataclass(frozen=True)
class _Key:
    section: Section
    judge: str
    metric: str
    run: int | None = None
    other_judge: str | None = None
    mechanism: Mechanism | None = None
    view: View | None = None


@dataclass(frozen=True)
class _Spec:
    key: _Key
    statistic: Statistic


Calls = dict[tuple[str, int], dict[ItemId, JudgeResult]]
Ratings = dict[tuple[str, int], _Labels]


def _gold_labels(gold: Sequence[GoldLabel]) -> _Labels:
    return _Labels(
        binary=tuple(YES if g.diverges else NO for g in gold),
        category=tuple(g.mechanism.value if g.mechanism else NONE for g in gold),
        found=tuple(None for _ in gold),
    )


def _judge_labels(universe: _Universe, calls: dict[ItemId, JudgeResult]) -> _Labels:
    results = [calls.get(item.id) for item in universe.items]
    usable = [r if r is not None and r.diverges is not None else None for r in results]
    return _Labels(
        binary=tuple(None if r is None else (YES if r.diverges else NO) for r in usable),
        category=tuple(
            None if r is None else (r.mechanism.value if r.mechanism else NONE) for r in usable
        ),
        found=tuple(None if r is None else r.quote_found for r in usable),
    )


def _rater_labels(universe: _Universe, rater: Rater) -> _Labels:
    """The rater's labels per unit; None on units it did not label. Spans are checked here."""
    by_item: dict[ItemId, GoldLabel] = {}
    for label in rater.labels:
        if label.item_id in by_item:
            raise DataError(f"rater {rater.name} labels item {label.item_id} twice")
        by_item[label.item_id] = label
    given = [by_item.get(item.id) for item in universe.items]
    return _Labels(
        binary=tuple(None if g is None else (YES if g.diverges else NO) for g in given),
        category=tuple(
            None if g is None else (g.mechanism.value if g.mechanism else NONE) for g in given
        ),
        found=tuple(
            None if g is None else quote_found(g.quoted_span, item.answer)
            for g, item in zip(given, universe.items, strict=True)
        ),
    )


def _ratings(universe: _Universe, calls: Calls, raters: Sequence[Rater]) -> Ratings:
    ratings = {key: _judge_labels(universe, by_item) for key, by_item in calls.items()}
    taken = {judge for judge, _ in calls}
    for rater in raters:
        if rater.name in taken:
            raise DataError(f"rater {rater.name} has the name of a judge or of another rater")
        taken.add(rater.name)
        ratings[rater.name, RATER_RUN] = _rater_labels(universe, rater)
    return ratings


def _false_alarms(
    universe: _Universe, valid: Sequence[int], raised: Callable[[int], bool]
) -> dict[str, Statistic]:
    negatives = [i for i in valid if universe.gold.binary[i] == NO]
    subsets = {
        "near_miss": [i for i in negatives if universe.items[i].kind is ItemKind.NEAR_MISS],
        "faithful": [i for i in negatives if universe.items[i].kind is ItemKind.FAITHFUL],
        "all": negatives,
    }
    return {
        f"false_alarm_{name}": proportion([i for i in subset if raised(i)], subset)
        for name, subset in subsets.items()
    }


def _false_alarms_by_recency(
    universe: _Universe, valid: Sequence[int], raised: Callable[[int], bool]
) -> dict[str, Statistic]:
    negatives = [i for i in valid if universe.gold.binary[i] == NO]
    subsets = {
        "recent_change": [i for i in negatives if universe.recent[i]],
        "other_passages": [i for i in negatives if not universe.recent[i]],
    }
    return {
        f"false_alarm_{name}": proportion([i for i in subset if raised(i)], subset)
        for name, subset in subsets.items()
    }


def _detection(universe: _Universe, judge: str, run: int, labels: _Labels) -> list[_Spec]:
    valid = [i for i in range(universe.n) if labels.binary[i] is not None]
    flagged = [i for i in valid if labels.binary[i] == YES]
    positives = [i for i in valid if universe.gold.binary[i] == YES]
    hits = [i for i in flagged if universe.gold.binary[i] == YES]

    def raised(i: int) -> bool:
        return labels.binary[i] == YES

    statistics = {
        "precision": proportion(hits, flagged),
        "recall": proportion(hits, positives),
        **_false_alarms(universe, valid, raised),
        **_false_alarms_by_recency(universe, valid, raised),
        "kappa_binary": kappa(labels.binary, universe.gold.binary),
        "kappa_mechanism": kappa(labels.category, universe.gold.category),
        "quote_found_rate": proportion([i for i in flagged if labels.found[i]], flagged),
    }
    return [_Spec(_Key("detection", judge, m, run=run), s) for m, s in statistics.items()]


def _per_mechanism(universe: _Universe, judge: str, run: int, labels: _Labels) -> list[_Spec]:
    valid = [i for i in range(universe.n) if labels.binary[i] is not None]
    specs: list[_Spec] = []
    for mechanism in Mechanism:
        value = mechanism.value
        named = [i for i in valid if labels.category[i] == value]
        actual = [i for i in valid if universe.gold.category[i] == value]
        right = [i for i in named if universe.gold.category[i] == value]
        statistics = {
            "precision": proportion(right, named),
            "recall": proportion(right, actual),
            "detection_recall": proportion([i for i in actual if labels.binary[i] == YES], actual),
            **_false_alarms(universe, valid, _names(labels, value)),
            "kappa": kappa(labels.one_vs_rest(mechanism), universe.gold.one_vs_rest(mechanism)),
            "quote_found_rate": proportion([i for i in named if labels.found[i]], named),
        }
        key = _Key("mechanism", judge, "", run=run, mechanism=mechanism, view="one_vs_rest")
        specs += [_Spec(replace(key, metric=m), s) for m, s in statistics.items()]
    return specs


def _names(labels: _Labels, value: str) -> Callable[[int], bool]:
    """Whether the rater named mechanism `value` on a unit."""
    return lambda i: labels.category[i] == value


def _agreement(key: _Key, first: _Labels, second: _Labels, gold: _Labels) -> list[_Spec]:
    """Kappa between two raters, and each against the gold, on units both rated."""
    both = [
        a is not None and b is not None for a, b in zip(first.binary, second.binary, strict=True)
    ]
    views = [labels.restricted(both).views() for labels in (first, second, gold)]
    specs: list[_Spec] = []
    for (view, mechanism), a in views[0].items():
        b, g = views[1][view, mechanism], views[2][view, mechanism]
        pair, a_gold, b_gold = kappa(a, b), kappa(a, g), kappa(b, g)
        delta = difference(pair, mean_of(a_gold, b_gold))
        for metric, statistic in zip(
            AGREEMENT_METRICS[key.section], (pair, a_gold, b_gold, delta), strict=True
        ):
            specific = replace(key, metric=metric, mechanism=mechanism, view=view)
            specs.append(_Spec(specific, statistic))
    return specs


def _all_specs(universe: _Universe, labels: Ratings) -> list[_Spec]:
    specs: list[_Spec] = []
    for (judge, run), judged in sorted(labels.items()):
        specs += [
            *_detection(universe, judge, run, judged),
            *_per_mechanism(universe, judge, run, judged),
        ]
    judges = sorted({judge for judge, _ in labels})
    for judge in judges:
        if (judge, 1) in labels and (judge, 2) in labels:
            key = _Key("self_agreement", judge, "")
            specs += _agreement(key, labels[judge, 1], labels[judge, 2], universe.gold)
    for first, second in combinations(judges, 2):
        shared = {r for j, r in labels if j == first} & {r for j, r in labels if j == second}
        for run in sorted(shared):
            key = _Key("judge_agreement", first, "", run=run, other_judge=second)
            specs += _agreement(key, labels[first, run], labels[second, run], universe.gold)
    return specs


def _figures(specs: Iterable[_Spec], n_units: int, resamples: int, seed: int) -> tuple[Figure, ...]:
    # A seeded generator for statistical resampling, not for anything security-bearing.
    weights = resample_weights(n_units, resamples, random.Random(seed))  # noqa: S311
    figures = []
    for spec in specs:
        result, key = estimate(spec.statistic, n_units, weights), spec.key
        figures.append(
            Figure(
                section=key.section,
                judge=key.judge,
                metric=key.metric,
                run=key.run,
                other_judge=key.other_judge,
                mechanism=key.mechanism,
                view=key.view,
                value=result.value,
                low=result.low,
                high=result.high,
                n=result.n,
                interval=result.interval,
            )
        )
    return tuple(figures)


def _universe(
    items: Sequence[Item], gold: Sequence[GoldLabel], recent_passages: frozenset[PassageId]
) -> _Universe:
    known = {item.id: item for item in items}
    labelled: dict[ItemId, GoldLabel] = {}
    for label in gold:
        if label.item_id in labelled:
            raise DataError(f"item {label.item_id} has two gold labels")
        if label.item_id in known:
            labelled[label.item_id] = label
    if not labelled:
        raise DataError("no gold labels for the current items; label them and run import-gold")
    ids = sorted(labelled)
    records = tuple(labelled[i] for i in ids)
    units = tuple(known[i] for i in ids)
    recent = tuple(item.passage_id in recent_passages for item in units)
    return _Universe(units, records, _gold_labels(records), recent)


def _calls(results: Iterable[JudgeResult]) -> Calls:
    calls: Calls = defaultdict(dict)
    for result in results:
        by_item = calls[result.judge, result.run]
        if result.item_id in by_item:
            raise DataError(
                f"judge {result.judge} run {result.run} has item {result.item_id} twice"
            )
        by_item[result.item_id] = result
    return dict(calls)


def _summaries(results: Sequence[JudgeResult]) -> tuple[JudgeSummary, ...]:
    summaries = []
    for judge in sorted({r.judge for r in results}):
        own = [r for r in results if r.judge == judge]
        runs = sorted({r.run for r in own})
        summaries.append(
            JudgeSummary(
                judge=judge,
                requested_models=tuple(sorted({r.requested_model for r in own})),
                returned_model_ids=tuple(sorted({r.returned_model_id for r in own})),
                temperatures=tuple(
                    sorted({r.temperature for r in own}, key=lambda t: (t is None, t or 0.0))
                ),
                efforts=tuple(sorted({r.effort for r in own}, key=lambda e: (e is None, e or ""))),
                runs=tuple(
                    RunSummary(
                        run=run,
                        calls=sum(1 for r in own if r.run == run),
                        malformed=sum(1 for r in own if r.run == run and r.parse_error),
                    )
                    for run in runs
                ),
            )
        )
    return tuple(summaries)


def _rater_summaries(universe: _Universe, raters: Sequence[Rater]) -> tuple[RaterSummary, ...]:
    scored = {item.id for item in universe.items}
    return tuple(
        RaterSummary(
            rater=rater.name,
            source=rater.source,
            labels=len(rater.labels),
            units=sum(1 for label in rater.labels if label.item_id in scored),
        )
        for rater in raters
    )


def _intent_disagreements(universe: _Universe) -> tuple[IntentDisagreement, ...]:
    found = []
    for item, gold in zip(universe.items, universe.gold_records, strict=True):
        intended = item.kind is ItemKind.DIVERGENT
        if gold.diverges != intended or (intended and gold.mechanism != item.intended_mechanism):
            found.append(
                IntentDisagreement(
                    item_id=item.id,
                    kind=item.kind,
                    intended_mechanism=item.intended_mechanism,
                    gold_diverges=gold.diverges,
                    gold_mechanism=gold.mechanism,
                )
            )
    return tuple(found)


def score(
    items: Sequence[Item],
    gold: Sequence[GoldLabel],
    results: Sequence[JudgeResult],
    *,
    resamples: int,
    seed: int,
    now: Callable[[], datetime],
    gold_file: str,
    recent_change_passages: frozenset[PassageId] = frozenset(),
    raters: Sequence[Rater] = (),
) -> ScoreSet:
    """Score every judge run, and every rater, against `gold`, read from `gold_file`."""
    universe = _universe(items, gold, recent_change_passages)
    known_items = {item.id for item in items}
    current = [r for r in results if r.item_id in known_items]
    labelled = {item.id for item in universe.items}
    specs = _all_specs(universe, _ratings(universe, _calls(current), raters))
    return ScoreSet(
        scored_at=now(),
        gold_file=gold_file,
        items=len(items),
        gold_labels=len(gold),
        units=universe.n,
        excluded_gold_labels=sum(1 for g in gold if g.item_id not in known_items),
        excluded_judge_results=len(results) - len(current),
        unlabelled_judge_results=sum(1 for r in current if r.item_id not in labelled),
        bootstrap_resamples=resamples,
        bootstrap_seed=seed,
        judges=_summaries(current),
        raters=_rater_summaries(universe, raters),
        figures=_figures(specs, universe.n, resamples, seed),
        intent_disagreements=_intent_disagreements(universe),
    )
