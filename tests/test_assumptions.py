import numpy as np
import pandas as pd
import pytest

from blackjack_take.data.hhi import hhi
from blackjack_take.stats import assumptions as A
from blackjack_take.stats.hypothesis import h1_two_groups, h3_anova


def test_hhi_monopoly_and_equal_split():
    assert hhi(pd.Series([1.0])) == pytest.approx(10_000)
    assert hhi(pd.Series([25, 25, 25, 25])) == pytest.approx(2_500)


def test_equal_variance_flags_unequal_groups():
    rng = np.random.default_rng(0)
    assert not A.equal_variance([rng.normal(0, 1, 200), rng.normal(0, 5, 200)]).passed


def test_outlier_check_flags_extreme_value():
    x = np.append(np.random.default_rng(1).normal(0, 1, 100), 25)
    assert not A.outliers(x).passed


def test_h1_falls_back_to_rank_test_for_skewed_data():
    rng = np.random.default_rng(2)
    shock, other = rng.lognormal(0, 1.2, 40), rng.lognormal(0.5, 1.2, 40)
    res = h1_two_groups(shock, other)
    assert res.primary == "mann_whitney_u"
    assert not res.assumptions.all_passed
    assert {"welch_t", "mann_whitney_u"} <= res.robustness.keys()


def test_h3_reports_assumptions_and_effect_size():
    rng = np.random.default_rng(3)
    res = h3_anova({k: rng.normal(m, 1, 60) for k, m in zip("abc", (0, 0.2, 1.5))})
    assert res.p_value < 0.05 and 0 < res.effect_size < 1
    assert res.assumptions.checks
