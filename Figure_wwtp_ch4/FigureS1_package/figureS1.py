#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure S1 - Cross-study comparison of national CH4 estimates for China's
municipal WWTPs, on a logarithmic axis with reported uncertainty ranges.
SELF-CONTAINED, LOCALLY RUNNABLE.

Run
---
    pip install numpy pandas matplotlib
    python figureS1.py

Reads only figS1_data.csv shipped next to this script (HERE-relative paths),
and writes FigureS1.png (600 dpi) + FigureS1.pdf (vector) next to itself.

Design logic (the figure is a visual argument, not decoration)
--------------------------------------------------------------
* Core claim: this study's THEORETICAL AD-recovery potential (~0.50 Tg CH4/yr)
  is the same order of magnitude as, and sits consistently ABOVE, independent
  measurement- and inventory-based estimates of ACTUAL emission - an
  order-of-magnitude plausibility check, NOT a validation (the quantities are
  physically different).
* Encoding: horizontal forest plot on a log x-axis. Two method families -
  recovery potential (this study, deep teal) vs actual emission (independent
  benchmarks, neutral grey) - separated by a hairline and by grouped left
  labels, so the eye immediately reads "different quantity, same ballpark,
  this study higher."
* This study carries a graded error bar: a thick bar for the Monte Carlo 95%
  CI (parameter + imputation uncertainty) and a thin bar for the fuller
  bias-bounding band (which additionally spans the influent-COD lever), making
  the paper's honest, wider uncertainty visible rather than hidden.
* IPCC-2006 top-down values are deliberately NOT plotted: the manuscript has no
  single sourced China-municipal number for them, so drawing a bar would be
  fabrication. The "below IPCC-2006" narrative is handled in the text, not the
  figure.
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, NullLocator

# --- paths (relative to this script) -----------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "figS1_data.csv")
if not os.path.exists(DATA):
    sys.exit("Required input not found: %s\n  Keep figureS1.py and figS1_data.csv together." % DATA)

# --- publication styling (inlined; no external module needed) ----------------
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "Liberation Sans"],
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "mathtext.default": "regular",
    "font.size": 7,
    "axes.linewidth": 0.8,
})

INK, MID = "#2F3337", "#8C9094"
TEAL = "#2C5A6B"     # this study  (Tier I colour, manuscript palette)
GREY = "#7C8084"     # emission benchmarks (neutral family)
STONE = "#CBC7BC"    # emission-range band

df = pd.read_csv(DATA)

# rows top -> bottom in the given file order
n = len(df)
y = np.arange(n)[::-1].astype(float)          # first row highest on the plot
df = df.reset_index(drop=True)

fig, ax = plt.subplots(figsize=(4.05, 2.55))
fig.subplots_adjust(left=0.335, right=0.965, top=0.845, bottom=0.175)

# --- emission-range anchor band (0.10-0.25 Tg) -------------------------------
emis = df[df.group == "emission"]
band_lo = float(np.nanmin(emis.value_Tg))
band_hi = float(np.nanmax(emis.value_Tg))
ax.axvspan(band_lo, band_hi, color=STONE, alpha=0.35, lw=0, zorder=0)
ax.text(np.sqrt(band_lo * band_hi), y.max() + 0.62,
        "actual-emission range", ha="center", va="bottom",
        fontsize=5.6, style="italic", color=MID)

