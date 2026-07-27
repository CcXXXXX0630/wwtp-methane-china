#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure 2 - Concentration of the methane resource (spatial and by plant size).
  (a) provincial treemap: each province's box area = its share of national CH4;
      a handful of provinces dominate (top 5 = 48%; provincial Gini 0.52) -
      the SPATIAL axis of concentration.
  (b) Lorenz curve of plant-level CH4 potential (Gini + top-decile readout) -
      the overall concentration measure.
  (c) raincloud of every plant's CH4 potential by tier (half-violin density +
      raw points + tier-mean bar), log axis; each tier labelled with its share
      of CH4 - the plant-SIZE axis of concentration (size, not count).
All quantities are theoretical potential (recoverable amplification is Figure 4).
Self-contained; reads fig2_data.csv and fig1_province_totals_1e8m3yr.csv beside
it. Writes Figure2.png/.pdf (600 dpi).
"""
import os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap

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
TCOL = {'I': '#2C5A6B', 'II': '#C08A5E', 'III': '#CBC7BC'}
TDARK = {'I': '#2C5A6B', 'II': '#B07A4E', 'III': '#8C887E'}
C_INK, C_MID, C_LIGHT = '#2F3337', '#8C9094', '#D9D9D7'
TEAL_SEQ = LinearSegmentedColormap.from_list('tealseq', ['#D3E2E6', '#6E97A3', '#1E4350'])


def gini(x):
    x = np.sort(np.asarray(x, float)); n = len(x); c = np.cumsum(x)
    return (n + 1 - 2 * np.sum(c) / c[-1]) / n


def panel_label(ax, s, x, y=1.04):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=11,
            fontweight='bold', va='bottom', ha='left')


# ---- squarified treemap (Bruls et al. 2000; standard algorithm) -------------
def _layout(sizes, x, y, dx, dy):
    r = []
    if dx >= dy:
        w = sum(sizes) / dy; yy = y
        for s in sizes:
            r.append((x, yy, w, s / w)); yy += s / w
    else:
        h = sum(sizes) / dx; xx = x
        for s in sizes:
            r.append((xx, y, s / h, h)); xx += s / h
    return r


def _leftover(sizes, x, y, dx, dy):
    if dx >= dy:
        w = sum(sizes) / dy; return x + w, y, dx - w, dy
    h = sum(sizes) / dx; return x, y + h, dx, dy - h


def _worst(sizes, x, y, dx, dy):
    return max(max(w / h, h / w) for (_, _, w, h) in _layout(sizes, x, y, dx, dy))


def squarify(sizes, x, y, dx, dy):
    sizes = [float(s) for s in sizes]
    if len(sizes) <= 1:
        return _layout(sizes, x, y, dx, dy)
    i = 1
    while i < len(sizes) and _worst(sizes[:i], x, y, dx, dy) >= _worst(sizes[:i + 1], x, y, dx, dy):
        i += 1
    cur, rest = sizes[:i], sizes[i:]
    lx, ly, ldx, ldy = _leftover(cur, x, y, dx, dy)
    return _layout(cur, x, y, dx, dy) + squarify(rest, lx, ly, ldx, ldy)


df = pd.read_csv(os.path.join(HERE, 'fig2_data.csv'), encoding='utf-8-sig')
cap = df['capacity_1e4_m3_d'].values
ch4 = df['CH4_1e4_m3_yr'].values
tier = np.where(cap >= 5, 'I', np.where(cap >= 2, 'II', 'III'))

prov = pd.read_csv(os.path.join(HERE, 'fig1_province_totals_1e8m3yr.csv'), encoding='utf-8-sig')
prov = prov.sort_values('ch4_1e8_m3_yr', ascending=False).reset_index(drop=True)
ptot = prov['ch4_1e8_m3_yr'].sum()
prov['share'] = prov['ch4_1e8_m3_yr'] / ptot * 100
prov['name'] = prov['prov'].map(lambda s: ''.join(s.split()).capitalize())
p_gini = gini(prov['ch4_1e8_m3_yr'].values)
top5 = prov['share'].iloc[:5].sum()

fig, (axa, axb, axc) = plt.subplots(1, 3, figsize=(7.6, 2.55))

# =============== (a) provincial treemap : area = share of CH4 =================
rects = squarify(prov['share'].values / prov['share'].sum(), 0, 0, 1.0, 1.0)
smax = prov['share'].max()
for rank, ((rx, ry, rw, rh), sh, nm) in enumerate(zip(rects, prov['share'], prov['name'])):
    col = TEAL_SEQ(0.12 + 0.88 * (sh / smax) ** 0.62)
    axa.add_patch(plt.Rectangle((rx, ry), rw, rh, facecolor=col,
                                edgecolor='white', lw=0.8, zorder=3))
    if rank < 8 and rh > 0.12:                        # label the eight leading provinces
        cw_in = rw * 1.77
        fs = min(6.2 if sh > 8 else 5.7, cw_in * 0.90 * 72 / (max(len(nm), 1) * 0.58))
        txt = axa.text(rx + rw / 2, ry + rh / 2, f'{nm}\n{sh:.0f}%',
                       ha='center', va='center', zorder=4, linespacing=1.1,
                       fontsize=fs, fontweight='bold', color='white')
        txt.set_path_effects([pe.Stroke(linewidth=1.3, foreground='#173A45'),
                              pe.Normal()])
axa.set_xlim(0, 1); axa.set_ylim(0, 1)
axa.set_xticks([]); axa.set_yticks([])
axa.set_aspect('auto')
for sp in axa.spines.values():
    sp.set_visible(False)
panel_label(axa, 'a', x=-0.045)

# ============================ (b) Lorenz curve ===============================
xa = np.sort(ch4); n = len(xa)
cum = np.concatenate([[0], np.cumsum(xa) / xa.sum()])
pop = np.concatenate([[0], np.arange(1, n + 1) / n])
g = gini(ch4)
axb.fill_between(pop, cum, pop, color=TCOL['I'], alpha=0.12, linewidth=0)
axb.plot(pop, cum, color=TCOL['I'], lw=1.6, zorder=3)
axb.plot([0, 1], [0, 1], color=C_MID, lw=1.0, ls=(0, (4, 2)))
axb.set_xlim(0, 1); axb.set_ylim(0, 1)
axb.set_xticks([0, 0.5, 1.0]); axb.set_yticks([0, 0.5, 1.0])
axb.set_xlabel('Cumulative share of plants')
axb.set_ylabel('Cumulative share of CH$_4$')
axb.text(0.055, 0.905, f'Gini = {g:.3f}', fontsize=8.2, color=C_INK, fontweight='bold')
axb.text(0.055, 0.80, 'top 10% of plants\nhold 54% of CH$_4$',
         fontsize=6.4, color=C_MID, linespacing=1.3)
for sp in ('top', 'right'):
    axb.spines[sp].set_visible(False)
panel_label(axb, 'b', x=-0.20)

# ============ (c) raincloud: every plant's CH4 potential, by tier ============
tiers = ('I', 'II', 'III')
ch4d = ch4 * 1e4 / 365.0
npl = {t: int((tier == t).sum()) for t in tiers}
mean_d = {t: ch4d[tier == t].mean() for t in tiers}
csh = {t: ch4[tier == t].sum() / ch4.sum() * 100 for t in tiers}
centers = {'I': 1.0, 'II': 2.0, 'III': 3.0}
rng = np.random.default_rng(42)


def kde(samples, grid):
    s = np.std(samples); m = len(samples)
    bw = max(1.06 * s * m ** (-0.2), 1e-3)
    d = (grid[:, None] - samples[None, :]) / bw
    return np.exp(-0.5 * d * d).sum(1) / (m * bw * np.sqrt(2 * np.pi))


grid = np.linspace(np.log10(0.5), np.log10(3.3e4), 220)
yv = 10 ** grid
pos = ch4d > 0
logd = np.log10(np.where(pos, ch4d, 1.0))
Y_ZERO = 0.34
dens = {t: kde(logd[(tier == t) & pos], grid) for t in tiers}
maxd = max(v.max() for v in dens.values())
HALF = 0.34
for t in tiers:
    cx = centers[t]
    dv = dens[t] / maxd * HALF
    axc.fill_betweenx(yv, cx - dv, cx, facecolor=TCOL[t], alpha=0.22, lw=0, zorder=2)
    axc.plot(cx - dv, yv, color=TCOL[t], lw=0.7, alpha=0.75, zorder=2)
    mp = (tier == t) & pos
    xx = cx + 0.045 + rng.uniform(0, 0.275, size=mp.sum())
    axc.scatter(xx, ch4d[mp], s=4.2, color=TCOL[t], alpha=0.38, edgecolors='none', zorder=3)
    mz = (tier == t) & (~pos)
    if mz.sum():
        xz = cx + 0.045 + rng.uniform(0, 0.275, size=mz.sum())
        axc.scatter(xz, np.full(mz.sum(), Y_ZERO), s=3.0, color=TCOL[t],
                    alpha=0.30, edgecolors='none', zorder=3)
    mb = mean_d[t]
    axc.plot([cx - HALF, cx + 0.32], [mb, mb], color=TDARK[t], lw=1.5,
             solid_capstyle='round', zorder=5,
             path_effects=[pe.Stroke(linewidth=2.8, foreground='white'), pe.Normal()])
axc.set_yscale('log')
axc.set_ylim(0.22, 1.7e5)
axc.set_yticks([1, 10, 100, 1000, 10000])
axc.set_yticklabels(['$10^0$', '$10^1$', '$10^2$', '$10^3$', '$10^4$'])
axc.set_xlim(0.42, 3.62)
axc.set_xticks([1, 2, 3])
axc.set_xticklabels([f'Tier {t}\nn={npl[t]}' for t in tiers], fontsize=7)
for tl, t in zip(axc.get_xticklabels(), tiers):
    tl.set_color(TDARK[t])
axc.set_ylabel('Plant CH$_4$ potential (m$^3$ d$^{-1}$)')
tr = axc.get_xaxis_transform()
for t in tiers:
    axc.text(centers[t], 0.99, f'{int(csh[t] + 0.5)}%', transform=tr, ha='center', va='top',
             fontsize=8.2 if t == 'I' else 7.0, fontweight='bold', color=TDARK[t])
    axc.text(centers[t], 0.925, 'of CH$_4$', transform=tr, ha='center', va='top',
             fontsize=5.5, color=C_MID)
axc.text(0.975, 0.005, 'point = one plant   bar = tier mean',
         transform=axc.transAxes, ha='right', va='bottom', fontsize=5.0,
         color=C_MID, style='italic')
for sp in ('top', 'right'):
    axc.spines[sp].set_visible(False)
panel_label(axc, 'c', x=-0.30)

fig.subplots_adjust(left=0.052, right=0.985, top=0.88, bottom=0.205, wspace=0.5)

# --- panel b: 'line of equality' label parallel to the dashed diagonal --------
fig.canvas.draw()
q0 = axb.transData.transform((0.30, 0.30))
q1 = axb.transData.transform((0.70, 0.70))
ang = np.degrees(np.arctan2(q1[1] - q0[1], q1[0] - q0[0]))
axb.text(0.545, 0.60, 'line of equality', fontsize=5.9, color=C_MID, style='italic',
         rotation=ang, rotation_mode='anchor', ha='center', va='bottom')

# --- panel a: subtitles, auto-shrunk so they never overflow the panel width ---
aw = axa.get_window_extent().width


def fit_text(y, s, fs0, **kw):
    t = axa.text(0.5, y, s, transform=axa.transAxes, ha='center', va='top', fontsize=fs0, **kw)
    fig.canvas.draw()
    while t.get_window_extent().width > aw * 0.99 and t.get_fontsize() > 4.3:
        t.set_fontsize(t.get_fontsize() - 0.2); fig.canvas.draw()


fit_text(-0.045, f'Top 5 provinces = {top5:.1f}% of CH$_4$', 6.1, color=C_INK)
fit_text(-0.140, f'box area = share  \u00b7  provincial Gini {p_gini:.2f}',
         5.5, color=C_MID, style='italic')

stem = os.path.join(HERE, 'Figure2')
for ext in ('png', 'pdf'):
    fig.savefig(f'{stem}.{ext}', dpi=600, bbox_inches='tight')
print('wrote Figure2.{png,pdf} | prov Gini=%.3f top5=%.1f%% | plant Gini=%.4f | tier CH4%%=%s'
      % (p_gini, top5, g, [round(csh[t], 1) for t in tiers]))
