"""Proportions, Cohen's kappa and their 95% intervals, in the standard library.

A proportion carries an exact Clopper-Pearson interval, computed from its counts; every
other statistic carries a percentile bootstrap interval. The bootstrap collapses to a point
when a proportion is 0 or 1 on every resample, which is where the exact interval matters.

Every statistic is computed from a vector of per-unit weights, where the unit is an item.
The point estimate uses a weight of one for every unit; a bootstrap resample uses the
number of times each unit was drawn. Sharing one set of resamples across statistics makes
differences between them (for example kappa between two runs minus kappa against the
gold) paired by construction.

Cost: a statistic over a subset of k units is O(k) per resample, so an interval over R
resamples is O(R * k).
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable, Hashable, Sequence
from dataclasses import dataclass
from typing import Literal

WeightedFunction = Callable[[Sequence[int]], float | None]
Interval = Literal["bootstrap", "exact"]
INTERVAL_LEVEL = 0.95
BISECTION_STEPS = 60


@dataclass(frozen=True)
class Statistic:
    """A figure that can be recomputed on any resample; `n` is its unit count at the point.

    `successes` is set for a proportion, whose interval is then exact.
    """

    compute: WeightedFunction
    n: int
    successes: int | None = None


@dataclass(frozen=True)
class Estimate:
    value: float | None
    low: float | None
    high: float | None
    n: int
    interval: Interval


def _total(weights: Sequence[int], indices: Sequence[int]) -> int:
    return sum([weights[i] for i in indices])


def proportion(numerator: Sequence[int], denominator: Sequence[int]) -> Statistic:
    """The weighted share of `denominator` units that are also `numerator` units."""
    top, bottom = tuple(numerator), tuple(denominator)

    def compute(weights: Sequence[int]) -> float | None:
        base = _total(weights, bottom)
        return _total(weights, top) / base if base else None

    return Statistic(compute, len(bottom), successes=len(set(top) & set(bottom)))


def kappa(first: Sequence[Hashable | None], second: Sequence[Hashable | None]) -> Statistic:
    """Cohen's unweighted kappa between two raters' per-unit labels.

    A unit counts only where both raters gave a label. Kappa is undefined (None) when no
    unit counts or when chance agreement is 1, that is, both raters used one category.
    """
    units = [i for i, (a, b) in enumerate(zip(first, second, strict=True)) if None not in (a, b)]
    agree = tuple(i for i in units if first[i] == second[i])
    categories = sorted({first[i] for i in units} | {second[i] for i in units}, key=repr)
    by_first = [tuple(i for i in units if first[i] == c) for c in categories]
    by_second = [tuple(i for i in units if second[i] == c) for c in categories]
    counted = tuple(units)

    def compute(weights: Sequence[int]) -> float | None:
        total = _total(weights, counted)
        if not total:
            return None
        observed = _total(weights, agree) / total
        chance = sum(
            _total(weights, a) * _total(weights, b)
            for a, b in zip(by_first, by_second, strict=True)
        ) / (total * total)
        if math.isclose(chance, 1.0):
            return None
        return (observed - chance) / (1.0 - chance)

    return Statistic(compute, len(counted))


def difference(first: Statistic, second: Statistic) -> Statistic:
    """`first` minus `second`, evaluated on the same resample."""

    def compute(weights: Sequence[int]) -> float | None:
        a, b = first.compute(weights), second.compute(weights)
        return None if a is None or b is None else a - b

    return Statistic(compute, first.n)


def mean_of(*statistics: Statistic) -> Statistic:
    """The mean of several statistics on the same resample; undefined if any is."""

    def compute(weights: Sequence[int]) -> float | None:
        values = [s.compute(weights) for s in statistics]
        defined = [v for v in values if v is not None]
        return sum(defined) / len(defined) if len(defined) == len(values) else None

    return Statistic(compute, min(s.n for s in statistics))


def _upper_tail(successes: int, trials: int, p: float) -> float:
    """P(X >= successes) for X ~ Binomial(trials, p)."""
    if p <= 0.0:
        return 0.0 if successes > 0 else 1.0
    if p >= 1.0:
        return 1.0
    log_p, log_q = math.log(p), math.log1p(-p)
    terms = [
        math.exp(
            math.lgamma(trials + 1)
            - math.lgamma(i + 1)
            - math.lgamma(trials - i + 1)
            + i * log_p
            + (trials - i) * log_q
        )
        for i in range(successes, trials + 1)
    ]
    return math.fsum(terms)


def _solve(target: Callable[[float], float], increasing: bool) -> float:
    """The p in [0, 1] at which a monotone `target` crosses zero, by bisection."""
    low, high = 0.0, 1.0
    for _ in range(BISECTION_STEPS):
        middle = (low + high) / 2
        if (target(middle) < 0) == increasing:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def clopper_pearson(successes: int, trials: int) -> tuple[float, float]:
    """The exact (Clopper-Pearson) interval at `INTERVAL_LEVEL` for a binomial proportion.

    The lower end is the p at which P(X >= successes) equals half the tail mass, the upper
    end the p at which P(X <= successes) does. Cost: O(trials) per bisection step.
    """
    if trials < 1 or not 0 <= successes <= trials:
        raise ValueError(f"no proportion of {successes} in {trials}")
    tail = (1.0 - INTERVAL_LEVEL) / 2
    low = 0.0
    if successes > 0:
        low = _solve(lambda p: _upper_tail(successes, trials, p) - tail, increasing=True)
    high = 1.0
    if successes < trials:
        high = _solve(
            lambda p: (1.0 - _upper_tail(successes + 1, trials, p)) - tail, increasing=False
        )
    return low, high


def resample_weights(n_units: int, resamples: int, rng: random.Random) -> list[list[int]]:
    """`resamples` draws of `n_units` units with replacement, as per-unit counts."""
    population = range(n_units)
    draws: list[list[int]] = []
    for _ in range(resamples):
        weights = [0] * n_units
        for unit in rng.choices(population, k=n_units):
            weights[unit] += 1
        draws.append(weights)
    return draws


def percentile(sorted_values: Sequence[float], fraction: float) -> float:
    """Linear interpolation between order statistics (Hyndman and Fan's definition 7)."""
    position = (len(sorted_values) - 1) * fraction
    below = math.floor(position)
    above = min(below + 1, len(sorted_values) - 1)
    share = position - below
    return sorted_values[below] + share * (sorted_values[above] - sorted_values[below])


def estimate(statistic: Statistic, n_units: int, weight_sets: Sequence[Sequence[int]]) -> Estimate:
    """The point estimate with its interval at `INTERVAL_LEVEL`: exact for a proportion,
    percentile bootstrap otherwise.

    Bootstrap resamples on which the statistic is undefined are left out of the interval.
    """
    interval: Interval = "bootstrap" if statistic.successes is None else "exact"
    value = statistic.compute([1] * n_units)
    if value is None:
        return Estimate(value=None, low=None, high=None, n=statistic.n, interval=interval)
    if statistic.successes is not None:
        low, high = clopper_pearson(statistic.successes, statistic.n)
        return Estimate(value=value, low=low, high=high, n=statistic.n, interval=interval)
    values = sorted(v for v in (statistic.compute(w) for w in weight_sets) if v is not None)
    if not values:
        return Estimate(value=value, low=None, high=None, n=statistic.n, interval=interval)
    tail = (1.0 - INTERVAL_LEVEL) / 2
    return Estimate(
        value=value,
        low=percentile(values, tail),
        high=percentile(values, 1.0 - tail),
        n=statistic.n,
        interval=interval,
    )
