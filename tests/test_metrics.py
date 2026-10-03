from __future__ import annotations

import random

import pytest

from meaning_evals.metrics import (
    Estimate,
    Statistic,
    clopper_pearson,
    difference,
    estimate,
    kappa,
    mean_of,
    percentile,
    proportion,
    resample_weights,
)

ONES_10 = [1] * 10


def test_proportion_counts_numerator_over_denominator() -> None:
    statistic = proportion(numerator=[0, 1, 2], denominator=[0, 1, 2, 3, 4, 5, 6, 7])
    assert statistic.n == 8
    assert statistic.compute(ONES_10) == pytest.approx(3 / 8)


def test_proportion_uses_resample_weights() -> None:
    statistic = proportion(numerator=[0, 1, 2], denominator=[0, 1, 2, 3, 4, 5, 6, 7])
    # Unit 0 drawn three times, unit 7 not at all: numerator 3+1+1, denominator 3+6.
    weights = [3, 1, 1, 1, 1, 1, 1, 0, 1, 0]
    assert statistic.compute(weights) == pytest.approx(5 / 9)


def test_proportion_is_undefined_on_an_empty_denominator() -> None:
    assert proportion(numerator=[], denominator=[]).compute(ONES_10) is None
    assert proportion(numerator=[1], denominator=[1]).compute([1, 0]) is None


def test_binary_kappa_matches_the_hand_computed_value() -> None:
    # 20 yes/yes, 5 yes/no, 10 no/yes, 15 no/no.
    # observed = 35/50 = 0.7; A says yes 25 times, B 30 times;
    # expected = (25*30 + 25*20) / 2500 = 0.5; kappa = (0.7 - 0.5) / (1 - 0.5) = 0.4.
    first = ["y"] * 25 + ["n"] * 25
    second = ["y"] * 20 + ["n"] * 5 + ["y"] * 10 + ["n"] * 15
    statistic = kappa(first, second)
    assert statistic.n == 50
    assert statistic.compute([1] * 50) == pytest.approx(0.4)


def test_three_category_kappa_matches_the_hand_computed_value() -> None:
    # Agreement on 7 of 10; both raters use A 3, B 3, C 4 times.
    # expected = (9 + 9 + 16) / 100 = 0.34; kappa = (0.7 - 0.34) / 0.66 = 6/11.
    first = list("AAABBBCCCC")
    second = list("AABBBCCCCA")
    assert kappa(first, second).compute(ONES_10) == pytest.approx(6 / 11)


def test_kappa_is_one_for_perfect_agreement_and_undefined_without_variation() -> None:
    assert kappa(list("ABAB"), list("ABAB")).compute([1] * 4) == pytest.approx(1.0)
    assert kappa(list("AAAA"), list("AAAA")).compute([1] * 4) is None


def test_kappa_skips_units_either_rater_did_not_label() -> None:
    statistic = kappa(["A", "B", None, "A"], ["A", "B", "A", None])
    assert statistic.n == 2
    assert statistic.compute([1] * 4) == pytest.approx(1.0)


def test_difference_and_mean_combine_statistics_on_the_same_resample() -> None:
    first = proportion(numerator=[0, 1], denominator=[0, 1, 2, 3])
    second = proportion(numerator=[0], denominator=[0, 1, 2, 3])
    assert difference(first, second).compute([1] * 4) == pytest.approx(0.25)
    assert mean_of(first, second).compute([1] * 4) == pytest.approx(0.375)
    undefined = proportion(numerator=[], denominator=[])
    assert difference(first, undefined).compute([1] * 4) is None


def test_percentile_interpolates_between_order_statistics() -> None:
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert percentile(values, 0.5) == pytest.approx(3.0)
    assert percentile(values, 0.25) == pytest.approx(2.0)
    assert percentile(values, 0.1) == pytest.approx(1.4)
    forty = [float(v) for v in range(1, 41)]
    assert percentile(forty, 0.975) == pytest.approx(39.025)
    assert percentile([7.0], 0.975) == pytest.approx(7.0)


