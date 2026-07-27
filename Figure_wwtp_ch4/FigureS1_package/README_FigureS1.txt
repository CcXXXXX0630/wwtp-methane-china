Figure S1 - Cross-study comparison of national CH4 estimates
============================================================

Files (keep together; paths are resolved relative to the script):
    figureS1.py        - self-contained generator (Python 3 + matplotlib/pandas/numpy)
    figS1_data.csv     - input data (from SI Table S2), with Nm3 -> Tg conversion baked in
    FigureS1.png       - 600 dpi raster
    FigureS1.pdf       - vector (editable text; pdf.fonttype 42)

Run:
    pip install numpy pandas matplotlib
    python figureS1.py            # writes FigureS1.png + FigureS1.pdf next to itself

What the figure argues
----------------------
This study's THEORETICAL AD-recovery potential (~0.50 Tg CH4/yr) is the same
order of magnitude as, and sits consistently ABOVE, independent measurement-
and inventory-based estimates of ACTUAL emission (0.10-0.25 Tg). It is an
order-of-magnitude plausibility check, NOT a validation - the two are
physically different quantities.

Design (Nature/Cell/Science conventions)
----------------------------------------
* Horizontal forest plot on a log x-axis; Arial; thin spines; white ground.
* Two method families, direct-labelled by left brackets: recovery potential
  (this study, deep teal #2C5A6B - Tier I colour) vs actual emission
  (independent benchmarks, neutral grey), separated by a hairline.
* This study carries a GRADED error bar: thick = Monte Carlo 95% CI
  (0.38-0.66 Tg); thin = full bias-bounding band (0.25-0.70 Tg, which adds the
  influent-COD lever). This shows the paper's wider, honest uncertainty rather
  than hiding it.
* CH4 density 0.716 kg/Nm3 used for Nm3 -> Tg.

Deliberate omission
-------------------
IPCC-2006 top-down values are NOT plotted: no single sourced China-municipal
number exists in the manuscript, so a bar would be fabrication. If a sourced
value is supplied it can be added as a right-hand marker; otherwise the
"below IPCC-2006" clause in the caption/main text should be dropped.

QA note
-------
Visual-preview tooling was unavailable at build time, so layout was verified
programmatically: pairwise text bounding-box overlap = 0; data points map to
the correct log-axis order (this study right-most); value labels clear the
error bars. Re-render and eyeball before final submission.
