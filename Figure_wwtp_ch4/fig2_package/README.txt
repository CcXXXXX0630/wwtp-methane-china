Figure 2 - reproducible package
===============================

Contents
    figure2.py                          self-contained plotting script
    fig2_data.csv                       per-plant data: capacity_1e4_m3_d,
                                        CH4_1e4_m3_yr, tier  (2,457 plants)
    fig1_province_totals_1e8m3yr.csv    provincial CH4 totals (29 provinces)
    Figure2.png                         output, 600 dpi raster
    Figure2.pdf                         output, vector (editable text)

Run
    pip install numpy pandas matplotlib
    python figure2.py

No SciPy needed (the half-violin KDE is computed in NumPy). Paths are resolved
relative to the script, so it runs from any working directory. The only
stochastic element is the seeded point jitter in (c); the figure is otherwise
deterministic.

The figure shows concentration along TWO axes.
    (a) SPATIAL - provincial treemap. Each province's box area = its share of
        national CH4; a squarified treemap (Bruls et al. 2000, implemented in
        the script) lays the 29 provinces out. The eight leading provinces are
        labelled; colour deepens with share. Top 5 provinces = 47.6%, provincial
        Gini 0.52.
    (b) OVERALL - Lorenz curve of plant-level CH4 potential; Gini = 0.663; the
        top 10% of plants hold 54% of CH4.
    (c) PLANT SIZE - raincloud (half-violin kernel density + one point per plant
        + tier-mean bar, log axis) of per-plant CH4 by tier, each tier labelled
        with its share of CH4 (76 / 20 / 4 %). Tiers I and III hold a similar
        NUMBER of plants (724 vs 729), but Tier I plants are ~18x larger on
        average, so Tier I holds 76% and Tier III 4% - concentration by plant
        SIZE, not count. The 26 zero-CH4 plants sit on a faint baseline.

All quantities are THEORETICAL potential (the recoverable amplification,
75.6% -> 86.4% for Tier I, is Figure 4). Tier colours match Figures 1, 3-4
(Tier I / II / III = #2C5A6B / #C08A5E / #CBC7BC); panel (a) uses a sequential
teal ramp for province magnitude.

Caption (suggested)
    Figure 2. The methane resource is concentrated both spatially and by plant
    size. (a) Provincial treemap (box area = province share of national CH4;
    top 5 provinces hold 47.6%, Gini 0.52). (b) Lorenz curve and Gini coefficient
    of plant-level CH4 potential. (c) Per-plant CH4 potential by tier (half-
    violin density, individual plants, and tier means on a log scale), labelled
    with each tier's share of CH4; Tiers I and III contain similar plant counts,
    but Tier I's larger plants carry most of the methane.
