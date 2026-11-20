import numpy as np
import pandas as pd
import pytest

from blackjack_take import config
from blackjack_take.data.load import (
    eligible_leaf_areas,
    load_blackjack,
    load_cpi,
    shock_split,
)

pytestmark = pytest.mark.skipif(not config.BJ_XLSX.exists(), reason="raw data not present")


@pytest.fixture(scope="module")
def bj():
    return load_blackjack()


def test_full_grid_per_area(bj):
    assert bj.groupby("area").size().nunique() == 1
    assert bj["area"].nunique() == len(config.BJ_SHEETS)


def test_covid_closure_is_nan_and_flagged(bj):
    sw = bj[bj["area"] == "Statewide"].set_index("month")
    closed = sw.index[sw["closed"]]
    assert list(closed) == [pd.Timestamp("2020-04-01"), pd.Timestamp("2020-05-01")]
    assert sw.loc[closed, "win_per_game_per_day"].isna().all()


def test_win_per_game_per_day_formula(bj):
    # 01/1995 statewide: Count 3344, Win 84,190,117.74, 31 days
    row = bj[(bj["area"] == "Statewide") & (bj["month"] == "1995-01-01")].iloc[0]
    assert row["win_per_game_per_day"] == pytest.approx(84190117.74 / 3344 / 31)


def test_missing_months_are_explicit_nan(bj):
    mes = bj[bj["area"] == "Mesquite"]
    assert len(mes) == len(pd.date_range(config.BJ_SERIES_START, "2026-09-01", freq="MS"))
    assert mes["win"].isna().sum() >= 2


def test_cpi_covers_grid_and_base_month_is_identity():
    cpi = load_cpi()
    grid = pd.date_range(config.BJ_SERIES_START, "2026-09-01", freq="MS")
    assert cpi.reindex(grid).notna().all()
    df = load_blackjack(areas=["Statewide"])
    base = df[df["month"] == config.CPI_BASE]
    if len(base) and base["win_per_game_per_day"].notna().all():
        assert base["real_win_per_game_per_day"].iloc[0] == pytest.approx(
            base["win_per_game_per_day"].iloc[0]
        )


def test_leaf_areas_exclude_parents_and_tiny_areas(bj):
    leaves = eligible_leaf_areas(bj)
    assert not set(leaves) & set(config.PARENT_AREAS)
    assert "Las Vegas Strip" in leaves and "Nye" not in leaves


def test_h1_split_excludes_closure_months(bj):
    shock, other = shock_split(bj)
    assert not np.isnan(shock).any() and not np.isnan(other).any()
    # GFC 24 months + COVID Mar-Dec 2020 (10) minus 2 closed months
    assert len(shock) == 24 + 10 - 2
