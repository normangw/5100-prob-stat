"""Herfindahl-Hirschman Index. Needs the ownership dataset (not yet built)."""
import pandas as pd


def hhi(shares: pd.Series) -> float:
    """HHI on a 0-10,000 scale from market shares of one area-month.

    Shares may be given as fractions or percents; they are renormalised to sum to 1.
    """
    s = shares.dropna().astype(float)
    if s.empty or s.sum() <= 0:
        raise ValueError("shares must contain a positive total")
    s = s / s.sum()
    return float((s**2).sum() * 10_000)


def hhi_by_group(df: pd.DataFrame, group_cols: list[str], owner_col: str, value_col: str):
    """HHI per group, first summing value (e.g. win) to the parent-company level."""
    owners = df.groupby(group_cols + [owner_col])[value_col].sum().reset_index()
    return owners.groupby(group_cols)[value_col].apply(hhi).rename("hhi").reset_index()
