"""
Tiered recovery scenarios and independent validation.

Section 2.4 / 3.5 convert theoretical potential into a recoverable amount by
applying three discount factors: tier-specific anaerobic-digestion coverage,
a digester operating rate, and a biogas utilisation rate. Methods S1.7
examines how the recoverable total and the Tier-I share respond across the
plausible ranges of those factors.

Methods S1.6 validates the size dependence that underlies the concentration
result against the independent measurement campaign of Sun et al. (2026).
"""

import itertools
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from wwtp_model import DATA, YNET, gini

#: Deployment scenarios (Section 2.4). ``ad_coverage`` is the share of each
#: tier's plants assumed to operate anaerobic digestion.
SCENARIOS = {
    "Conservative": {
        "ad_coverage": {"I": 0.50, "II": 0.20, "III": 0.05},
        "operating_rate": 0.70,
        "biogas_utilisation": 0.40,
    },
    "Mid": {
        "ad_coverage": {"I": 0.65, "II": 0.35, "III": 0.15},
        "operating_rate": 0.80,
        "biogas_utilisation": 0.60,
    },
    "Optimistic": {
        "ad_coverage": {"I": 0.80, "II": 0.50, "III": 0.30},
        "operating_rate": 0.90,
        "biogas_utilisation": 0.80,
    },
}


def recoverable_by_tier(df, ad_coverage, operating_rate, biogas_utilisation,
                        value_col="ch4_annual_1e4_m3"):
    """Recoverable methane per tier, in the units of ``value_col``."""
    theoretical = df.groupby("tier")[value_col].sum()
    return {
        tier: theoretical.get(tier, 0.0) * ad_coverage[tier]
              * operating_rate * biogas_utilisation
        for tier in ["I", "II", "III"]
    }


def scenario_table(df, value_col="ch4_annual_1e4_m3"):
    """Table 2: recoverable methane and tier composition by scenario.

    The recovery rate is expressed relative to the deterministic theoretical
    total, which is the denominator used throughout the paper.
    """
    total_theoretical = df[value_col].sum()
    rows = []
    for name, cfg in SCENARIOS.items():
        rec = recoverable_by_tier(df, **cfg, value_col=value_col)
        rtot = sum(rec.values())
        rows.append({
            "scenario": name,
            "recoverable_1e8_Nm3_yr": rtot * 1e4 / 1e8,
            "recovery_rate_pct": 100 * rtot / total_theoretical,
            "tier_I_pct": 100 * rec["I"] / rtot,
            "tier_II_pct": 100 * rec["II"] / rtot,
            "tier_III_pct": 100 * rec["III"] / rtot,
        })
    return pd.DataFrame(rows)


#: Coverage levels used for the sensitivity analyses (Methods S1.7). Each is
#: the mid value +/- 15 percentage points, with Tier III floored at 0.05 (the
#: Conservative-scenario value) rather than zero, since some digestion capacity
#: exists at small plants in every plausible deployment.
COVERAGE_LEVELS = {
    "I": [0.50, 0.65, 0.80],
    "II": [0.20, 0.35, 0.50],
    "III": [0.05, 0.15, 0.30],
}

#: Tier-II coverage is held at its mid value for the Table S6 grid.
TABLE_S6_TIER_II = 0.35


def coverage_sensitivity(df, value_col="ch4_annual_1e4_m3"):
    """Table S6: Tier-I share of recoverable methane across the coverage grid.

    Tier-II coverage is fixed at 0.35; Tier-I coverage varies down the rows
    and Tier-III coverage across the columns. The operating rate and biogas
    utilisation are applied uniformly across tiers, so they cancel exactly in
    the Tier-I share and do not appear here.

    Returns
    -------
    pandas.DataFrame
        Matrix of Tier-I shares (%), rows indexed by Tier-I coverage and
        columns by Tier-III coverage.
    """
    theoretical = df.groupby("tier")[value_col].sum()
    matrix = {}
    for cIII in COVERAGE_LEVELS["III"]:
        col = {}
        for cI in COVERAGE_LEVELS["I"]:
            cov = {"I": cI, "II": TABLE_S6_TIER_II, "III": cIII}
            rec = {t: theoretical.get(t, 0.0) * cov[t] for t in ["I", "II", "III"]}
            col[cI] = 100 * rec["I"] / sum(rec.values())
        matrix[cIII] = col
    out = pd.DataFrame(matrix)
    out.index.name = "tier_I_coverage"
    out.columns.name = "tier_III_coverage"
    return out


