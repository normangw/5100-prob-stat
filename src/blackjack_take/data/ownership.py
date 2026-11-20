"""Load and validate the hand-built ownership table (property -> parent company, dated).

Columns: property, area, parent_company, start, end, source.
`start`/`end` are inclusive months (YYYY-MM or YYYY-MM-DD); leave `end` blank if still owned.
`area` must be a name from config.BJ_SHEETS. One row per ownership spell per property.
"""

import pandas as pd

from blackjack_take import config

COLUMNS = ["property", "area", "parent_company", "start", "end", "source"]


def load_ownership(path=config.OWNERSHIP_CSV) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str).apply(lambda c: c.str.strip())
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"ownership file missing columns: {sorted(missing)}")
    df["start"] = pd.to_datetime(df["start"])
    df["end"] = pd.to_datetime(df["end"])  # blank -> NaT (still owned)
    return df[COLUMNS]


def validate_ownership(df: pd.DataFrame) -> list[str]:
    """Return a list of problems (empty list = OK)."""
    problems = []
    for col in ["property", "area", "parent_company", "start"]:
        n = int(df[col].isna().sum())
        if n:
            problems.append(f"{n} rows missing {col}")
    bad_areas = sorted(set(df["area"].dropna()) - set(config.BJ_SHEETS.values()))
    if bad_areas:
        problems.append(f"unknown areas: {bad_areas}")
    parents = sorted(set(df["area"].dropna()) & set(config.PARENT_AREAS))
    if parents:
        problems.append(f"use leaf areas, not parents: {parents}")
    if (df["end"] < df["start"]).any():
        problems.append("rows with end before start")
    # overlapping ownership spells for the same property
    for prop, g in df.sort_values("start").groupby("property"):
        ends = g["end"].fillna(pd.Timestamp.max)
        if (g["start"].iloc[1:].to_numpy() <= ends.iloc[:-1].to_numpy()).any():
            problems.append(f"overlapping spells: {prop}")
    return problems


def owner_at(df: pd.DataFrame, month) -> pd.DataFrame:
    """Rows of the ownership table in force in `month`."""
    m = pd.Timestamp(month)
    return df[(df["start"] <= m) & (df["end"].isna() | (df["end"] >= m))]
