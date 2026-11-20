"""Load NGCB workbook sheets into tidy (month, area, value) frames."""

import pandas as pd

from blackjack_take import config


def load_sheet(sheet: str, path=config.RAW_XLSX) -> pd.DataFrame:
    """Return long frame [month, area, value] for one sheet.

    Handles the workbook quirks: title row above the header, '#DIV/0!' strings, empty
    trailing rows, and a mostly-empty 'Bal. of Clark' header split across rows 2-3.
    """
    raw = pd.read_excel(path, sheet_name=sheet, header=config.HEADER_ROW - 1)
    raw = raw.rename(columns=lambda c: str(c).strip())
    raw = raw.rename(columns={"County": "Bal. of Clark County"})
    raw["Month"] = pd.to_datetime(raw["Month"], errors="coerce")
    raw = raw.dropna(subset=["Month"])
    value_cols = [c for c in raw.columns if c in config.AREAS]
    long = raw.melt(id_vars="Month", value_vars=value_cols, var_name="area", value_name="value")
    long["value"] = pd.to_numeric(long["value"], errors="coerce")  # '#DIV/0!' -> NaN
    long = long.rename(columns={"Month": "month"})
    return long[(long["month"] >= config.START) & (long["month"] <= config.END)].reset_index(
        drop=True
    )


def load_take(path=config.RAW_XLSX) -> pd.DataFrame:
    """Win per game per day by area, using the series named in config."""
    return load_sheet(config.WIN_PER_UNIT_PER_DAY_SHEET, path)


# --- Blackjack-only data (NGCB TL040, "001 - Twenty One") -------------------------------


def load_cpi(path=config.CPI_CSV) -> pd.Series:
    """FRED CPIAUCSL indexed by month start.

    Oct 2025 was never published (federal shutdown), so FRED has a blank there; it is linearly
    interpolated between Sep and Nov 2025. Any other gap is left as NaN.
    """
    cpi = pd.read_csv(path, parse_dates=["observation_date"]).set_index("observation_date")
    s = pd.to_numeric(cpi["CPIAUCSL"], errors="coerce").rename("cpi")
    gap = s.index == pd.Timestamp("2025-10-01")
    return s.where(~gap, s.interpolate(method="time"))


def _load_bj_sheet(sheet: str, area: str, path) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=sheet, header=config.BJ_HEADER_ROW - 1)
    raw["month"] = pd.to_datetime(raw["Period"], format="%m/%Y", errors="coerce")
    raw = raw.dropna(subset=["month"]).set_index("month")
    out = raw[["Count", "Drop", "Win"]].apply(pd.to_numeric, errors="coerce")
    out.columns = ["count", "drop", "win"]
    out.insert(0, "area", area)
    return out


def load_blackjack(
    areas=None, path=config.BJ_XLSX, start=config.BJ_SERIES_START, end=None
) -> pd.DataFrame:
    """Long frame [month, area, count, drop, win, win_per_game_per_day, hold, closed, cpi,
    real_win_per_game_per_day] on a full monthly grid per area.

    - Months with Count == 0 (the Apr-May 2020 closure) become NaN and are flagged `closed`.
    - Months absent from a sheet (e.g. Mesquite, Churchill) are explicit NaN rows.
    - win_per_game_per_day = win / count / days_in_month.
    - `end` defaults to the last month present in the data (never pads future months).
    - real_* is deflated by national CPI to config.CPI_BASE prices; nominal kept alongside.
    """
    wanted = {s: a for s, a in config.BJ_SHEETS.items() if areas is None or a in areas}
    sheets = {a: _load_bj_sheet(sh, a, path) for sh, a in wanted.items()}
    end = end or max(d.index.max() for d in sheets.values())
    grid = pd.date_range(start, end, freq="MS")
    cpi = load_cpi()
    deflator = cpi / cpi.loc[config.CPI_BASE]
    frames = []
    for area, raw in sheets.items():
        d = raw.reindex(grid)
        d["area"] = area
        d["closed"] = d["count"].fillna(0).eq(0)
        d.loc[d["closed"], ["count", "drop", "win"]] = float("nan")
        d["win_per_game_per_day"] = d["win"] / d["count"] / d.index.days_in_month
        d["hold"] = d["win"] / d["drop"]
        d["cpi"] = cpi.reindex(grid)
        d["real_win_per_game_per_day"] = d["win_per_game_per_day"] / deflator.reindex(grid)
        frames.append(d.rename_axis("month").reset_index())
    return pd.concat(frames, ignore_index=True)


def eligible_leaf_areas(df: pd.DataFrame, min_median_games: int = config.MIN_MEDIAN_GAMES):
    """Non-overlapping areas with a median monthly game count above the noise threshold."""
    med = df[df["area"].isin(config.LEAF_AREAS)].groupby("area")["count"].median()
    return sorted(med[med >= min_median_games].index)


def period_means(df: pd.DataFrame, value: str = "real_win_per_game_per_day") -> pd.DataFrame:
    """One value per area and config.PERIODS window (rows with NaN skipped). Use this for
    area-level permutation/ANOVA so each unit contributes one independent number per period."""
    parts = []
    for label, lo, hi in config.PERIODS:
        sub = df[(df["month"] >= lo) & (df["month"] <= hi)]
        m = sub.groupby("area")[value].mean().rename(value).reset_index()
        m["period"] = label
        parts.append(m)
    return pd.concat(parts, ignore_index=True)


def shock_split(
    df: pd.DataFrame,
    area: str = "Statewide",
    value: str = "real_win_per_game_per_day",
    start=config.START,
):
    """(shock, other) arrays for H1. Closure months are NaN and drop out automatically."""
    s = df[(df["area"] == area) & (df["month"] >= start)].set_index("month")[value].dropna()
    in_shock = pd.Series(False, index=s.index)
    for _, lo, hi in config.SHOCKS:
        in_shock |= (s.index >= lo) & (s.index <= hi)
    return s[in_shock].to_numpy(), s[~in_shock].to_numpy()