def full_factorial(df, value_col="ch4_annual_1e4_m3"):
    """Methods S1.7: three-level factorial over all five conversion inputs."""
    cov_levels = COVERAGE_LEVELS
    op_levels = [0.70, 0.80, 0.90]
    bu_levels = [0.40, 0.60, 0.80]
    theoretical = df.groupby("tier")[value_col].sum()
    total_theoretical = df[value_col].sum()

    rows = []
    for cI, cII, cIII, op, bu in itertools.product(
            cov_levels["I"], cov_levels["II"], cov_levels["III"],
            op_levels, bu_levels):
        cov = {"I": cI, "II": cII, "III": cIII}
        rec = {t: theoretical.get(t, 0.0) * cov[t] * op * bu
               for t in ["I", "II", "III"]}
        rtot = sum(rec.values())
        rows.append({
            "coverage_I": cI, "coverage_II": cII, "coverage_III": cIII,
            "operating_rate": op, "biogas_utilisation": bu,
            "recoverable_1e8_Nm3_yr": rtot * 1e4 / 1e8,
            "recovery_rate_pct": 100 * rtot / total_theoretical,
            "tier_I_share_pct": 100 * rec["I"] / rtot,
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Independent validation against Sun et al. (2026) - Methods S1.6
# --------------------------------------------------------------------------

#: Process-averaged influent COD reported by Sun et al. (2026), mg/L.
SUN_PROCESS_COD = {"AAO": 194.0, "OD": 134.0, "SBR": 160.0, "Other": 160.0}
SUN_COD_DEFAULT = 160.0


#: Guidance printed if the Sun et al. tables have been removed from the
#: distribution (they carry a NonCommercial licence; see LICENSE.md).
SUN_DATA_MISSING_HELP = """\
    The Sun et al. (2026) tables are not present in data/, so the independent
    validation of Methods S1.6 was skipped. Every other result is unaffected.

    These two files carry a CC BY-NC 4.0 licence and may have been removed
    before deposit. To restore them, download the Supplementary Materials of

      Sun, C. et al. (2026). Science Advances 12 (15), eaec0536.
      https://doi.org/10.1126/sciadv.aec0536

    and transcribe Table S2 and Table S3 into data/ as:

      sun_S2_capacity.csv   columns: site, capacity_1e3_m3d, process
      sun_S3_periods.csv    columns: site, ER_kg_h

    The 'site' values must match between the two files."""


def sun_data_available(capacity_path=None, periods_path=None):
    """Whether both Sun et al. input tables are present."""
    capacity_path = Path(capacity_path) if capacity_path else DATA / "sun_S2_capacity.csv"
    periods_path = Path(periods_path) if periods_path else DATA / "sun_S3_periods.csv"
    return capacity_path.exists() and periods_path.exists()


def load_sun_dataset(capacity_path=None, periods_path=None):
    """Load the Sun et al. capacity and emission-rate tables.

    Returns one row per plant with its design capacity, process, mean measured
    emission rate and the number of observational periods.

    Raises
    ------
    FileNotFoundError
        If either table is absent. See ``SUN_DATA_MISSING_HELP``.
    """
    capacity_path = Path(capacity_path) if capacity_path else DATA / "sun_S2_capacity.csv"
    periods_path = Path(periods_path) if periods_path else DATA / "sun_S3_periods.csv"
    for p in (capacity_path, periods_path):
        if not p.exists():
            raise FileNotFoundError(p)

    cap = pd.read_csv(capacity_path, encoding="utf-8-sig")
    per = pd.read_csv(periods_path, encoding="utf-8-sig")

    agg = per.groupby("site")["ER_kg_h"].agg(["mean", "median", "count"])
    agg.columns = ["ER_mean_kg_h", "ER_median_kg_h", "n_periods"]

    df = cap.merge(agg, left_on="site", right_index=True, how="inner")
    df["capacity_m3d"] = df["capacity_1e3_m3d"].astype(float) * 1e3
    df["tier"] = np.where(df["capacity_m3d"] >= 5e4, "I",
                          np.where(df["capacity_m3d"] >= 2e4, "II", "III"))
    return df


def predicted_potential(df):
    """Model-predicted potential for the Sun plants, using Sun's process COD.

    Applies the same yield chain as the national model but substitutes Sun's
    process-averaged influent COD, so the comparison tests the size dependence
    rather than the absolute magnitude.
    """
    proc = df["process"].astype(str).str.strip()
    cod_in = proc.map(SUN_PROCESS_COD).fillna(SUN_COD_DEFAULT)
    ynet = proc.map(YNET).fillna(0.35)
    delta = np.clip(df["capacity_m3d"] * (cod_in - 60.0) * 1e-3, 0, None)
    return delta * ynet * 0.55 * 0.35


def validation_stats(df):
    """Rank-correlation validation statistics reported in Methods S1.6."""
    cap = df["capacity_m3d"].to_numpy(float)
    er = df["ER_mean_kg_h"].to_numpy(float)

    rho_cap, p_cap = stats.spearmanr(cap, er)
    tau, p_tau = stats.kendalltau(cap, er)
    rho_med, _ = stats.spearmanr(cap, df["ER_median_kg_h"])

    rep = df[df["n_periods"] >= 2]
    rho_rep, p_rep = stats.spearmanr(rep["capacity_m3d"], rep["ER_mean_kg_h"])

    pred = predicted_potential(df)
    rho_pred, p_pred = stats.spearmanr(pred, er)

    ok = (cap > 0) & (er > 0)
    slope, intercept, r, p_fit, se = stats.linregress(
        np.log10(cap[ok]), np.log10(er[ok])
    )

    top30 = np.sort(er)[::-1][:int(np.ceil(0.30 * er.size))].sum() / er.sum()

    return {
        "n_plants": int(df.shape[0]),
        "spearman_capacity_vs_emission": rho_cap,
        "p_capacity": p_cap,
        "kendall_tau": tau,
        "p_kendall": p_tau,
        "spearman_using_medians": rho_med,
        "n_repeat_plants": int(rep.shape[0]),
        "spearman_repeat_only": rho_rep,
        "p_repeat": p_rep,
        "spearman_predicted_vs_measured": rho_pred,
        "p_predicted": p_pred,
        "loglog_slope": slope,
        "loglog_r2": r ** 2,
        "gini_measured_emission": gini(er),
        "top30pct_share": top30,
        "pct_at_or_above_5e4": 100 * (cap >= 5e4).mean(),
        "median_capacity_m3d": float(np.median(cap)),
    }
