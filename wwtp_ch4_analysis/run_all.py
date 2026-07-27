#!/usr/bin/env python3
"""
Reproduce every quantitative result reported in the manuscript and SI.

Usage
-----
    python run_all.py                  # full run (2,000 Monte Carlo iterations)
    python run_all.py --quick          # 200 iterations, for a fast check
    python run_all.py --seed 25        # choose the Monte Carlo seed
    python run_all.py --no-mc          # skip the Monte Carlo entirely

Outputs are written to ``outputs/`` as CSV. A verification table comparing
each computed value against the published figure is printed at the end and
saved to ``outputs/verification.csv``.
"""

import argparse
import sys

import numpy as np
import pandas as pd

import distribution as D
import montecarlo as MC
import recoverable as R
import wwtp_model as M


def banner(text):
    print("\n" + "=" * 74)
    print(text)
    print("=" * 74)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=MC.SEED,
                    help=f"Monte Carlo seed (default {MC.SEED})")
    ap.add_argument("--iterations", type=int, default=MC.N_ITERATIONS,
                    help=f"Monte Carlo iterations (default {MC.N_ITERATIONS})")
    ap.add_argument("--quick", action="store_true",
                    help="shorthand for --iterations 200")
    ap.add_argument("--no-mc", action="store_true",
                    help="skip the Monte Carlo analysis")
    args = ap.parse_args(argv)
    if args.quick:
        args.iterations = 200

    out = M.ensure_outputs()
    checks = []

    def check(label, value, published, tol, fmt="{:.4g}"):
        ok = abs(value - published) <= tol
        checks.append({
            "quantity": label,
            "computed": value,
            "published": published,
            "tolerance": tol,
            "match": "PASS" if ok else "FAIL",
        })
        flag = "  ok" if ok else "  ** MISMATCH **"
        print(f"    {label:<46s} {fmt.format(value):>12s}  "
              f"(paper {fmt.format(published)}){flag}")

    # ---------------------------------------------------------------- load
    banner("1. Loading plant records")
    plants = M.load_plants()
    print(f"    above-ground plants retained          : {len(plants)}")
    print(f"    with measured influent COD            : {plants['cod_measured'].notna().sum()}")
    print(f"    influent COD imputed                  : {plants['cod_measured'].isna().sum()}")
    check("plant count", len(plants), 2457, 0, "{:.0f}")
    check("plants with measured COD", int(plants["cod_measured"].notna().sum()), 2188, 0, "{:.0f}")
    check("plants with imputed COD", int(plants["cod_measured"].isna().sum()), 269, 0, "{:.0f}")

    # ------------------------------------------------------- deterministic
    banner("2. Deterministic estimate (Methods S1.1)")
    det = M.deterministic_estimate(plants)
    annual = det["ch4_annual_1e4_m3"]
    total = M.to_1e8_nm3_per_year(annual)

    check("national total (1e8 Nm3/yr)", total, 7.32, 0.005, "{:.2f}")
    check("Gini coefficient", M.gini(annual), 0.663, 0.001, "{:.3f}")
    check("plants with positive output", int((annual > 0).sum()), 2431, 0, "{:.0f}")
    check("standard-coal equivalent (Mt/yr)", M.standard_coal_mt(total), 0.90, 0.01, "{:.2f}")
    check("mass (Tg/yr)", M.teragrams(total), 0.52, 0.005, "{:.2f}")

    tiers = M.tier_summary(det)
    for _, row in tiers.iterrows():
        published_n = {"I": 724, "II": 1004, "III": 729}[row["tier"]]
        published_share = {"I": 75.6, "II": 20.2, "III": 4.2}[row["tier"]]
        check(f"Tier {row['tier']} plant count", int(row["plants"]), published_n, 0, "{:.0f}")
        check(f"Tier {row['tier']} CH4 share (%)", row["ch4_share_pct"], published_share, 0.06, "{:.1f}")

    check("top 10% of plants hold (%)", 100 * M.top_share(annual, 0.10), 54.0, 0.5, "{:.1f}")
    check("top 50% of plants hold (%)", 100 * M.top_share(annual, 0.50), 91.0, 0.5, "{:.1f}")

    det.to_csv(out / "plant_level_estimates.csv", index=False, encoding="utf-8-sig")
    tiers.to_csv(out / "tier_summary.csv", index=False)

    # Table 1: size-category breakdown
    bins = [(0, 1), (1, 2), (2, 5), (5, 10), (10, 20), (20, 50), (50, np.inf)]
    rows, cumulative = [], 0.0
    for lo, hi in bins:
        m = (det["capacity"] >= lo) & (det["capacity"] < hi)
        share = 100 * annual[m].sum() / annual.sum()
        cumulative += share
        rows.append({
            "capacity_1e4_m3_d": f"{lo}-{hi}" if np.isfinite(hi) else f">= {lo}",
            "plants": int(m.sum()),
            "plant_share_pct": 100 * m.sum() / len(det),
            "ch4_1e4_m3_yr": annual[m].sum(),
            "ch4_share_pct": share,
            "cumulative_pct": cumulative,
        })
    table1 = pd.DataFrame(rows)
    table1.to_csv(out / "table1_size_categories.csv", index=False)
    print("\n    Table 1 written to outputs/table1_size_categories.csv")

    # Table S3: threshold sweep
    rows = []
    for thr in [2, 3, 4, 5, 6]:
        m = det["capacity"] >= thr
        rows.append({
            "threshold_1e4_m3_d": thr,
            "plants": int(m.sum()),
            "plant_share_pct": 100 * m.sum() / len(det),
            "ch4_share_pct": 100 * annual[m].sum() / annual.sum(),
        })
    pd.DataFrame(rows).to_csv(out / "tableS3_thresholds.csv", index=False)

    # ------------------------------------------------------- distribution
    banner("3. Distribution fitting and Vuong test (Methods S1.2)")
    x = D.positive_output(det)
    ln = D.fit_lognormal(x)
    pl = D.fit_powerlaw(x)
    vg = D.vuong_test(x)

    check("log-normal mu", ln["mu"], 5.786, 0.001, "{:.3f}")
    check("log-normal sigma", ln["sigma"], 1.402, 0.001, "{:.3f}")
    check("geometric mean (m3/d)", ln["geometric_mean"], 326, 1, "{:.0f}")
    check("power-law alpha", vg["alpha"], 1.993, 0.002, "{:.3f}")
    check("power-law x_min (m3/d)", pl["xmin"], 350, 1, "{:.0f}")
    check("Vuong R", vg["R"], -5.01, 0.02, "{:.2f}")
    print(f"    Vuong p-value: {vg['p_value']:.2e}   preferred: {vg['preferred']}"
          f"   [{vg['implementation']}]")

    D.ccdf(x).to_csv(out / "ccdf.csv", index=False)
    pd.DataFrame([{**ln, **pl, **vg}]).to_csv(out / "distribution_fit.csv", index=False)

    # -------------------------------------------------------- Monte Carlo
    if not args.no_mc:
        banner(f"4. Monte Carlo ({args.iterations} iterations, seed {args.seed})")
        mc = MC.run_monte_carlo(plants, n_iter=args.iterations,
                                seed=args.seed, progress=True)
        summary = MC.summarise(mc)
        sens = MC.sensitivity(mc)
        mc.to_csv(out / "monte_carlo_iterations.csv", index=False)
        summary.to_csv(out / "monte_carlo_summary.csv", index=False)
        sens.to_csv(out / "monte_carlo_sensitivity.csv", index=False)

        tot = summary.iloc[0]
        gin = summary.iloc[1]
        tia = summary.iloc[2]
        check("MC median total (1e8 Nm3/yr)", tot["median"], 7.04, 0.06, "{:.2f}")
        check("MC total 2.5th pct", tot["p2.5"], 5.27, 0.12, "{:.2f}")
        check("MC total 97.5th pct", tot["p97.5"], 9.20, 0.12, "{:.2f}")
        check("MC Gini 2.5th pct", gin["p2.5"], 0.665, 0.002, "{:.3f}")
        check("MC Gini 97.5th pct", gin["p97.5"], 0.674, 0.002, "{:.3f}")
        check("MC Tier-I share 2.5th pct", tia["p2.5"], 75.2, 0.2, "{:.1f}")
        check("MC Tier-I share 97.5th pct", tia["p97.5"], 76.0, 0.2, "{:.1f}")

        print("\n    Sensitivity ranking (|Spearman rho| vs national total):")
        for _, r in sens.iterrows():
            print(f"      {r['parameter']:<10s} {r['abs_spearman']:.3f}")
        expected = ["eta_AD", "Y_net", "k_CH4"]
        actual = sens["parameter"].tolist()[:3]
        ok = actual == expected
        checks.append({
            "quantity": "sensitivity ranking (top 3)",
            "computed": " > ".join(actual),
            "published": " > ".join(expected),
            "tolerance": "exact",
            "match": "PASS" if ok else "FAIL",
        })
        print(f"    ranking {' > '.join(actual)}"
              f"{'  ok' if ok else '  ** MISMATCH **'}")
    else:
        print("\n(Monte Carlo skipped)")

    # --------------------------------------------------------- recoverable
    banner("5. Tiered recovery scenarios (Section 3.5, Methods S1.7)")
    scen = R.scenario_table(det)
    print(scen.round(2).to_string(index=False))
    scen.to_csv(out / "table2_scenarios.csv", index=False)

    mid = scen[scen["scenario"] == "Mid"].iloc[0]
    check("mid recoverable (1e8 Nm3/yr)", mid["recoverable_1e8_Nm3_yr"], 2.00, 0.01, "{:.2f}")
    check("mid recovery rate (%)", mid["recovery_rate_pct"], 27.3, 0.1, "{:.1f}")
    check("mid Tier-I share of recoverable (%)", mid["tier_I_pct"], 86.4, 0.1, "{:.1f}")

    fac = R.full_factorial(det)
    fac.to_csv(out / "tableS7_full_factorial.csv", index=False)
    check("factorial min recoverable (1e8)", fac["recoverable_1e8_Nm3_yr"].min(), 0.86, 0.01, "{:.2f}")
    check("factorial max recoverable (1e8)", fac["recoverable_1e8_Nm3_yr"].max(), 3.79, 0.01, "{:.2f}")

    check("factorial min Tier-I share (%)", fac["tier_I_share_pct"].min(), 76.9, 0.1, "{:.1f}")
    check("factorial max Tier-I share (%)", fac["tier_I_share_pct"].max(), 93.4, 0.1, "{:.1f}")

    cov = R.coverage_sensitivity(det)
    cov.to_csv(out / "tableS6_coverage_sensitivity.csv")
    print("\n    Table S6 - Tier-I share (%) by coverage "
          "(rows: Tier-I, columns: Tier-III, Tier-II fixed at 0.35)")
    print(cov.round(1).to_string())
    check("Table S6 minimum (%)", cov.values.min(), 81.9, 0.1, "{:.1f}")
    check("Table S6 mid cell (%)", cov.loc[0.65, 0.15], 86.4, 0.1, "{:.1f}")

    # ---------------------------------------------------------- validation
    banner("6. Independent validation against Sun et al. (Methods S1.6)")
    if not R.sun_data_available():
        print(R.SUN_DATA_MISSING_HELP)
        sun = None
    else:
        sun = R.load_sun_dataset()
    if sun is not None:
        vs = R.validation_stats(sun)
        sun.to_csv(out / "sun_validation_plants.csv", index=False)
        pd.DataFrame([vs]).to_csv(out / "sun_validation_stats.csv", index=False)

        check("Sun plants matched", vs["n_plants"], 105, 0, "{:.0f}")
        check("Spearman capacity vs emission", vs["spearman_capacity_vs_emission"], 0.61, 0.01, "{:.2f}")
        check("Kendall tau", vs["kendall_tau"], 0.46, 0.01, "{:.2f}")
        check("Spearman, repeat-measured only", vs["spearman_repeat_only"], 0.77, 0.01, "{:.2f}")
        check("log-log slope", vs["loglog_slope"], 0.65, 0.01, "{:.2f}")
        check("log-log R2", vs["loglog_r2"], 0.43, 0.01, "{:.2f}")
        check("Gini of measured emission", vs["gini_measured_emission"], 0.52, 0.01, "{:.2f}")
        check("share at or above 5e4 m3/d (%)", vs["pct_at_or_above_5e4"], 75.0, 0.5, "{:.1f}")
        print(f"    Spearman predicted vs measured        : "
              f"{vs['spearman_predicted_vs_measured']:.2f}  (paper 0.56)")

    # ------------------------------------------------------------- verdict
    banner("Verification summary")
    ver = pd.DataFrame(checks)
    ver.to_csv(out / "verification.csv", index=False)
    n_fail = (ver["match"] == "FAIL").sum()
    print(f"    {len(ver) - n_fail} of {len(ver)} checks passed.")
    if n_fail:
        print("\n    Failing checks:")
        print(ver[ver["match"] == "FAIL"].to_string(index=False))
    print(f"\n    All outputs written to: {out}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
