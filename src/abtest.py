import math

import numpy as np
from scipy import stats


def z(alpha=0.05, power=0.80):
    return stats.norm.ppf(1 - alpha / 2), stats.norm.ppf(power)


def n_per_arm_mean(sd, delta, alpha=0.05, power=0.80, variance_reduction=0.0):
    """Users (or orders) needed in each arm to detect an absolute difference `delta` in a mean.
    variance_reduction = share of variance removed by a covariate (CUPED), 0 to <1."""
    za, zb = z(alpha, power)
    var = sd**2 * (1 - variance_reduction)
    return math.ceil(2 * (za + zb) ** 2 * var / delta**2)


def mde_mean(sd, n, alpha=0.05, power=0.80, variance_reduction=0.0):
    za, zb = z(alpha, power)
    return (za + zb) * math.sqrt(2 * sd**2 * (1 - variance_reduction) / n)


def n_per_arm_proportion(p0, delta, alpha=0.05, power=0.80):
    za, zb = z(alpha, power)
    p1 = p0 + delta
    pbar = (p0 + p1) / 2
    num = (za * math.sqrt(2 * pbar * (1 - pbar)) + zb * math.sqrt(p0 * (1 - p0) + p1 * (1 - p1))) ** 2
    return math.ceil(num / delta**2)


def duration_days(n_per_arm, eligible_per_day, share_in_test=0.5, min_days=14):
    """Days to collect the sample, never less than two full weeks so every weekday is seen twice."""
    per_day_per_arm = eligible_per_day * share_in_test / 2
    return max(min_days, math.ceil(n_per_arm / per_day_per_arm))


def lognormal_params(mean, cv):
    s2 = math.log(1 + cv**2)
    return math.log(mean) - s2 / 2, math.sqrt(s2)


def simulate_power(mean, cv, effect_rel, n_per_arm, sims=3000, alpha=0.05, seed=3):
    """Share of simulated A/B tests that reach p < alpha. Order values are log-normal, so the data are skewed like real baskets.
    effect_rel = 0 gives the false-positive rate."""
    rng = np.random.default_rng(seed)
    mu, sigma = lognormal_params(mean, cv)
    hits = 0
    for _ in range(sims):
        a = rng.lognormal(mu, sigma, n_per_arm)
        b = rng.lognormal(mu, sigma, n_per_arm) * (1 + effect_rel)
        hits += stats.ttest_ind(b, a, equal_var=False).pvalue < alpha
    return hits / sims
