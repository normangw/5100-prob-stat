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

- `config.py` is the single place for sheet names, areas, shock/period windows, alpha, seed, permutation count. Swap the series here when blackjack-only data arrives.
- `stats/assumptions.py` returns `AssumptionReport` objects; `stats/hypothesis.py` (H1-H3) and `ts/diagnostics.py` run them before computing and return them alongside results. Keep that coupling.

## Data quirks (NGCB workbook, `data/raw/1 - EXTRACT DATA BY AREA - Sept 2026 (external).xlsx`)

- **Not blackjack-only.** Sheets are combined Game & Table (win, drop, counts, per-day). The proposal's blackjack series does not exist yet; the pipeline uses "Win per Game & Table per Day" as a proxy. A data request to NGCB for blackjack-only data is pending. Label any proxy result as such.
- Data starts 1983-04; filter to 2000+ (`config.START`). Areas are Statewide, Clark County, Downtown LV, Strip, North LV, Laughlin, Boulder Strip, Mesquite, Bal. of Clark. **No Reno/Washoe.**
- Header is on row 3 (title row 1; the "Bal. of Clark County" label is split across rows 2-3). Some cells are `'#DIV/0!'` strings (coerce to NaN). Slot Coin-In, Slot Win %, Coin-in per Slot (per Day), Sheet1, Sheet2 are empty. Sheet "Win per Game & Table per Day" has title "WIN PER GAME & TABLE" same as the non-daily sheet: verify scale (daily values are in the hundreds, non-daily in the tens of thousands).
- Ownership/HHI, LVCVA visitor and FRED unemployment data are not in the repo yet. `data/hhi.py` is ready; ownership mapping is Norman's task.
- Monthly series: nominal dollars, not inflation-adjusted. Decide and document deflation before long-run comparisons.

## Statistical rigor policy (applies to ALL tests, ANOVA, regressions, and time-series models)

No p-value, coefficient, or forecast may be reported until its assumptions have been checked and the result recorded next to it. When a check fails, state the fallback used and report both primary and fallback results.

- **t-tests / ANOVA / permutation:** independence, normality of residuals (Shapiro + Q-Q; at large n lean on CLT), equal variance (Brown-Forsythe; use Welch if violated), outliers (|z|>3; verify data error, report with and without). Monthly observations are autocorrelated, so independence usually fails: say so, attach Ljung-Box, and treat p-values as optimistic (consider block permutation or aggregating to one value per area/period).
- **Permutation test:** state exchangeability; permute at the unit that is exchangeable (area), fixed `config.SEED`, +1 correction in p-value.
- **Post hoc:** correct for multiple comparisons (Tukey after ANOVA, Dunn with Holm after Kruskal-Wallis). H1-H3 are three tests: say whether familywise correction is applied.
- **Regression (any OLS/ARIMAX/ownership or visitors/unemployment on take):** linearity and residual-vs-fitted plot, residual normality, homoskedasticity (Breusch-Pagan), residual autocorrelation (Durbin-Watson/Ljung-Box; use HAC/Newey-West SEs if present), multicollinearity (VIF), influential points (Cook's distance). Regressing non-stationary series on each other is spurious: confirm stationarity (ADF **and** KPSS) or difference/cointegrate first.
- **Time series:** stationarity before ARIMA/SARIMA and cross-correlation; after fitting, residuals must be white (Ljung-Box), roughly normal, and homoskedastic (ARCH-LM). Choose orders from ACF/PACF plus AIC, not the placeholder defaults. Structural-break dates are exploratory unless a formal test is reported.
- Report effect sizes and confidence intervals with every p-value; never infer causation from shock-period or HHI comparisons (confounded, small number of markets).
