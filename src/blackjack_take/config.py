"""Project-wide constants. Change the series here, not in analysis code."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Blackjack-only ("001 - Twenty One") NGCB report TL040, one sheet per area, Count/Drop/Win monthly.
BJ_XLSX = ROOT / "data" / "raw" / "Copy of Device Summary 1995 to 09.30.26 - NWang 11.19.26.xlsx"
BJ_HEADER_ROW = 2  # 1-indexed; row 1 holds the area label and device name
BJ_SERIES_START = "1995-01-01"  # extra pre-period history for time series; tests use START
CPI_CSV = ROOT / "data" / "raw" / "CPIAUCSL.csv"  # FRED CPI-U, SA, national (proxy for NV prices)
CPI_BASE = "2025-12-01"  # real dollars are expressed in this month's prices

# Sheet name -> area label.
BJ_SHEETS = {
    "Statewide": "Statewide",
    "Clark County Games": "Clark County",
    "Washoe County Games": "Washoe County",
    "Elko County Games": "Elko County",
    "Douglas County Games": "Douglas County",
    "Bal. of Clark County Games": "Bal. of Clark County",
    "Downtown Games": "Downtown Las Vegas",
    "LV Strip Games": "Las Vegas Strip",
    "N. Las Vegas Games": "North Las Vegas",
    "Laughlin Games": "Laughlin",
    "Boulder Hwy Games": "Boulder Strip",
    "Mesquite Games": "Mesquite",
    "Washoe Bal of Cty Games": "Bal. of Washoe County",
    "Reno Games": "Reno",
    "Sparks Games": "Sparks",
    "No Shore Lake Tahoe Games": "North Shore Lake Tahoe",
    "Elko Bal of County Games": "Bal. of Elko County",
    "Wendover Games": "Wendover",
    "South Shore Lake Tahoe Games": "South Shore Lake Tahoe",
    "Churchill Games": "Churchill",
    "Nye Games": "Nye",
    "Carson City Games": "Carson City",
}
# Parents contain children; never put a parent and its child in the same ANOVA/permutation.
# Verified against the data: Clark = 7 sub-areas, Washoe = Bal+Reno+Sparks+North Shore LT,
# Elko = Bal+Wendover (all exact). South Shore LT sits inside Douglas County.
PARENT_AREAS = ["Statewide", "Clark County", "Washoe County", "Elko County", "Douglas County"]
LEAF_AREAS = [a for a in BJ_SHEETS.values() if a not in PARENT_AREAS]
MIN_MEDIAN_GAMES = 20  # drop areas whose median monthly game count is smaller (too noisy)

START = "2000-01-01"  # headline comparisons start here; BJ_SERIES_START is the data start

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

# Dated property -> parent-company mapping (hand-built; see data/ownership.py for the checks).
OWNERSHIP_CSV = ROOT / "data" / "external" / "ownership.csv"
