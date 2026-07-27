"""
Monte Carlo uncertainty analysis (Supplementary Methods S1.3).

Each iteration draws one value for every uncertain parameter, applies it to
all 2,457 plants, and recomputes the national total together with the
concentration metrics. Spearman rank correlations between the drawn parameter
values and the resulting national total rank the parameters by influence.

Parameter treatment
-------------------
eta_AD    triangular(0.40, 0.55, 0.65)
Y_net     uniform multiplier on the process-specific base values, +/-15%
k_CH4     triangular(0.30, 0.35, 0.40)
f_VS      uniform(0.55, 0.80) - decoy; does not enter the methane chain
COD       bootstrap resample (with replacement) from the 2,188 measured
          values, redrawn each iteration for the 269 plants with no
          measurement

The f_VS decoy is included deliberately: its near-zero rank correlation
confirms that the sensitivity ranking reflects the model structure rather
than sampling noise.
"""

import numpy as np
import pandas as pd
from scipy import stats

from wwtp_model import (
    ETA_AD, F_VS, K_CH4, TIER_I_MIN,
    gini, methane_daily, methane_annual_1e4,
)

#: Monte Carlo settings used for the published run.
N_ITERATIONS = 2000
SEED = 25

ETA_AD_TRIANGULAR = (0.40, 0.55, 0.65)   # (left, mode, right)
K_CH4_TRIANGULAR = (0.30, 0.35, 0.40)
YNET_MULTIPLIER_RANGE = (0.85, 1.15)     # +/-15%
F_VS_UNIFORM = (0.55, 0.80)


def run_monte_carlo(plants, n_iter=N_ITERATIONS, seed=SEED, progress=False):
    """Run the Monte Carlo ensemble.

    Parameters
    ----------
    plants : pandas.DataFrame
        Output of :func:`wwtp_model.load_plants`.
    n_iter : int
        Number of iterations.
    seed : int
        Seed for ``numpy.random.default_rng``.
    progress : bool
        Print a progress line every 500 iterations.

    Returns
    -------
    pandas.DataFrame
        One row per iteration with the drawn parameter values and the
        resulting national total (10^8 Nm3/yr), Gini coefficient and Tier-I
        output share (%).
    """
    rng = np.random.default_rng(seed)

    capacity = plants["capacity"].to_numpy(float)
    effluent = plants["effluent_cod"].to_numpy(float)
    ynet_base = plants["ynet"].to_numpy(float)
    cod = plants["cod_measured"].to_numpy(float)
    missing = np.isnan(cod)
    measured_pool = cod[~missing]
    is_tier_i = capacity >= TIER_I_MIN

    records = []
    for i in range(n_iter):
        eta = float(rng.triangular(*ETA_AD_TRIANGULAR))
        k = float(rng.triangular(*K_CH4_TRIANGULAR))
        ymult = float(rng.uniform(*YNET_MULTIPLIER_RANGE))
        fvs = float(rng.uniform(*F_VS_UNIFORM))

        cod_iter = cod.copy()
        draw = rng.choice(measured_pool, size=int(missing.sum()), replace=True)
        cod_iter[missing] = draw

        daily = methane_daily(capacity, cod_iter, effluent,
                              ynet_base * ymult, eta_ad=eta, k_ch4=k)
        annual = methane_annual_1e4(daily)
        total = annual.sum() * 1e4 / 1e8

        records.append({
            "iteration": i,
            "eta_AD": eta,
            "Y_net_multiplier": ymult,
            "k_CH4": k,
            "COD_mean_imputed": float(draw.mean()),
            "VSS_DS": fvs,
            "total_1e8_Nm3_yr": total,
            "gini": gini(annual),
            "tier_I_share_pct": 100 * annual[is_tier_i].sum() / annual.sum(),
        })

        if progress and (i + 1) % 500 == 0:
            print(f"    ... {i + 1}/{n_iter} iterations")

    return pd.DataFrame(records)


def summarise(mc):
    """Median and 95% interval for each Monte Carlo indicator."""
    rows = []
    for col, label in [("total_1e8_Nm3_yr", "National total (1e8 Nm3/yr)"),
                       ("gini", "Gini coefficient"),
                       ("tier_I_share_pct", "Tier-I share (%)")]:
        v = mc[col]
        lo, med, hi = np.percentile(v, [2.5, 50, 97.5])
        rows.append({
            "indicator": label,
            "p2.5": lo,
            "median": med,
            "p97.5": hi,
            "relative_CI_width_pct": 100 * (hi - lo) / med,
        })
    return pd.DataFrame(rows)


def sensitivity(mc, target="total_1e8_Nm3_yr"):
    """Absolute Spearman rank correlation of each parameter with the target."""
    params = [
        ("eta_AD", "eta_AD"),
        ("Y_net_multiplier", "Y_net"),
        ("k_CH4", "k_CH4"),
        ("COD_mean_imputed", "COD"),
        ("VSS_DS", "VSS/DS"),
    ]
    rows = []
    for col, label in params:
        rho, p = stats.spearmanr(mc[col], mc[target])
        rows.append({
            "parameter": label,
            "abs_spearman": abs(rho),
            "spearman": rho,
            "p_value": p,
        })
    return (pd.DataFrame(rows)
            .sort_values("abs_spearman", ascending=False)
            .reset_index(drop=True))
