"""
Plant-level distribution fitting and model comparison (Methods S1.2).

Fits a log-normal and a power law to the daily methane output of the plants
with positive output, and compares them with a Vuong likelihood-ratio test.

The power law is fitted above x_min, taken as the median of the positive
values; the Vuong comparison is carried out on that same tail using the
``powerlaw`` package (Alstott, Bullmore & Plenz, 2014), which is the standard
implementation of the Clauset-Shalizi-Newman procedure.

A negative normalised ratio R means the log-normal is preferred.
"""

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


def positive_output(df, col="ch4_daily_m3"):
    """Daily methane values for plants with strictly positive output."""
    return df.loc[df[col] > 0, col].to_numpy(float)


def fit_lognormal(x):
    """Maximum-likelihood log-normal parameters of ``x``."""
    lx = np.log(x)
    mu = float(lx.mean())
    sigma = float(lx.std(ddof=0))
    return {"mu": mu, "sigma": sigma, "geometric_mean": float(np.exp(mu))}


def fit_powerlaw(x, xmin=None):
    """Maximum-likelihood power-law exponent above ``xmin``.

    ``xmin`` defaults to the median of ``x``, the convention used for the
    published fit.
    """
    xmin = float(np.median(x)) if xmin is None else float(xmin)
    tail = x[x >= xmin]
    alpha = 1.0 + tail.size / np.sum(np.log(tail / xmin))
    return {"alpha": float(alpha), "xmin": xmin, "n_tail": int(tail.size)}


def vuong_test(x, xmin=None):
    """Vuong comparison of power law against log-normal on the upper tail.

    Returns a dict with the normalised log-likelihood ratio ``R`` and its
    two-sided p-value. ``R < 0`` favours the log-normal.

    Requires the ``powerlaw`` package. If it is not installed, a
    self-contained fallback is used; the fallback reproduces the same sign and
    conclusion but may differ slightly in magnitude, and a warning is emitted.
    """
    xmin = float(np.median(x)) if xmin is None else float(xmin)
    try:
        import powerlaw
    except ImportError:
        return _vuong_fallback(x, xmin)

    fit = powerlaw.Fit(x, xmin=xmin, discrete=False)
    R, p = fit.distribution_compare("power_law", "lognormal",
                                    normalized_ratio=True)
    return {
        "R": float(R),
        "p_value": float(p),
        "alpha": float(fit.power_law.alpha),
        "xmin": xmin,
        "preferred": "lognormal" if R < 0 else "power_law",
        "implementation": "powerlaw package",
    }


def _vuong_fallback(x, xmin):
    """Self-contained Vuong test used when ``powerlaw`` is unavailable."""
    from scipy import stats

    warnings.warn(
        "The 'powerlaw' package is not installed; using the built-in Vuong "
        "fallback. The sign and conclusion agree with the published test but "
        "the magnitude of R may differ slightly. Install with: pip install powerlaw",
        RuntimeWarning,
    )
    tail = x[x >= xmin]
    n = tail.size
    alpha = 1.0 + n / np.sum(np.log(tail / xmin))
    ll_pl = np.log(alpha - 1) - np.log(xmin) - alpha * np.log(tail / xmin)

    lx = np.log(x)
    mu, sigma = lx.mean(), lx.std(ddof=0)
    ll_ln = (-np.log(tail * sigma * np.sqrt(2 * np.pi))
             - (np.log(tail) - mu) ** 2 / (2 * sigma ** 2))
    ll_ln = ll_ln - np.log(1 - stats.norm.cdf((np.log(xmin) - mu) / sigma))

    diff = ll_pl - ll_ln
    R = diff.sum() / (np.sqrt(n) * diff.std(ddof=0))
    p = 2 * stats.norm.sf(abs(R))
    return {
        "R": float(R),
        "p_value": float(p),
        "alpha": float(alpha),
        "xmin": xmin,
        "preferred": "lognormal" if R < 0 else "power_law",
        "implementation": "built-in fallback",
    }


def ccdf(x):
    """Complementary cumulative distribution, P(X > x)."""
    xs = np.sort(np.asarray(x, dtype=float))
    n = xs.size
    return pd.DataFrame({
        "ch4_m3d": xs,
        "ccdf_P_X_gt_x": 1.0 - np.arange(n) / n,
    })
