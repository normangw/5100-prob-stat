# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

DSAN 5100 Group 6, "Dealing the House's Edge": how Nevada's blackjack take (win per game per day) changed 2000-2026, and whether economic shocks (2008-09, 2020) and ownership concentration (HHI) explain it. Proposal: `docs/proposal/Group 6.pdf`. Test-selection and assumption cheatsheet (R-flavoured): `docs/references/stats-test-cheatsheet.html`.

- H1: win/game/day lower in shock periods. Welch t, Wilcoxon rank-sum as check.
- H2: above-median-HHI areas have higher win/game. Permutation test.
- H3: win/game differs across areas. One-way ANOVA, Kruskal-Wallis backup.
- Time series: ADF/KPSS, STL, ACF/PACF, SARIMA fit on pre-shock data vs. actual, structural breaks, cross-correlation with LVCVA visitors and FRED Nevada unemployment.

## Commands

Use uv. Do not use the system anaconda Python: it has a broken NumPy 2 / NumPy 1 compiled-module mix.

```
uv sync                                   # create .venv from pyproject.toml
uv run pytest                             # all tests
uv run pytest tests/test_assumptions.py::test_hhi_monopoly_and_equal_split   # one test
uv run ruff check . && uv run ruff format .
uv run jupyter lab                        # notebooks/
```

## Architecture

Pipeline: `data/raw` (immutable) -> `src/blackjack_take/data` (load/clean, HHI) -> `data/interim|processed` (gitignored) -> `stats` and `ts` -> `reports/{figures,tables}`. Notebooks in `notebooks/` call the package; logic lives in `src/`, not notebooks.

- `config.py` is the single place for sheet-to-area map, shock/period windows, alpha, seed, permutation count. Blackjack-only workbook, CPI and area mappings (`BJ_SHEETS`, `LEAF_AREAS`) live here.
- `stats/assumptions.py` returns `AssumptionReport` objects; `stats/hypothesis.py` (H1-H3) and `ts/diagnostics.py` run them before computing and return them alongside results. Keep that coupling.

## Data (data/raw)

Primary: `Copy of Device Summary 1995 to 09.30.26 - NWang 11.19.26.xlsx` (NGCB TL040, **blackjack only**, "001 - Twenty One"). One sheet per area (Statewide + 21), header on row 2: `Period` (`MM/YYYY`), `Count` (games), `Drop`, `Win`; monthly 01/1995-09/2026. Load with `data.load.load_blackjack()`.

- **Closure zeros:** Apr-May 2020 have Count = 0 everywhere. The loader sets them to NaN and flags `closed`; never treat them as zero take.
- **Gaps:** Mesquite (379 rows) and Churchill (334, ends 2025-01) are missing months. The loader reindexes to a full grid so they are explicit NaN.
- **Hierarchy (verified exact):** Clark = Bal. of Clark + Downtown + Strip + North LV + Laughlin + Boulder + Mesquite. Washoe = Bal. + Reno + Sparks + North Shore LT. Elko County = Bal. + Wendover. South Shore LT sits inside Douglas. Never mix a parent with its child in ANOVA/permutation: use `config.LEAF_AREAS` (via `eligible_leaf_areas`, median games >= `MIN_MEDIAN_GAMES`).
- **Derived:** `win_per_game_per_day = Win / Count / days_in_month`; `hold = Win/Drop`. No per-day column in the source.
- **Real dollars:** `data/raw/CPIAUCSL.csv` (FRED CPI-U SA, national, proxy for NV prices). Oct 2025 CPI was never published (shutdown) and is interpolated. `real_win_per_game_per_day` is in `config.CPI_BASE` prices; use it for long-run comparisons and report nominal as a check. In real terms the post-2021 jump is mostly inflation (about 1,700 in 2008, 2025 and 2026).
- Game count fell from about 3,300 (1990s) to about 1,900, so the take per game also moves with supply. Hold % is the supply-robust check.
- Ownership/HHI, LVCVA visitors (and optional FRED `NVUR` unemployment) are not in the repo yet. `data/hhi.py` is ready; ownership mapping is Norman's task. Unemployment only feeds the cross-correlation step, not H1-H3.
- Monthly observations are autocorrelated: use `period_means()` (one value per area/period) for area-level tests.

## Statistical rigor policy (applies to ALL tests, ANOVA, regressions, and time-series models)

No p-value, coefficient, or forecast may be reported until its assumptions have been checked and the result recorded next to it. When a check fails, state the fallback used and report both primary and fallback results.

- **t-tests / ANOVA / permutation:** independence, normality of residuals (Shapiro + Q-Q; at large n lean on CLT), equal variance (Brown-Forsythe; use Welch if violated), outliers (|z|>3; verify data error, report with and without). Monthly observations are autocorrelated, so independence usually fails: say so, attach Ljung-Box, and treat p-values as optimistic (consider block permutation or aggregating to one value per area/period).
- **Permutation test:** state exchangeability; permute at the unit that is exchangeable (area), fixed `config.SEED`, +1 correction in p-value.
- **Post hoc:** correct for multiple comparisons (Tukey after ANOVA, Dunn with Holm after Kruskal-Wallis). H1-H3 are three tests: say whether familywise correction is applied.
- **Regression (any OLS/ARIMAX/ownership or visitors/unemployment on take):** linearity and residual-vs-fitted plot, residual normality, homoskedasticity (Breusch-Pagan), residual autocorrelation (Durbin-Watson/Ljung-Box; use HAC/Newey-West SEs if present), multicollinearity (VIF), influential points (Cook's distance). Regressing non-stationary series on each other is spurious: confirm stationarity (ADF **and** KPSS) or difference/cointegrate first.
- **Time series:** stationarity before ARIMA/SARIMA and cross-correlation; after fitting, residuals must be white (Ljung-Box), roughly normal, and homoskedastic (ARCH-LM). Choose orders from ACF/PACF plus AIC, not the placeholder defaults. Structural-break dates are exploratory unless a formal test is reported.
- Report effect sizes and confidence intervals with every p-value; never infer causation from shock-period or HHI comparisons (confounded, small number of markets).
