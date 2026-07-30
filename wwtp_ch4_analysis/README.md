# Concentration and Monte Carlo analysis code

Analysis code accompanying:

> Can Xiong *Concentrated distribution and targeted
> deployment of methane resources in China's municipal wastewater treatment
> plants.* Resources, Conservation & Recycling (2026). 

Running `run_all.py` reproduces every quantitative result in the manuscript
and Supplementary Information from the raw plant dataset, and prints a
verification table comparing each computed value against the published figure.

---

## Quick start

```bash
pip install -r requirements.txt
python run_all.py
```

Expected runtime: about 90 seconds (most of it the 2,000 Monte Carlo
iterations). For a fast check:

```bash
python run_all.py --quick      # 200 iterations
python run_all.py --no-mc      # skip the Monte Carlo
```

The run ends with a line of the form `43 of 43 checks passed.` Any mismatch is
listed explicitly.

---

## Contents

| File | Purpose |
|---|---|
| `wwtp_model.py` | Core full-chain yield model (Methods S1.1), tier assignment, Gini/Lorenz metrics |
| `montecarlo.py` | Monte Carlo uncertainty ensemble and sensitivity ranking (Methods S1.3) |
| `distribution.py` | Log-normal and power-law fits, Vuong comparison (Methods S1.2) |
| `recoverable.py` | Tiered recovery scenarios, coverage sensitivity (S1.7), Sun et al. validation (S1.6) |
| `run_all.py` | Runs everything, writes `outputs/`, verifies against published values |
| `data/` | Input data (see below) |
| `outputs/` | Generated results (created on first run) |

### Input data

| File | Source |
|---|---|
| `中国污水处理厂数据集.xlsx` | Zhou, S. *et al.* (2024) *Scientific Data* **11**, 941. Sheet `A-WWTP` (above-ground plants) is used. |
| `sun_S2_capacity.csv` | Transcribed from Table S2 of Sun, C. *et al.* (2026) *Science Advances* **12**, eaec0536 — plant capacity and process. |
| `sun_S3_periods.csv` | Transcribed from Table S3 of the same paper — measured emission rates by observational period. |

Both source datasets are openly published; see the licence note at the end.

### Generated outputs

`plant_level_estimates.csv` (per-plant results, 2,457 rows) ·
`table1_size_categories.csv` · `table2_scenarios.csv` · `tier_summary.csv` ·
`tableS3_thresholds.csv` · `tableS6_coverage_sensitivity.csv` ·
`tableS7_full_factorial.csv` · `distribution_fit.csv` · `ccdf.csv` ·
`monte_carlo_iterations.csv` · `monte_carlo_summary.csv` ·
`monte_carlo_sensitivity.csv` · `sun_validation_plants.csv` ·
`sun_validation_stats.csv` · `verification.csv`

`plant_level_estimates.csv` is the per-plant methane estimate referred to in
the Data availability statement, and is the input to the figure scripts,
which are distributed separately.

---

## Method summary

**Full-chain model (Methods S1.1).** Eight steps from design capacity to
annual methane: daily flow → influent COD → design effluent COD by discharge
grade (GB 18918-2002) → COD removal → volatile suspended solids via a
process-specific net sludge yield → methane via VS destruction (η_AD = 0.55)
and the yield coefficient (k_CH₄ = 0.35 m³ kg VS⁻¹). Parameter values are in
`wwtp_model.py` and Table S1.

**Deployment tiers (Section 2.3).** Tier I ≥ 5 × 10⁴ m³ d⁻¹, Tier II
2–5 × 10⁴, Tier III < 2 × 10⁴, following HJ-BAT-002 (MEP, 2010).

