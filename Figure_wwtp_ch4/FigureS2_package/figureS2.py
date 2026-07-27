#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure S2 - Independent measurement-based check of the size dependence.
Measured plant-level CH4 emission rate (Sun et al. 2026, Sci. Adv.,
DOI 10.1126/sciadv.aec0536) versus treatment capacity, on log-log axes.
SELF-CONTAINED, LOCALLY RUNNABLE.

Run
---
    pip install numpy scipy matplotlib
    python figureS2.py

Reproduces everything from the two raw source tables transcribed from the
Sun et al. Supplementary Materials, shipped next to this script:
    sun_S2_capacity.csv  (Table S2: site -> capacity 1e3 m3/d, process; 105 plants)
    sun_S3_periods.csv   (Table S3: site -> measured ER kg/h; 141 obs. periods)
For each plant the mean measured ER across its observation periods is taken,
giving one point per plant; the point is coloured by our size tier and sized by
the number of observation periods. Writes FigureS2.png (600 dpi) + FigureS2.pdf.

Why this figure
---------------
Our national estimate builds in a size dependence (large plants dominate the
recoverable methane). This figure shows that an INDEPENDENT, measurement-based
dataset exhibits the same monotonic rise of CH4 with plant scale - a validation
of the mechanism, using data we did not generate. Note the y-axis is a measured
fugitive EMISSION rate, not our recovery potential; the two are physically
different quantities, so only the DIRECTION/scaling of the size dependence is
being validated here, not the magnitude.
"""
import os, sys, csv, math
import numpy as np
from scipy import stats
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, NullLocator
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
CAP  = os.path.join(HERE, "sun_S2_capacity.csv")
PER  = os.path.join(HERE, "sun_S3_periods.csv")
for f in (CAP, PER):
    if not os.path.exists(f):
        sys.exit("Required input not found: %s" % f)

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "Liberation Sans"],
    "svg.fonttype": "none", "pdf.fonttype": 42,
    "mathtext.default": "regular", "font.size": 7, "axes.linewidth": 0.8,
})
INK, MID = "#2F3337", "#8C9094"
TIER_COL = {"I": "#2C5A6B", "II": "#C08A5E", "III": "#CBC7BC"}   # manuscript palette
CITY = {"N": "Nanjing", "S": "Shenyang", "Z": "Zibo", "X": "Xi'an", "G": "Guangzhou"}

# ---- load + aggregate ----
cap = {}
with open(CAP) as fh:
    for r in csv.DictReader(fh):
        cap[r["site"]] = (float(r["capacity_1e3_m3d"]) * 1000.0, r["process"])
per = {}
with open(PER) as fh:
    for r in csv.DictReader(fh):
        per.setdefault(r["site"], []).append(float(r["ER_kg_h"]))

sites = [s for s in cap if s in per]
x   = np.array([cap[s][0] for s in sites])                 # m3/d
y   = np.array([float(np.mean(per[s])) for s in sites])    # kg/h
npd = np.array([len(per[s]) for s in sites])               # obs periods
tier= np.array(["I" if c >= 5e4 else ("II" if c >= 2e4 else "III") for c in x])

# ---- stats ----
rho, prho = stats.spearmanr(x, y)
lx, ly = np.log10(x), np.log10(y)
slope, inter, r, p, se = stats.linregress(lx, ly)
r2 = r**2

# ---- figure ----
fig, ax = plt.subplots(figsize=(3.95, 3.45))
fig.subplots_adjust(left=0.145, right=0.965, top=0.925, bottom=0.135)

# tier-boundary guides
for xb in (2e4, 5e4):
    ax.axvline(xb, color=MID, lw=0.6, ls=(0, (4, 3)), alpha=0.5, zorder=1)
ax.text(math.sqrt(1e3 * 2e4), 0.155, "III", ha="center", va="bottom", fontsize=6.4,
        color=TIER_COL["III"], fontweight="bold")
ax.text(math.sqrt(2e4 * 5e4), 0.155, "II", ha="center", va="bottom", fontsize=6.4,
        color=TIER_COL["II"], fontweight="bold")
ax.text(math.sqrt(5e4 * 1.2e6), 0.155, "I", ha="center", va="bottom", fontsize=6.4,
        color=TIER_COL["I"], fontweight="bold")

# fit line + 95% band (over log-x grid)
xx = np.linspace(lx.min(), lx.max(), 100)
yy = inter + slope * xx
n = len(lx); sx = np.sum((lx - lx.mean())**2)
tval = stats.t.ppf(0.975, n - 2)
band = tval * np.sqrt(np.sum((ly - (inter + slope*lx))**2)/(n-2)) * \
       np.sqrt(1.0/n + (xx - lx.mean())**2 / sx)
ax.fill_between(10**xx, 10**(yy - band), 10**(yy + band),
                color=INK, alpha=0.08, lw=0, zorder=2)
ax.plot(10**xx, 10**yy, color=INK, lw=1.3, zorder=5)

# points: colour by tier, size by n obs periods
def area(nn): return 22 + 12 * (nn - 1)
for t in ("III", "II", "I"):                     # draw light stone first, teal last
    m = tier == t
    ax.scatter(x[m], y[m], s=area(npd[m]), c=TIER_COL[t],
               edgecolors="white" if t != "III" else INK,
               linewidths=0.6 if t != "III" else 0.4, alpha=0.9, zorder=4)

# axes
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(7e2, 1.4e6); ax.set_ylim(0.14, 95)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.xaxis.set_major_locator(FixedLocator([1e3, 1e4, 1e5, 1e6]))
ax.xaxis.set_minor_locator(NullLocator())
ax.set_xticklabels([r"$10^3$", r"$10^4$", r"$10^5$", r"$10^6$"])
ax.yaxis.set_major_locator(FixedLocator([0.2, 0.5, 1, 2, 5, 10, 20, 50]))
ax.yaxis.set_minor_locator(NullLocator())
ax.set_yticklabels(["0.2", "0.5", "1", "2", "5", "10", "20", "50"])
ax.tick_params(length=3, width=0.8, labelsize=6.6)
ax.set_xlabel("Treatment capacity  (m$^3$ d$^{-1}$, log scale)", fontsize=7.2, color=INK)
ax.set_ylabel("Measured CH$_4$ emission rate  (kg h$^{-1}$, log scale)", fontsize=7.2, color=INK)

# stats box (upper-left, data trends up-right); consistent with the caption at n=105
txt = ("Spearman $\\rho$ = %.2f  (p < 10$^{-11}$)\n"
       "log-log slope = %.2f,  $R^2$ = %.2f\n"
       "n = %d plants  (%d obs. periods)") % (
       rho, slope, r2, len(sites), sum(len(v) for v in per.values()))
ax.text(0.035, 0.975, txt, transform=ax.transAxes, ha="left", va="top",
        fontsize=6.3, color=INK,
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=MID, lw=0.6, alpha=0.9))

# tier colour legend (compact, tucked into the empty bottom-right corner)
tier_handles = [Line2D([0],[0], marker="o", ls="", mfc=TIER_COL[t],
                mec="white" if t!="III" else INK, mew=0.4, ms=4.2,
                label={"I":"Tier I  (\u22655\u00d710$^4$)","II":"Tier II  (2\u20135\u00d710$^4$)",
                       "III":"Tier III  (<2\u00d710$^4$)"}[t]) for t in ("I","II","III")]
leg1 = ax.legend(handles=tier_handles, loc="lower right", bbox_to_anchor=(1.0, 0.145),
                 fontsize=4.6, frameon=False, handletextpad=0.3, labelspacing=0.22,
                 borderaxespad=0.2, title="plant size tier", title_fontsize=4.9)
ax.add_artist(leg1)

# size key (n obs periods)
size_handles = [Line2D([0],[0], marker="o", ls="", mfc=MID, mec="white", mew=0.4,
                ms=(math.sqrt(area(k))/math.sqrt(math.pi)*1.0) * 0.62, label="%d"%k) for k in (1,3,13)]
ax.legend(handles=size_handles, loc="lower right", bbox_to_anchor=(1.0, 0.0),
          fontsize=4.6, frameon=False, handletextpad=0.4, labelspacing=0.3,
          title="obs. periods", title_fontsize=4.9, borderpad=0.25, borderaxespad=0.2)

stem = os.path.join(HERE, "FigureS2")
fig.savefig(stem + ".png", dpi=600, bbox_inches="tight")
fig.savefig(stem + ".pdf", bbox_inches="tight")
print("wrote FigureS2.{png,pdf} | rho=%.3f slope=%.3f R2=%.3f n=%d" %
      (rho, slope, r2, len(sites)))
