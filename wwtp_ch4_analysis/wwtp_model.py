"""
Core full-chain methane-yield model for China's above-ground municipal WWTPs.

Implements Supplementary Methods S1.1 (eight-step yield chain), the tier
definitions of Section 2.3, and the concentration metrics of Section 2.4.

All parameter values are those reported in Table S1 of the Supplementary
Information. Nothing here depends on files outside this package.

Reference
---------
Xiong, C., Liu, Y., Tang, X., Li, Q. Concentrated distribution and targeted
deployment of methane resources in China's municipal wastewater treatment
plants. Resources, Conservation & Recycling (submitted).
"""

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE / "outputs"

# --------------------------------------------------------------------------
# Model parameters (Table S1)
# --------------------------------------------------------------------------

#: Net sludge yield Y_net by process category (kg VSS per kg COD removed).
#: Table S1 groups these as AAO/AO 0.35-0.40, MBR 0.25-0.30, biofilm 0.25;
#: the values below are the specific figures used for the published run.
YNET = {
    "AAO": 0.40,
    "AO": 0.40,
    "Others": 0.40,
    "SBR": 0.38,
    "OD": 0.35,
    "MBR": 0.30,
    "Biofilm": 0.25,
}

#: Design effluent COD by discharge grade under GB 18918-2002 (mg/L), Step 3.
EFFLUENT_COD = {
    "Above Class 1A": 30,
    "Class 1A": 50,
    "Class 1B": 60,
    "Class 2 and below": 100,
    "Others": 60,
}
EFFLUENT_COD_DEFAULT = 60  # where the discharge grade is unspecified

ETA_AD = 0.55        # VS destruction fraction in AD (35 C, SRT 20 d)
K_CH4 = 0.35         # methane yield coefficient, m3 per kg VS destroyed
F_VS = 0.65          # VSS/DS ratio; reporting only, does not affect CH4
DAYS_PER_YEAR = 365

#: Constant fill used for the 269 plants without a measured influent COD in
#: the deterministic (point) estimate. This is the rounded mean of the 2,188
#: measured values (252.3 mg/L). The Monte Carlo replaces this constant with
#: bootstrap resampling from the measured distribution (Methods S1.3).
COD_FILL_DETERMINISTIC = 252.0

#: Tier thresholds on design capacity, 10^4 m3/d (Section 2.3, HJ-BAT-002).
TIER_I_MIN = 5.0
TIER_II_MIN = 2.0

#: Unit conversions used in reporting.
CH4_DENSITY_KG_PER_NM3 = 0.716
CH4_LHV_MJ_PER_NM3 = 35.9
STANDARD_COAL_MJ_PER_KG = 29.27

# Source-file column names (Chinese headers in the published dataset).
_COL_CAPACITY = "规模_污水处理厂(104m3/d)"
_COL_COD = "污水中化学需氧量的年平均浓度(mg/L)"
_COL_STANDARD = "污水处理排放标准"
_COL_PROCESS = "工艺类别"
_COL_PROV = "省份"
_COL_CITY = "城市"
_COL_LON = "经度"
_COL_LAT = "维度"


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------

def load_plants(path=None):
    """Load and filter the above-ground WWTP records.

    Reads the ``A-WWTP`` sheet of the published dataset (Zhou et al., 2024),
    drops records without a usable design capacity, and returns a tidy frame.

    Returns
    -------
    pandas.DataFrame
        One row per plant with columns ``prov, city, lon, lat, capacity,
        process, cod_measured, effluent_cod, ynet, tier``. ``capacity`` is in
        10^4 m3/d; ``cod_measured`` is NaN where no measurement exists.
    """
    path = Path(path) if path else DATA / "中国污水处理厂数据集.xlsx"
    raw = pd.read_excel(path, sheet_name="A-WWTP")
    raw.columns = [c.strip() for c in raw.columns]

    capacity = pd.to_numeric(raw[_COL_CAPACITY], errors="coerce")
    keep = capacity.notna()
    df = raw.loc[keep].copy()

    out = pd.DataFrame({
        "prov": df[_COL_PROV].astype(str).str.strip(),
        "city": df[_COL_CITY].astype(str).str.strip(),
        "lon": pd.to_numeric(df[_COL_LON], errors="coerce"),
        "lat": pd.to_numeric(df[_COL_LAT], errors="coerce"),
        "capacity": capacity.loc[keep].astype(float),
        "process": df[_COL_PROCESS].astype(str).str.strip(),
        "cod_measured": pd.to_numeric(df[_COL_COD], errors="coerce"),
    })
    out["effluent_cod"] = (
        df[_COL_STANDARD].map(EFFLUENT_COD).fillna(EFFLUENT_COD_DEFAULT).values
    )
    out["ynet"] = out["process"].map(YNET)
    if out["ynet"].isna().any():
        missing = sorted(out.loc[out["ynet"].isna(), "process"].unique())
        raise ValueError(f"No Y_net defined for process categories: {missing}")
    out["tier"] = assign_tier(out["capacity"])
    return out.reset_index(drop=True)


