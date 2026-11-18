"""Project-wide constants. Change the series here, not in analysis code."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_XLSX = ROOT / "data" / "raw" / "1 - EXTRACT DATA BY AREA - Sept 2026 (external).xlsx"

# NGCB workbook has only combined Game & Table data (no blackjack-only sheet) until NGCB
# supplies one. Swap these names when blackjack-only data arrives.
WIN_PER_UNIT_PER_DAY_SHEET = "Win per Game & Table per Day"
GAME_COUNT_SHEET = "Game Count"
WIN_SHEET = "Game & Table Win"

HEADER_ROW = 3  # 1-indexed; row 1 is a title, row 2 holds the "Bal. of Clark" label overflow
AREAS = [
    "Statewide", "Clark County", "Downtown Las Vegas", "Las Vegas Strip",
    "North Las Vegas", "Laughlin", "Boulder Strip", "Mesquite", "Bal. of Clark County",
]
START, END = "2000-01-01", "2026-12-31"

# (label, start, end) -- inclusive month ranges for H1 and perspective comparisons
SHOCKS = [("GFC", "2008-01-01", "2009-12-31"), ("COVID", "2020-03-01", "2020-12-31")]
PERIODS = [
    ("pre-2008", "2000-01-01", "2007-12-31"),
    ("recession", "2008-01-01", "2009-12-31"),
    ("recovery", "2010-01-01", "2019-12-31"),
    ("covid", "2020-03-01", "2021-12-31"),
    ("post-covid", "2022-01-01", "2026-12-31"),
]

ALPHA = 0.05
SEED = 5100
N_PERM = 10_000