**Monte Carlo (Methods S1.3).** 2,000 iterations. Each draws one value per
parameter and applies it to all plants: η_AD ~ triangular(0.40, 0.55, 0.65);
Y_net scaled by a uniform ±15 % multiplier; k_CH₄ ~ triangular(0.30, 0.35,
0.40); f_VS ~ uniform(0.55, 0.80); missing influent COD bootstrap-resampled
from the 2,188 measured values. f_VS does not enter the methane chain and is
included as a decoy — its near-zero rank correlation confirms the sensitivity
ranking reflects model structure rather than sampling noise.

---

## Two implementation notes

**1. Deterministic COD imputation uses a constant, not the bootstrap.**
For the deterministic point estimate the 269 plants without a measured
influent COD are filled with a single constant, 252 mg L⁻¹ — the rounded mean
of the 2,188 measured values (`COD_FILL_DETERMINISTIC` in `wwtp_model.py`).
Bootstrap resampling is used in the Monte Carlo, where the resulting spread is
part of the reported uncertainty. Step 2 of Methods S1.1 describes the
imputation only in its bootstrap form; the constant fill is what produces the
published deterministic total of 7.32 × 10⁸ Nm³ yr⁻¹, and the two are
reconciled here.

**2. Monte Carlo percentiles carry sampling noise.**
The default seed is 25 (`montecarlo.py`). Across seeds the median national
total varies by roughly ±0.05 × 10⁸ Nm³ yr⁻¹ and the interval bounds by about
±0.10 × 10⁸, so digit-for-digit agreement with the published interval is not
expected from an arbitrary seed. The quantities the paper's argument rests on
are stable across every seed tested: the Gini interval (0.665–0.674), the
Tier-I share interval (75.2–76.0 %), and the sensitivity ranking
(η_AD > Y_net > k_CH₄ ≫ COD, f_VS). The rank correlations for COD and f_VS are
small and noisy by construction; only their negligibility is meaningful, not
their exact values.

Everything else — the deterministic total, Gini, tier counts and shares,
distribution parameters, Vuong statistic, scenario table and validation
statistics — is deterministic and reproduces exactly.

---

## Requirements

Python 3.9 or later, with `pandas`, `numpy`, `scipy`, `openpyxl`, and
`powerlaw`.

`powerlaw` supplies the Vuong comparison. If it is not installed the code
falls back to a built-in implementation that reaches the same conclusion but
returns a slightly different value of R, and emits a warning; install
`powerlaw` to reproduce the published statistic exactly.

---

## Licence and attribution

This package mixes three sets of terms; **see `LICENSE.md` for the per-file
detail.** In summary:

| Component | Licence |
|---|---|
| Code (`*.py`) | MIT |
| Results generated into `outputs/` | CC BY 4.0 |
| `data/中国污水处理厂数据集.xlsx` | CC BY 4.0 (Zhou *et al.*, figshare) |
| `data/sun_S2_capacity.csv`, `data/sun_S3_periods.csv` | **CC BY-NC 4.0** (Sun *et al.*) |

Because the two Sun *et al.* files carry a NonCommercial condition, a
repository record containing them should be registered as **CC BY-NC 4.0**.
To deposit under a fully permissive CC BY 4.0 record instead, delete those two
files first — `run_all.py` detects their absence, skips the validation
section, prints instructions for obtaining them, and reproduces everything
else unchanged.

Both source datasets permit redistribution. Cite them as:

- Zhou, S. *et al.* (2024). A Dataset of Distribution and Characterization of
  Underground Wastewater Treatment Plants in China. figshare.
  https://doi.org/10.6084/m9.figshare.26085265 — Data Descriptor:
  *Scientific Data* **11**, 941. https://doi.org/10.1038/s41597-024-03815-x
- Sun, C. *et al.* (2026). Measurement-based assessment reveals key drivers
  and mitigation potential of methane emissions from China's wastewater
  treatment. *Science Advances* **12** (15), eaec0536.
  https://doi.org/10.1126/sciadv.aec0536

CC BY 4.0 requires that modifications be indicated. The column headers of the
Zhou *et al.* file redistributed here were translated from English to Chinese;
no values were changed. The full header mapping is given in `LICENSE.md`.