def test_resample_weights_draw_n_units_and_are_reproducible() -> None:
    first = resample_weights(12, 50, random.Random(3))
    second = resample_weights(12, 50, random.Random(3))
    other = resample_weights(12, 50, random.Random(4))
    assert first == second
    assert first != other
    assert len(first) == 50
    assert all(len(weights) == 12 and sum(weights) == 12 for weights in first)


def _bootstrapped(statistic: Statistic) -> Statistic:
    """The same figure without its counts, so that `estimate` resamples it."""
    return Statistic(statistic.compute, statistic.n)


def test_bootstrap_interval_contains_the_point_estimate() -> None:
    # 12 of 30 units positive: point estimate 0.4, standard error about 0.089,
    # so a 95% interval should be roughly 0.4 +/- 0.18.
    statistic = _bootstrapped(proportion(numerator=list(range(12)), denominator=list(range(30))))
    weights = resample_weights(30, 2000, random.Random(20260925))
    result = estimate(statistic, n_units=30, weight_sets=weights)
    assert result.value == pytest.approx(0.4)
    assert result.n == 30
    assert result.low is not None and result.high is not None
    assert result.low < 0.4 < result.high
    assert 0.25 < result.high - result.low < 0.45


def test_estimate_of_an_undefined_statistic_has_no_value_or_interval() -> None:
    result = estimate(proportion(numerator=[], denominator=[]), n_units=5, weight_sets=[[1] * 5])
    assert result == Estimate(value=None, low=None, high=None, n=0, interval="exact")


def test_interval_ignores_resamples_where_the_statistic_is_undefined() -> None:
    statistic = _bootstrapped(proportion(numerator=[0], denominator=[0, 1]))
    # The first resample leaves the denominator empty; the other two give 0.5 and 1.0,
    # so the 2.5th and 97.5th percentiles are 0.5 + 0.025 * 0.5 and 0.5 + 0.975 * 0.5.
    weight_sets = [[0, 0, 2], [1, 1, 0], [2, 0, 0]]
    result = estimate(statistic, n_units=3, weight_sets=weight_sets)
    assert result.value == pytest.approx(0.5)
    assert result.low == pytest.approx(0.5125)
    assert result.high == pytest.approx(0.9875)


def test_clopper_pearson_matches_the_published_interval_for_five_of_ten() -> None:
    # The exact 95% interval for 5 successes in 10 trials is [0.1871, 0.8129].
    low, high = clopper_pearson(5, 10)
    assert low == pytest.approx(0.187086, abs=1e-5)
    assert high == pytest.approx(0.812914, abs=1e-5)


def test_clopper_pearson_at_the_boundaries_has_its_closed_form() -> None:
    # With no successes the upper end is 1 - (alpha/2)^(1/n);
    # with all successes the lower end is (alpha/2)^(1/n).
    assert clopper_pearson(0, 61) == (0.0, pytest.approx(1 - 0.025 ** (1 / 61)))
    assert clopper_pearson(47, 47) == (pytest.approx(0.025 ** (1 / 47)), 1.0)


def test_clopper_pearson_needs_a_count_within_its_trials() -> None:
    with pytest.raises(ValueError):
        clopper_pearson(3, 2)
    with pytest.raises(ValueError):
        clopper_pearson(0, 0)


def test_a_proportion_carries_an_exact_interval_and_kappa_a_bootstrap_one() -> None:
    weights = resample_weights(10, 200, random.Random(1))
    share = estimate(
        proportion(numerator=[0, 1, 2, 3, 4], denominator=list(range(10))), 10, weights
    )
    assert share.interval == "exact"
    assert share.value == pytest.approx(0.5)
    assert share.low == pytest.approx(0.187086, abs=1e-5)
    agreement = estimate(kappa(list("ABABABABAB"), list("ABABABABAA")), 10, weights)
    assert agreement.interval == "bootstrap"


def test_a_perfect_proportion_still_has_a_width() -> None:
    perfect = estimate(proportion(numerator=list(range(47)), denominator=list(range(47))), 47, [])
    assert perfect.value == pytest.approx(1.0)
    assert perfect.high == pytest.approx(1.0)
    assert perfect.low is not None and perfect.low == pytest.approx(0.9245, abs=1e-4)
