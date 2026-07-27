Figure 3 - reproducible package
===============================

Contents
    figure3.py                 self-contained plotting script (no external modules)
    Figure3.png                output, 600 dpi raster
    Figure3.pdf                output, vector (editable text, pdf.fonttype=42)
    input CSVs (5):
        fig3a_pdf_hist.csv       log10 histogram of plant-level CH4 (density/decade)
        fig3b_ccdf.csv           empirical complementary CDF (ch4_m3d, P(X>x))
        fig3_fit_stats.csv       log-normal (mu,sigma), power-law (alpha,x_min), Vuong
        fig3c_mc_indicators.csv  Monte-Carlo p2.5/median/p97.5 for 3 indicators
        fig3d_sensitivity.csv    |Spearman rho| of each parameter vs national total

Run
    pip install numpy pandas scipy matplotlib
    python figure3.py

Paths are resolved relative to the script, so it runs from any working
directory. It regenerates Figure3.png and Figure3.pdf next to itself.
Output is deterministic (the CSVs already contain the fitted / Monte-Carlo
results; this script only plots them).

Panels
    (a) probability density of per-plant daily CH4 with the log-normal fit
        (mu=5.79, sigma=1.40; geometric mean e^mu = 326 m3/d).
    (b) complementary CDF on log-log axes: the empirical tail follows the
        log-normal, not the power law (Vuong test prefers log-normal, p<0.001).
    (c) Monte-Carlo robustness: the national total is uncertain (95% CI 55.8%),
        whereas the Gini coefficient (1.4%) and Tier-I share (1.1%) are nearly
        invariant.
    (d) parameter sensitivity: eta_AD and Y_net dominate; COD and VSS/DS
        negligible.

Colour semantics (harmonised with Figures 1-2):
    deep teal #2C5A6B = fitted / robust quantities (log-normal, Gini, Tier-I);
    clay      #C08A5E = uncertain / dominant-driver quantities (national total,
                        eta_AD, Y_net; power-law reference);
    sand      #C2A06B = secondary driver (k_CH4); stone #CBC7BC = negligible.

Caption (suggested)
    Figure 3. Distribution and robustness of plant-level CH4 potential across
    2,431 plants with positive potential. (a) Probability density with the
    log-normal fit. (b) Complementary CDF versus log-normal and power-law
    references. (c) Monte-Carlo relative spread of the national total, Gini
    coefficient and Tier-I share. (d) Parameter sensitivity (|Spearman rho|
    versus the national total).
