#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure 4 - Resource cascade and tiered deployment.
THEORETICAL --(tiered conversion; Tier I amplifies)--> RECOVERABLE --> VALUE LADDER.
A hand-built alluvial: Tier I's scale carries it across the whole value ladder
(CHP -> biomethane -> single-cell protein); smaller tiers reach lower rungs.

Colour semantics (harmonised with Figures 1-3):
  Tier I  = deep teal #2C5A6B,  Tier II = clay #C08A5E,  Tier III = stone #CBC7BC.
  The value ladder is Tier I's high-value destination, so its rungs use a TEAL
  gradient (pale -> deep = low -> high value); the clay hue is reserved for
  Tier II throughout, avoiding any clash with the value column.

Self-contained: numpy, pandas, matplotlib. Reads fig1_plants.csv beside it
(tier + ch4_y) and applies the recoverable model (AD coverage 0.65/0.35/0.15,
biogas utilisation 0.60, operating rate 0.80). Writes Figure4.png / .pdf.
"""
import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, PathPatch, FancyBboxPatch
from matplotlib.path import Path

HERE = os.path.dirname(os.path.abspath(__file__))

mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'Liberation Sans', 'DejaVu Sans'],
    'svg.fonttype': 'none', 'pdf.fonttype': 42, 'mathtext.default': 'regular',
})
# palette harmonised with Figures 1-3
TCOL = {'I': '#2C5A6B', 'II': '#C08A5E', 'III': '#CBC7BC'}
C_INK, C_MID, C_LIGHT = '#2F3337', '#8C9094', '#D9D9D7'
TEDGE3 = '#9A968C'
# value ladder: teal gradient, pale (low value) -> deep (high value)
RUNG = {'CHP': '#B7C9CF', 'BIO': '#7BA0AB', 'SCP': '#2C5A6B'}

# ---- data: tier sums + recoverable model ------------------------------------
df = pd.read_csv(os.path.join(HERE, 'fig1_plants.csv'), encoding='utf-8-sig')
g = df.groupby('tier')['ch4_y'].sum(); tot = g.sum()
adcov, biogas, oprate = {'I': 0.65, 'II': 0.35, 'III': 0.15}, 0.60, 0.80
rec = {t: g[t] * adcov[t] * biogas * oprate for t in ['I', 'II', 'III']}
rtot = sum(rec.values())
theo = {t: 100 * g[t] / tot for t in ['I', 'II', 'III']}
actS = {t: 100 * rec[t] / rtot for t in ['I', 'II', 'III']}
npl = {t: int((df.tier == t).sum()) for t in ['I', 'II', 'III']}
recpct = 100 * rtot / tot
theo_1e8 = tot * 1e4 / 1e8       # deterministic national total (matches the caption)


def ribbon(ax, x0, x1, y0t, y0b, y1t, y1b, fc, alpha=0.80, z=3):
    mx = (x0 + x1) / 2
    V = [(x0, y0t), (mx, y0t), (mx, y1t), (x1, y1t), (x1, y1b),
         (mx, y1b), (mx, y0b), (x0, y0b), (x0, y0t)]
    C = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.LINETO,
         Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(V, C), fc=fc, ec='none', alpha=alpha, zorder=z))


fig, ax = plt.subplots(figsize=(7.6, 4.15))
ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis('off')
yT, yB = 7.45, 1.35; H = yT - yB
xTb0, xTb1 = 1.85, 2.18
xRb0, xRb1 = 4.20, 4.53
xVe, xVw = 6.05, 8.92
Lb = {}; y = yT
for t in ['I', 'II', 'III']:
    h = theo[t] / 100 * H; Lb[t] = (y - h, y); y -= h
Rb = {}; y = yT
for t in ['I', 'II', 'III']:
    h = actS[t] / 100 * H; Rb[t] = (y - h, y); y -= h
Vb = {'I': (3.45, 7.02), 'II': (2.30, 3.25), 'III': (1.50, 1.92)}

# stage 1: theoretical -> recoverable (taper => amplification)
for t in ['III', 'II', 'I']:
    ribbon(ax, xTb1, xRb0, Lb[t][1], Lb[t][0], Rb[t][1], Rb[t][0], TCOL[t])
# stage 2: recoverable -> value band
for t in ['III', 'II', 'I']:
    ribbon(ax, xRb1, xVe, Rb[t][1], Rb[t][0], Vb[t][1], Vb[t][0], TCOL[t], alpha=0.55)
# bars
for t in ['I', 'II', 'III']:
    ax.add_patch(mpatches.Rectangle((xTb0, Lb[t][0]), xTb1 - xTb0, Lb[t][1] - Lb[t][0],
                 fc=TCOL[t], ec='white', lw=1.0, zorder=5))
    ax.add_patch(mpatches.Rectangle((xRb0, Rb[t][0]), xRb1 - xRb0, Rb[t][1] - Rb[t][0],
                 fc=TCOL[t], ec='white', lw=1.0, zorder=5))

# ---- value column: Tier I ladder (teal rungs, deepening upward) --------------
rungs = [('CHP', 'heat + power', 3.95, RUNG['CHP']),
         ('Pipeline biomethane', 'grid / vehicle fuel', 5.00, RUNG['BIO']),
         ('Single-cell protein', 'aquafeed', 6.05, RUNG['SCP'])]
ax.add_patch(FancyBboxPatch((xVe + 0.10, Vb['I'][0]), xVw - xVe - 0.10, Vb['I'][1] - Vb['I'][0],
             boxstyle='round,pad=0.02,rounding_size=0.10', fc='#F6F5F2', ec=TCOL['I'], lw=1.1, zorder=5))
ax.text(xVe + 0.30, Vb['I'][1] - 0.22, 'Tier I \u00b7 independent recovery', ha='left', va='center',
        fontsize=6.3, fontweight='bold', color=TCOL['I'], zorder=7)
ax.text(xVe + 0.30, Vb['I'][1] - 0.45, f"{npl['I']} plants", ha='left', va='center',
        fontsize=6.0, color=C_MID, zorder=7)
ax.add_patch(FancyArrowPatch((xVe + 0.45, 3.70), (xVe + 0.45, 6.35), arrowstyle='-|>',
             mutation_scale=10, lw=1.0, color=TCOL['I'], alpha=0.8, zorder=6))
for nm, sub, yy, fc in rungs:
    ax.add_patch(mpatches.Rectangle((xVe + 0.24, yy - 0.28), 0.42, 0.56, fc=fc, ec='white', lw=0.8, zorder=6))
    ax.text(xVe + 0.82, yy + 0.08, nm, ha='left', va='center',
            fontsize=7.4 if nm.startswith('Single') else 7.0, fontweight='bold', color=C_INK, zorder=6)
    ax.text(xVe + 0.82, yy - 0.20, sub, ha='left', va='center', fontsize=6.0, color=C_MID, style='italic', zorder=6)
# Tier II / III destination pills
for t, lbl, sub, fcp in [('II', 'CHP \u00b7 biogas \u2192 heat + power', f"Tier II \u00b7 regional synergy \u00b7 {npl['II']} plants", '#F0E7DE'),
                         ('III', 'Sludge hauled to hub', f"Tier III \u00b7 centralized disposal \u00b7 {npl['III']} plants", '#EEEDE9')]:
    b, tp = Vb[t]
    ax.add_patch(FancyBboxPatch((xVe + 0.10, b), xVw - xVe - 0.10, tp - b,
                 boxstyle='round,pad=0.02,rounding_size=0.08', fc=fcp,
                 ec=(TEDGE3 if t == 'III' else TCOL['II']), lw=1.1, zorder=6))
    if t == 'II':
        ax.text(xVe + 0.30, (b + tp) / 2 + 0.20, lbl, ha='left', va='center', fontsize=6.9, fontweight='bold', color=C_INK, zorder=7)
        ax.text(xVe + 0.30, (b + tp) / 2 - 0.18, sub, ha='left', va='center', fontsize=5.9, color=C_MID, zorder=7)
    else:
        ax.text(xVe + 0.30, (b + tp) / 2, sub, ha='left', va='center', fontsize=6.2, fontweight='bold', color=C_INK, zorder=7)

# headers (neutral stage labels)
ax.text((xTb0 + xTb1) / 2, yT + 0.60, 'THEORETICAL', ha='center', va='center', fontsize=7.2, fontweight='bold', color=C_INK)
ax.text((xTb0 + xTb1) / 2, yT + 0.31, f'{theo_1e8:.2f}\u00d710$^8$ Nm$^3$ yr$^{{-1}}$', ha='center', va='center', fontsize=6.1, color=C_MID)
ax.text((xRb0 + xRb1) / 2, yT + 0.60, 'RECOVERABLE', ha='center', va='center', fontsize=7.2, fontweight='bold', color=C_INK)
ax.text((xRb0 + xRb1) / 2, yT + 0.31, f'{rtot * 1e4 / 1e8:.2f}\u00d710$^8$ \u00b7 {recpct:.0f}%', ha='center', va='center', fontsize=6.1, color=C_MID)
ax.text((xVe + xVw) / 2, yT + 0.60, 'VALUE LADDER', ha='center', va='center', fontsize=7.2, fontweight='bold', color=TCOL['I'])
ax.text((xVe + xVw) / 2, yT + 0.31, 'value per unit CH$_4$  \u2191', ha='center', va='center', fontsize=6.1, color=C_MID, style='italic')

# left tier + theoretical share
for t in ['I', 'II', 'III']:
    yc = (Lb[t][0] + Lb[t][1]) / 2
    ax.text(xTb0 - 0.20, yc + 0.13, 'Tier ' + t, ha='right', va='center',
            fontsize=8.6 if t == 'I' else 7.6, fontweight='bold', color=TCOL[t])
    ax.text(xTb0 - 0.20, yc - 0.15, f'{theo[t]:.1f}%', ha='right', va='center', fontsize=6.1, color=C_MID)
# recoverable punchline + amplification
ax.text((xRb0 + xRb1) / 2, (Rb['I'][0] + Rb['I'][1]) / 2, f"{actS['I']:.0f}%", ha='center', va='center',
        fontsize=8.2, fontweight='bold', color='white', zorder=6)
ax.text(2.85, 8.85, f"Tier I share amplifies  {theo['I']:.1f}% \u2192 {actS['I']:.1f}%  (+{round(actS['I'],1)-round(theo['I'],1):.1f} pp)",
        ha='left', va='center', fontsize=6.5, fontweight='bold', color=TCOL['I'])

fig.tight_layout()
stem = os.path.join(HERE, 'Figure4')
for ext in ('png', 'pdf'):
    fig.savefig(f'{stem}.{ext}', dpi=600, bbox_inches='tight')
print('wrote Figure4.{png,pdf} | theo=%s | rec Tier I=%.1f%% | rec total=%.2fe8 (%.0f%%) | n=%s'
      % ({t: round(theo[t], 1) for t in theo}, actS['I'], rtot * 1e4 / 1e8, recpct, npl))
