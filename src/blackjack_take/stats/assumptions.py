"""Assumption checks that gate every test/model. Mirrors docs/references/stats-test-cheatsheet.html §3."""
from dataclasses import dataclass, field

import numpy as np
from scipy import stats

from blackjack_take import config


@dataclass
class Check:
    name: str
    statistic: float
    p_value: float | None
    passed: bool
    note: str = ""


@dataclass
class AssumptionReport:
    checks: list[Check] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def failed(self) -> list[str]:
        return [c.name for c in self.checks if not c.passed]

    def add(self, check: Check) -> "AssumptionReport":
        self.checks.append(check)
        return self

    def summary(self) -> str:
        return "\n".join(
            f"[{'PASS' if c.passed else 'FAIL'}] {c.name}: stat={c.statistic:.4g}"
            + (f", p={c.p_value:.4g}" if c.p_value is not None else "")
            + (f" ({c.note})" if c.note else "")
            for c in self.checks
        )


def normality(x, label: str = "values", alpha: float = config.ALPHA) -> Check:
    """Shapiro-Wilk. Low power at small n and oversensitive at large n: also inspect a Q-Q plot."""
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    n = len(x)
    stat, p = stats.shapiro(x[:5000])
    note = "n>5000 truncated; rely on Q-Q + CLT" if n > 5000 else ("large n: CLT usually ok" if n > 200 else "")
    return Check(f"normality({label})", float(stat), float(p), p > alpha, note)


def equal_variance(groups, alpha: float = config.ALPHA) -> Check:
    """Brown-Forsythe (median-centred Levene): robust to non-normality."""
    gs = [np.asarray(g, float)[~np.isnan(g)] for g in groups]
    stat, p = stats.levene(*gs, center="median")
    return Check("equal_variance(brown-forsythe)", float(stat), float(p), p > alpha)


def outliers(x, z: float = 3.0) -> Check:
    """Flag |standardised value| > z. Passing means none flagged; check for data errors first."""
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    zs = np.abs((x - x.mean()) / x.std(ddof=1))
    k = int((zs > z).sum())
    return Check("outliers(|z|>3)", float(k), None, k == 0, f"{k} flagged of {len(x)}")


def independence_ljung_box(resid, lags: int = 12, alpha: float = config.ALPHA) -> Check:
    """Ljung-Box on residuals. Monthly series are autocorrelated: failing here means the
    iid-based tests (t, ANOVA, permutation of labels) are anti-conservative."""
    from statsmodels.stats.diagnostic import acorr_ljungbox

    r = np.asarray(resid, float)
    r = r[~np.isnan(r)]
    out = acorr_ljungbox(r, lags=[min(lags, len(r) // 2 - 1)])
    return Check(
        "independence(ljung-box)", float(out["lb_stat"].iloc[0]), float(out["lb_pvalue"].iloc[0]),
        float(out["lb_pvalue"].iloc[0]) > alpha,
    )


def check_two_groups(a, b) -> AssumptionReport:
    rep = AssumptionReport()
    rep.add(normality(a, "group_a")).add(normality(b, "group_b"))
    rep.add(equal_variance([a, b])).add(outliers(a)).add(outliers(b))
    return rep


def check_k_groups(groups, labels=None) -> AssumptionReport:
    rep = AssumptionReport()
    for i, g in enumerate(groups):
        rep.add(normality(g, str(labels[i]) if labels else f"group_{i}"))
        rep.add(outliers(g))
    rep.add(equal_variance(groups))
    return rep