def assign_tier(capacity):
    """Assign deployment tier from design capacity (10^4 m3/d)."""
    capacity = np.asarray(capacity, dtype=float)
    return np.where(
        capacity >= TIER_I_MIN, "I",
        np.where(capacity >= TIER_II_MIN, "II", "III"),
    )


# --------------------------------------------------------------------------
# Full-chain yield model (Methods S1.1, Steps 1-8)
# --------------------------------------------------------------------------

def methane_daily(capacity, cod_in, effluent_cod, ynet,
                  eta_ad=ETA_AD, k_ch4=K_CH4):
    """Daily methane potential per plant, m3/d (Steps 1, 4, 5, 7).

    Parameters
    ----------
    capacity : array_like
        Design capacity, 10^4 m3/d.
    cod_in, effluent_cod : array_like
        Influent and design effluent COD, mg/L.
    ynet : array_like
        Net sludge yield, kg VSS per kg COD removed.
    eta_ad, k_ch4 : float or array_like
        VS destruction fraction and methane yield coefficient.

    Notes
    -----
    COD removal is floored at zero where influent COD falls below the design
    effluent value (Step 4). Step 6 (dry solids) is reporting-only and does
    not enter the methane calculation, so it is omitted here.
    """
    flow = np.asarray(capacity, dtype=float) * 1e4                  # Step 1
    delta_cod = np.clip(
        flow * (np.asarray(cod_in, dtype=float)
                - np.asarray(effluent_cod, dtype=float)) * 1e-3,
        0.0, None,
    )                                                                # Step 4
    vss = delta_cod * np.asarray(ynet, dtype=float)                  # Step 5
    return vss * eta_ad * k_ch4                                      # Step 7


def methane_annual_1e4(daily_m3):
    """Convert daily methane (m3/d) to 10^4 m3/yr (Step 8)."""
    return np.asarray(daily_m3, dtype=float) * DAYS_PER_YEAR / 1e4


def deterministic_estimate(plants, cod_fill=COD_FILL_DETERMINISTIC):
    """Run the deterministic point estimate.

    Missing influent COD is filled with a single constant (the rounded mean of
    the measured values). Returns the input frame with ``cod_used``,
    ``ch4_daily_m3`` and ``ch4_annual_1e4_m3`` columns added.
    """
    df = plants.copy()
    df["cod_used"] = df["cod_measured"].fillna(cod_fill)
    df["ch4_daily_m3"] = methane_daily(
        df["capacity"], df["cod_used"], df["effluent_cod"], df["ynet"]
    )
    df["ch4_annual_1e4_m3"] = methane_annual_1e4(df["ch4_daily_m3"])
    return df


# --------------------------------------------------------------------------
# Concentration metrics (Section 2.4)
# --------------------------------------------------------------------------

def gini(values):
    """Gini coefficient of a non-negative distribution."""
    x = np.sort(np.asarray(values, dtype=float))
    if x.size == 0 or x.sum() == 0:
        return np.nan
    n = x.size
    cum = np.cumsum(x)
    return (n + 1 - 2 * cum.sum() / cum[-1]) / n


def lorenz_curve(values):
    """Lorenz curve as (cumulative plant share, cumulative output share).

    Both arrays start at the origin and have ``len(values) + 1`` points.
    """
    x = np.sort(np.asarray(values, dtype=float))
    n = x.size
    cum = np.concatenate([[0.0], np.cumsum(x)])
    return np.arange(n + 1) / n, cum / cum[-1]


def top_share(values, fraction):
    """Share of the total held by the largest ``fraction`` of units."""
    x = np.sort(np.asarray(values, dtype=float))[::-1]
    k = int(round(fraction * x.size))
    return x[:k].sum() / x.sum()


def tier_summary(df, value_col="ch4_annual_1e4_m3"):
    """Plant counts, mean capacity and output share by tier."""
    total = df[value_col].sum()
    rows = []
    for tier in ["I", "II", "III"]:
        m = df["tier"] == tier
        rows.append({
            "tier": tier,
            "plants": int(m.sum()),
            "plant_share_pct": 100 * m.sum() / len(df),
            "mean_capacity_1e4_m3_d": df.loc[m, "capacity"].mean(),
            "ch4_1e4_m3_yr": df.loc[m, value_col].sum(),
            "ch4_share_pct": 100 * df.loc[m, value_col].sum() / total,
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Reporting helpers
# --------------------------------------------------------------------------

def to_1e8_nm3_per_year(annual_1e4):
    """Sum a column of 10^4 m3/yr values and express it in 10^8 Nm3/yr."""
    return float(np.sum(annual_1e4)) * 1e4 / 1e8


def standard_coal_mt(total_1e8_nm3):
    """Standard-coal equivalent of an annual methane volume, Mt/yr."""
    return total_1e8_nm3 * 1e8 * CH4_LHV_MJ_PER_NM3 / STANDARD_COAL_MJ_PER_KG / 1e9


def teragrams(total_1e8_nm3):
    """Mass of an annual methane volume, Tg/yr."""
    return total_1e8_nm3 * 1e8 * CH4_DENSITY_KG_PER_NM3 / 1e9


def ensure_outputs():
    """Create the outputs directory if it does not exist."""
    OUT.mkdir(parents=True, exist_ok=True)
    return OUT
