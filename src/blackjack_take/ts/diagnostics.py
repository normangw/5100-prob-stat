"""Time-series checks. Stationarity must be established before ARIMA or any regression on levels."""

import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import adfuller, kpss

from blackjack_take import config
from blackjack_take.stats.assumptions import AssumptionReport, Check, normality


def stationarity(y: pd.Series, alpha: float = config.ALPHA) -> AssumptionReport:
    """ADF (H0: unit root) and KPSS (H0: stationary). Agreement of both is the strong result."""
    y = y.dropna()
    adf_p = adfuller(y, autolag="AIC")[1]
    kpss_p = kpss(y, regression="c", nlags="auto")[1]
    rep = AssumptionReport()
    rep.add(
        Check("stationary(adf)", float(adfuller(y, autolag="AIC")[0]), float(adf_p), adf_p < alpha)
    )
    rep.add(
        Check(
            "stationary(kpss)",
            float(kpss(y, regression="c", nlags="auto")[0]),
            float(kpss_p),
            kpss_p > alpha,
            "p is clipped to [0.01, 0.1] by statsmodels",
        )
    )
    return rep


def stl_decompose(y: pd.Series, period: int = 12):
    return STL(y.dropna(), period=period, robust=True).fit()


def residual_diagnostics(resid, lags: int = 24, alpha: float = config.ALPHA) -> AssumptionReport:
    """Whiteness (Ljung-Box), normality (Shapiro) and constant variance (ARCH-LM) of residuals."""
    r = pd.Series(resid).dropna()
    lb = acorr_ljungbox(r, lags=[lags])
    arch_p = het_arch(r)[1]
    rep = AssumptionReport()
    rep.add(
        Check(
            "residual_whiteness(ljung-box)",
            float(lb["lb_stat"].iloc[0]),
            float(lb["lb_pvalue"].iloc[0]),
            float(lb["lb_pvalue"].iloc[0]) > alpha,
        )
    )
    rep.add(normality(r, "residuals"))
    rep.add(
        Check(
            "residual_homoskedasticity(arch-lm)",
            float(het_arch(r)[0]),
            float(arch_p),
            arch_p > alpha,
        )
    )
    return rep


def fit_sarima_pre_shock(y: pd.Series, cutoff: str, order=(1, 1, 1), seasonal=(0, 1, 1, 12)):
    """Fit on data before `cutoff`; return (fit, forecast over the remaining months, diagnostics).

    Order is a placeholder: choose via ACF/PACF + AIC after stationarity checks, and re-run
    residual_diagnostics on the chosen model before interpreting forecast gaps.
    """
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    train, test = y[y.index < cutoff].dropna(), y[y.index >= cutoff]
    fit = SARIMAX(train, order=order, seasonal_order=seasonal).fit(disp=False)
    fc = fit.get_forecast(len(test)).summary_frame()
    return fit, fc, residual_diagnostics(fit.resid.iloc[max(order[1], seasonal[1] * seasonal[3]) :])


def cross_correlation(x: pd.Series, y: pd.Series, max_lag: int = 12) -> pd.Series:
    """corr(x_{t-k}, y_t). Inputs must be stationary (difference first) or results are spurious."""
    d = pd.concat([x, y], axis=1).dropna()
    return pd.Series(
        {k: d.iloc[:, 0].shift(k).corr(d.iloc[:, 1]) for k in range(max_lag + 1)}, name="ccf"
    ).rename_axis("lag")


def detect_breaks(y: pd.Series, n_bkps: int = 2):
    import ruptures as rpt

    algo = rpt.Binseg(model="l2").fit(np.asarray(y.dropna(), float))
    idx = algo.predict(n_bkps=n_bkps)[:-1]
    return [y.dropna().index[i] for i in idx]
