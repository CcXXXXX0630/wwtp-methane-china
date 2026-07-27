#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure 3 - Distribution and robustness of plant-level CH4 potential.
  (a) probability density of per-plant daily CH4 with the log-normal fit;
  (b) complementary CDF (log-log): the empirical tail follows the log-normal,
      not a power law (Vuong test prefers log-normal);
  (c) Monte-Carlo robustness: the national total is uncertain, whereas the
      Gini coefficient and the Tier-I share are nearly invariant;
  (d) parameter sensitivity (|Spearman rho| vs national total).

Colour semantics (harmonised with Figures 1-2):
  deep teal  #2C5A6B  = the fitted / robust quantities (log-normal, Gini, Tier-I);
  clay       #C08A5E  = the uncertain or dominant-driver quantities
                        (national total, eta_AD, Y_net; power-law reference);
  sand       #C2A06B  = secondary driver (k_CH4); stone #CBC7BC = negligible.

Self-contained: numpy, pandas, scipy, matplotlib. Reads the five CSVs beside it.
Writes Figure3.png / .pdf (600 dpi).
"""
import os
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib as mpl
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))

mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans', 'Liberation Sans'],
    'svg.fonttype': 'none', 'pdf.fonttype': 42,
    'axes.edgecolor': '#2F3337', 'axes.labelsize': 8,
    'xtick.labelsize': 7, 'ytick.labelsize': 7,
    'xtick.major.width': 0.7, 'ytick.major.width': 0.7,
    'xtick.major.size': 3, 'ytick.major.size': 3, 'axes.linewidth': 0.8,
    'legend.frameon': False, 'mathtext.default': 'regular',
})
# palette harmonised with Figures 1-2
C_FIT   = '#2C5A6B'   # deep teal  - fitted / robust
C_DRIVE = '#C08A5E'   # clay       - uncertain / dominant driver / power-law ref
C_GOLD  = '#C2A06B'   # sand       - secondary driver
C_STONE = '#CBC7BC'   # stone      - negligible
C_INK, C_MID, C_LIGHT = '#2F3337', '#8C9094', '#D9D9D7'


def panel_label(ax, s, x=-0.115, y=1.03):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=11,
            fontweight='bold', va='bottom', ha='left')


def csv(name):
    return pd.read_csv(os.path.join(HERE, name), encoding='utf-8-sig')


hist = csv('fig3a_pdf_hist.csv')
ccdf = csv('fig3b_ccdf.csv')
fit = csv('fig3_fit_stats.csv').set_index('parameter')['value']
mci = csv('fig3c_mc_indicators.csv').set_index('indicator')
sen = csv('fig3d_sensitivity.csv')

mu, sigma = float(fit['lognormal_mu']), float(fit['lognormal_sigma'])
alpha, xmin = float(fit['powerlaw_alpha']), float(fit['x_min_m3d'])
p_tail = float(fit['P_tail_ge_xmin'])

fig, ax = plt.subplots(2, 2, figsize=(7.2, 5.95))
axA, axB, axC, axD = ax[0, 0], ax[0, 1], ax[1, 0], ax[1, 1]

# ---- (a) PDF + log-normal density (log10 space) -----------------------------
left = hist['log10_ch4_left'].values
right = hist['log10_ch4_right'].values
dens = hist['density_per_decade'].values
axA.bar(left, dens, width=(right - left), align='edge', color=C_LIGHT,
        edgecolor='white', linewidth=0.4, zorder=1)
m10, s10 = mu / np.log(10), sigma / np.log(10)
tt = np.linspace(left.min(), right.max(), 400)
axA.plot(tt, stats.norm.pdf(tt, m10, s10), color=C_FIT, lw=2.0, zorder=3)
axA.axvline(m10, color=C_INK, ls=(0, (1, 1)), lw=0.9, zorder=2)
axA.set_xlabel('Plant-level CH$_4$ potential (m$^3$ d$^{-1}$)')
axA.set_ylabel('Probability density (per decade)')
axA.set_xlim(left.min(), right.max()); axA.set_ylim(0, None)
dec = np.arange(int(np.floor(left.min())), int(np.ceil(right.max())) + 1)
axA.set_xticks(dec); axA.set_xticklabels([f'$10^{{{d}}}$' for d in dec])
axA.text(0.96, 0.95, f'Log-normal fit\n$\\mu$={mu:.2f}, $\\sigma$={sigma:.2f}',
         transform=axA.transAxes, ha='right', va='top', fontsize=7.5,
         color=C_FIT, linespacing=1.3)
axA.annotate(f'geometric mean\n$e^{{\\mu}}$ = {np.exp(mu):,.0f} m$^3$ d$^{{-1}}$',
             xy=(m10, stats.norm.pdf(m10, m10, s10) * 0.60),
             xytext=(left.min() + 0.15, axA.get_ylim()[1] * 0.80),
             fontsize=7, color=C_INK, ha='left', va='center',
             arrowprops=dict(arrowstyle='-', color=C_MID, lw=0.7))
for sp in ('top', 'right'):
    axA.spines[sp].set_visible(False)
panel_label(axA, 'a')

# ---- (b) log-log CCDF + log-normal SF + power-law reference ------------------
x = ccdf['ch4_m3d'].values
y = ccdf['ccdf_P_X_gt_x'].values
n = len(x)
xx = np.logspace(np.log10(x.min()), np.log10(x.max()), 400)
axB.scatter(x, y, s=6, color=C_MID, alpha=0.42, edgecolors='none',
            zorder=2, label=f'Empirical (n = {n})')
axB.plot(xx, stats.lognorm.sf(xx, s=sigma, scale=np.exp(mu)),
         color=C_FIT, lw=2.0, zorder=4, label='Log-normal')
xpl = np.logspace(np.log10(xmin), np.log10(x.max()), 100)
axB.plot(xpl, p_tail * (xpl / xmin) ** (-(alpha - 1.0)),
         color=C_DRIVE, lw=1.8, ls=(0, (5, 2)), zorder=3,
         label=f'Power-law ($\\alpha$={alpha:.2f})')
axB.axvline(xmin, color=C_MID, lw=0.8, ls=(0, (1, 1.5)), zorder=1)
axB.set_xscale('log'); axB.set_yscale('log')
axB.set_xlabel('Plant-level CH$_4$ potential (m$^3$ d$^{-1}$)')
axB.set_ylabel('P($X>x$)')
axB.set_xlim(x.min(), x.max() * 1.1); axB.set_ylim(2e-4, 1.3)
axB.legend(loc='lower left', fontsize=7, handlelength=1.6, borderaxespad=0.3)
axB.text(0.04, 0.62, 'Vuong test:\nlog-normal preferred\n($p$ < 0.001)',
         transform=axB.transAxes, ha='left', va='center', fontsize=7.5,
         color=C_INK, linespacing=1.3)
for sp in ('top', 'right'):
    axB.spines[sp].set_visible(False)
panel_label(axB, 'b')

# ---- (c) Monte-Carlo relative spread ----------------------------------------
order = ['national_total_1e4m3yr', 'gini', 'tierI_share_pct']
labels = ['National\ntotal', 'Gini\ncoefficient', 'Tier-I\nshare']
cols = [C_DRIVE, C_FIT, C_FIT]                     # clay = uncertain, teal = robust
ys = np.arange(3)[::-1]
for yv, key, c in zip(ys, order, cols):
    lo, md, hi = mci.loc[key, ['p2.5', 'median', 'p97.5']].values
    r = np.array([lo, md, hi]) / md
    axC.plot([r[0], r[2]], [yv, yv], color=c, lw=5, solid_capstyle='round',
             alpha=0.5, zorder=2)
    axC.plot(1.0, yv, 'o', color=c, ms=8, zorder=3)
    axC.text(1.0, yv + 0.26, f'95% CI {100 * (hi - lo) / md:.1f}%',
             va='bottom', ha='center', fontsize=7, color=C_INK)
axC.axvline(1.0, color=C_MID, ls=(0, (2, 2)), lw=0.8, zorder=1)
axC.set_yticks(ys); axC.set_yticklabels(labels, fontsize=8)
for tl, c in zip(axC.get_yticklabels(), cols):
    tl.set_color(c)
axC.set_ylim(-0.6, 2.9); axC.set_xlim(0.70, 1.34)
axC.set_xlabel('Monte-Carlo value relative to median')
for sp in ('top', 'right'):
    axC.spines[sp].set_visible(False)
panel_label(axC, 'c')

# ---- (d) parameter sensitivity tornado --------------------------------------
sen2 = sen.sort_values('abs_spearman_vs_total', ascending=True)
names = sen2['parameter'].tolist()
vals = sen2['abs_spearman_vs_total'].tolist()
bc = [C_DRIVE if nm in ('eta_AD', 'Y_net') else
      (C_GOLD if nm == 'k_CH4' else C_STONE) for nm in names]
axD.barh(range(len(names)), vals, color=bc, height=0.68,
         edgecolor='white', linewidth=0.5, zorder=3)
for i, v in enumerate(vals):
    axD.text(v + 0.015, i, f'{v:.2f}', va='center', ha='left', fontsize=7,
             color=C_INK)
nice = {'eta_AD': '$\\eta_{AD}$', 'Y_net': '$Y_{net}$', 'k_CH4': '$k_{CH_4}$',
        'COD_impute': 'COD', 'VSS/DS': 'VSS/DS'}
axD.set_yticks(range(len(names)))
axD.set_yticklabels([nice.get(nm, nm) for nm in names], fontsize=9)
axD.set_xlim(0, 0.86); axD.set_xticks([0, 0.3, 0.6])
axD.set_xlabel('|Spearman $\\rho$| vs national total')
for sp in ('top', 'right'):
    axD.spines[sp].set_visible(False)
panel_label(axD, 'd')

fig.tight_layout(w_pad=2.2, h_pad=2.4)
stem = os.path.join(HERE, 'Figure3')
for ext in ('png', 'pdf'):
    fig.savefig(f'{stem}.{ext}', dpi=600, bbox_inches='tight')
print('wrote Figure3.{png,pdf} | mu=%.3f sigma=%.3f alpha=%.3f | MC CI%%: %s'
      % (mu, sigma, alpha,
         [round(100*(mci.loc[k,'p97.5']-mci.loc[k,'p2.5'])/mci.loc[k,'median'],1) for k in order]))
