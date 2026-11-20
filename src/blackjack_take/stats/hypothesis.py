"""H1-H3. Every function runs assumption checks first and returns them with the result."""

from dataclasses import dataclass

import numpy as np
from scipy import stats

from blackjack_take import config
from blackjack_take.stats import assumptions as A


@dataclass
class TestResult:
    hypothesis: str
    primary: str  # test chosen after checking assumptions
    statistic: float
    p_value: float
    effect_size: float
    effect_name: str
    robustness: dict  # fallback/companion test -> p-value
    assumptions: A.AssumptionReport
    n: dict


def h1_two_groups(shock, other) -> TestResult:
    """H1: mean win per game per day lower in shock periods. One-sided Welch t; Wilcoxon check.

    Caveat: consecutive months are autocorrelated, so independence is rarely met. The
    Ljung-Box flag on each series is attached; treat p-values as optimistic if it fails.
    """
    shock, other = np.asarray(shock, float), np.asarray(other, float)
    rep = A.check_two_groups(shock, other)
    rep.add(A.independence_ljung_box(shock)).add(A.independence_ljung_box(other))
    welch = stats.ttest_ind(shock, other, equal_var=False, alternative="less")
    mw = stats.mannwhitneyu(shock, other, alternative="less")
    sp = np.sqrt((shock.var(ddof=1) + other.var(ddof=1)) / 2)
    d = (shock.mean() - other.mean()) / sp  # Cohen's d (pooled-SD form)
    normal_ok = (
        all(c.passed for c in rep.checks if c.name.startswith("normality"))
        or min(len(shock), len(other)) > 200
    )
    primary = "welch_t" if normal_ok else "mann_whitney_u"
    stat, p = (welch.statistic, welch.pvalue) if normal_ok else (mw.statistic, mw.pvalue)
    return TestResult(
        "H1",
        primary,
        float(stat),
        float(p),
        float(d),
        "cohen_d",
        {"welch_t": float(welch.pvalue), "mann_whitney_u": float(mw.pvalue)},
        rep,
        {"shock": len(shock), "other": len(other)},
    )


def h2_permutation(high, low, n_perm: int = config.N_PERM, seed: int = config.SEED) -> TestResult:
    """H2: above-median-HHI areas have higher win per game. Permutation test on mean difference.

    Exchangeability is the key assumption; with area-month panels, permute at the area level
    (pass one value per area) or use block permutation, not raw months.
    """
    high, low = np.asarray(high, float), np.asarray(low, float)
    rep = A.check_two_groups(high, low)
    obs = high.mean() - low.mean()
    pooled = np.concatenate([high, low])
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n_perm):
        rng.shuffle(pooled)
        cnt += (pooled[: len(high)].mean() - pooled[len(high) :].mean()) >= obs
    p = (cnt + 1) / (n_perm + 1)
    sp = np.sqrt((high.var(ddof=1) + low.var(ddof=1)) / 2)
    return TestResult(
        "H2",
        "permutation_mean_diff",
        float(obs),
        float(p),
        float(obs / sp),
        "cohen_d",
        {},
        rep,
        {"high": len(high), "low": len(low)},
    )


def h3_anova(groups: dict[str, np.ndarray]) -> TestResult:
    """H3: win per game differs across areas. ANOVA primary only if checks pass; otherwise
    Welch ANOVA (unequal variance) or Kruskal-Wallis (non-normal). Post hoc not run here."""
    labels = list(groups)
    gs = [np.asarray(groups[k], float) for k in labels]
    rep = A.check_k_groups(gs, labels)
    f = stats.f_oneway(*gs)
    kw = stats.kruskal(*gs)
    allx = np.concatenate(gs)
    ssb = sum(len(g) * (g.mean() - allx.mean()) ** 2 for g in gs)
    eta2 = ssb / ((allx - allx.mean()) ** 2).sum()
    norm_ok = all(c.passed for c in rep.checks if c.name.startswith("normality"))
    var_ok = next(c for c in rep.checks if c.name.startswith("equal_variance")).passed
    if norm_ok and var_ok:
        primary, stat, p = "one_way_anova", f.statistic, f.pvalue
    else:
        primary, stat, p = "kruskal_wallis", kw.statistic, kw.pvalue
    return TestResult(
        "H3",
        primary,
        float(stat),
        float(p),
        float(eta2),
        "eta_squared",
        {"one_way_anova": float(f.pvalue), "kruskal_wallis": float(kw.pvalue)},
        rep,
        {k: len(v) for k, v in groups.items()},
    )