# --- points + error bars -----------------------------------------------------
for i, r in df.iterrows():
    yi = y[i]
    col = TEAL if r.group == "potential" else GREY
    v = float(r.value_Tg)

    if r.group == "potential":
        # thin full-uncertainty band (behind), no caps
        if pd.notna(r.lo_band_Tg):
            ax.plot([r.lo_band_Tg, r.hi_band_Tg], [yi, yi], color=TEAL,
                    lw=1.1, alpha=0.42, solid_capstyle="butt", zorder=2)
        # thick MC 95% CI
        ax.errorbar(v, yi, xerr=[[v - r.lo_Tg], [r.hi_Tg - v]], fmt="none",
                    ecolor=TEAL, elinewidth=2.4, capsize=2.6, capthick=1.1, zorder=3)
        ax.plot(v, yi, "o", ms=7.2, mfc=TEAL, mec="white", mew=0.9, zorder=4)
    else:
        if pd.notna(r.lo_Tg):
            ax.errorbar(v, yi, xerr=[[v - r.lo_Tg], [r.hi_Tg - v]], fmt="none",
                        ecolor=GREY, elinewidth=1.4, capsize=2.4, capthick=0.9, zorder=3)
        ax.plot(v, yi, "o", ms=5.4, mfc=GREY, mec="white", mew=0.8, zorder=4)

    # value label (placed to the right of the row's right-most drawn element)
    if r.group == "potential" and pd.notna(r.hi_band_Tg):
        xr = float(r.hi_band_Tg)
    elif pd.notna(r.get("hi_Tg")):
        xr = float(r.hi_Tg)
    else:
        xr = v
    lab = ("%.2f Tg" % v) if r.group == "potential" else (("\u2248%.2f" % v) if r.range_note == "no reported range" else ("%.2f" % v))
    ax.annotate(lab, (xr, yi), xytext=(6, 0), textcoords="offset points",
                ha="left", va="center", fontsize=6.4,
                color=(TEAL if r.group == "potential" else INK),
                fontweight=("bold" if r.group == "potential" else "normal"))

    # left labels: study name + sublabel (anchored in axes-fraction x to avoid log(0))
    trL = ax.get_yaxis_transform()
    ax.annotate(r.label, xy=(-0.33, yi), xycoords=trL, xytext=(0, 3.2),
                textcoords="offset points", ha="left", va="center",
                fontsize=6.9, color=INK,
                fontweight=("bold" if r.group == "potential" else "normal"),
                annotation_clip=False)
    ax.annotate(r.sublabel, xy=(-0.33, yi), xycoords=trL, xytext=(0, -5.4),
                textcoords="offset points", ha="left", va="center",
                fontsize=5.5, color=MID, style="italic", annotation_clip=False)

# --- group brackets on the far left ------------------------------------------
def bracket(y0, y1, text, color):
    xb = -0.40             # axes fraction (to the left of everything)
    tr = ax.get_yaxis_transform()  # x in axes frac, y in data
    ax.plot([xb, xb], [y0, y1], color=color, lw=1.4, transform=tr,
            clip_on=False, solid_capstyle="round")
    for yy in (y0, y1):
        ax.plot([xb, xb + 0.018], [yy, yy], color=color, lw=1.4, transform=tr, clip_on=False)
    ax.text(xb - 0.028, (y0 + y1) / 2, text, rotation=90, ha="center", va="center",
            fontsize=6.0, color=color, fontweight="bold", transform=tr, clip_on=False)

pot_y = y[df.group == "potential"].tolist()
emi_y = y[df.group == "emission"].tolist()
bracket(min(pot_y) - 0.28, max(pot_y) + 0.28, "Potential", TEAL)
bracket(min(emi_y) - 0.28, max(emi_y) + 0.28, "Actual emission", GREY)

# hairline separating the two families
ysep = (min(pot_y) + max(emi_y)) / 2.0
ax.axhline(ysep, color=MID, lw=0.5, ls=(0, (3, 3)), alpha=0.6, zorder=1)

# --- axes cosmetics ----------------------------------------------------------
ax.set_xscale("log")
ax.set_xlim(0.072, 1.05)
ax.set_ylim(-0.7, y.max() + 0.95)
ax.set_yticks([])
for sp in ("top", "left", "right"):
    ax.spines[sp].set_visible(False)
ticks = [0.1, 0.2, 0.3, 0.5, 0.7]
ax.xaxis.set_major_locator(FixedLocator(ticks))
ax.xaxis.set_minor_locator(NullLocator())
ax.set_xticklabels(["%.1f" % t for t in ticks])
ax.tick_params(axis="x", length=3, width=0.8, labelsize=6.6)
for t in ticks:
    ax.axvline(t, color=MID, lw=0.4, alpha=0.16, zorder=0)
ax.set_xlabel("National CH$_4$  (Tg yr$^{-1}$, log scale)", fontsize=7.0, color=INK)

# graded-error-bar note
ax.text(0.965, -0.62, "this study:  thick = MC 95% CI   thin = full uncertainty band",
        ha="right", va="center", fontsize=5.2, style="italic", color=MID,
        transform=ax.get_yaxis_transform())

stem = os.path.join(HERE, "FigureS1")
fig.savefig(stem + ".png", dpi=600, bbox_inches="tight")
fig.savefig(stem + ".pdf", bbox_inches="tight")
print("wrote FigureS1.{png,pdf} | this study 0.50 Tg (MC CI 0.38-0.66; band 0.25-0.70) | "
      "emission benchmarks 0.10-0.25 Tg")
