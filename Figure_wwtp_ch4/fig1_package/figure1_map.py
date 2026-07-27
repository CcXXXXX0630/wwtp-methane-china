#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure 1 - Spatial distribution of theoretical CH4 potential across 2,457
above-ground municipal WWTPs in China.  SELF-CONTAINED, LOCALLY RUNNABLE.

Run
---
    pip install numpy pandas matplotlib pyshp pyproj
    python figure1_map.py

It reads only files shipped alongside this script (paths are resolved relative
to the script itself, so it runs from any working directory):

    figure1_map.py            <- this file
    fig1_plants.csv           <- 2,457 plants (prov,city,lon,lat,scale,proc,tier,ch4_d,ch4_y)
    gis_shapefiles/           <- boundary shapefiles (WGS84)
        国家.shp / .shx / .dbf / .prj / .cpg      national polygon
        省.shp   / .shx / .dbf / .prj / .cpg      province polylines
        九段线.shp / .shx / .dbf / .prj / .cpg     nine-dash line

and writes Figure1.png (600 dpi) + Figure1.pdf (vector) next to itself.

Design notes
------------
* Symbol encoding: matplotlib scatter takes s = (marker diameter in points)^2.
  The map uses s = SCALE * sqrt(v): symbol AREA scales with sqrt(potential),
  RADIUS with potential^0.25 (a strong compression, needed because plant-level
  CH4 potential spans ~5 orders of magnitude). The legend draws circles of
  radius sqrt(s)/2 in points, so legend circles are the EXACT size of the map
  symbols they key. The compression is disclosed in the legend.
* Legend values 10/100/1000 are log decades straddling the data median (12.5)
  to the maximum (1204); adjacent radii differ by a constant x1.78.
* Tier colour and symbol size are SEPARATE keys: tiers overlap heavily in CH4
  potential, so merging them into one object would misrepresent the data.
* Base-map attribution GS(2019)1686 belongs in the figure CAPTION, not on the
  canvas (see manuscript).
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Circle
from matplotlib.collections import LineCollection

try:
    import shapefile          # pyshp
    import pyproj
except ImportError as e:
    sys.exit("Missing dependency: %s\n  pip install pyshp pyproj" % e.name)

# --- paths (relative to this script) -----------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
PLANTS_CSV = os.path.join(HERE, "fig1_plants.csv")
GIS = os.path.join(HERE, "gis_shapefiles")
PROV, NINE, NATION = (os.path.join(GIS, "省"),
                      os.path.join(GIS, "九段线"),
                      os.path.join(GIS, "国家"))
for _p in [PLANTS_CSV, NATION + ".shp", PROV + ".shp", NINE + ".shp"]:
    if not os.path.exists(_p):
        sys.exit("Required input not found: %s\n"
                 "  Keep figure1_map.py, fig1_plants.csv and gis_shapefiles/ together."
                 % _p)

# --- publication styling (inlined; no external module needed) ----------------
mpl.rcParams["font.family"] = "sans-serif"
mpl.rcParams["font.sans-serif"] = ["Arial", "Helvetica", "DejaVu Sans", "Liberation Sans"]
mpl.rcParams["svg.fonttype"] = "none"       # editable text in SVG
mpl.rcParams["pdf.fonttype"] = 42           # editable TrueType in PDF
mpl.rcParams["mathtext.default"] = "regular"

C_INK, C_MID, C_LIGHT = "#2F3337", "#8C9094", "#D9D9D7"
LAND, GRID = "#F5F4F1", "#B4B2AD"
TCOL = {"I": "#2C5A6B", "II": "#C08A5E", "III": "#CBC7BC"}   # cool / warm / neutral
TEDGE = {"I": "white", "II": "white", "III": "#9A968C"}
C_SIZEKEY = "#8C9094"                        # size key is tier-agnostic
HALO = [pe.withStroke(linewidth=2.4, foreground="white")]

# --- China Albers Equal-Area conic -------------------------------------------
AEA = pyproj.CRS.from_proj4("+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 "
                            "+x_0=0 +y_0=0 +datum=WGS84 +units=m")
_TF = pyproj.Transformer.from_crs("EPSG:4326", AEA, always_xy=True)
def project(lon, lat):
    return _TF.transform(np.asarray(lon, float), np.asarray(lat, float))

def polygon_path(name):
    r = shapefile.Reader(name, encoding="utf-8"); verts, codes = [], []
    for sh in r.shapes():
        pts = np.asarray(sh.points, float)
        if not len(pts): continue
        parts = list(sh.parts) + [len(pts)]
        for i in range(len(sh.parts)):
            ring = pts[parts[i]:parts[i+1]]
            if len(ring) < 3: continue
            xs, ys = project(ring[:, 0], ring[:, 1])
            verts.append(np.column_stack([xs, ys]))
            codes += [Path.MOVETO] + [Path.LINETO]*(len(ring)-2) + [Path.CLOSEPOLY]
    return Path(np.vstack(verts), codes)

def line_segments(name):
    r = shapefile.Reader(name, encoding="utf-8"); segs = []
    for sh in r.shapes():
        pts = np.asarray(sh.points, float)
        if not len(pts): continue
        parts = list(sh.parts) + [len(pts)]
        for i in range(len(sh.parts)):
            ring = pts[parts[i]:parts[i+1]]
            if len(ring) < 2: continue
            xs, ys = project(ring[:, 0], ring[:, 1])
            segs.append(np.column_stack([xs, ys]))
    return segs

def proj_limits(lon0, lon1, lat0, lat1, padx=0.004, pady=0.006):
    lo = np.r_[np.linspace(lon0, lon1, 200), np.linspace(lon0, lon1, 200),
               np.full(200, lon0), np.full(200, lon1)]
    la = np.r_[np.full(200, lat0), np.full(200, lat1),
               np.linspace(lat0, lat1, 200), np.linspace(lat0, lat1, 200)]
    x, y = project(lo, la)
    dx, dy = (x.max()-x.min())*padx, (y.max()-y.min())*pady
    return (x.min()-dx, x.max()+dx), (y.min()-dy, y.max()+dy)

nation_path = polygon_path(NATION)
prov_segs = line_segments(PROV)
nine_segs = line_segments(NINE)

# --- plants ------------------------------------------------------------------
df = pd.read_csv(PLANTS_CSV)
df = df[(df["lon"] > 70) & (df["lat"] > 15)].copy()
rng = np.random.default_rng(42)                 # fixed seed -> reproducible jitter
df["jlon"] = df["lon"] + rng.normal(0, 0.18, len(df))
df["jlat"] = df["lat"] + rng.normal(0, 0.18, len(df))
df = df.sort_values("ch4_y")
df["px"], df["py"] = project(df["jlon"].values, df["jlat"].values)

SCALE = 10.5
def marker_s(v):                                # map encoding: s = (diameter in pt)^2
    return SCALE * np.sqrt(np.clip(v, 0, None))
def radius_pt(v):                               # exact radius of a map symbol, in points
    return np.sqrt(marker_s(v)) / 2.0
df["s"] = marker_s(df["ch4_y"].values)

MLON0, MLON1, MLAT0, MLAT1 = 73, 135, 15.5, 54
XLIM, YLIM = proj_limits(MLON0, MLON1, MLAT0, MLAT1)
_AR = (YLIM[1]-YLIM[0]) / (XLIM[1]-XLIM[0])
fig, ax = plt.subplots(figsize=(9.0, 9.0*_AR))

# graticule (subtle texture; no coordinate labels)
for lon in [80, 90, 100, 110, 120, 130]:
    la = np.linspace(MLAT0, MLAT1, 120); xs, ys = project(np.full_like(la, lon), la)
    ax.plot(xs, ys, color=GRID, lw=0.4, ls=(0, (1, 4)), zorder=1.2)
for lat in [20, 30, 40, 50]:
    lo = np.linspace(MLON0, MLON1, 120); xs, ys = project(lo, np.full_like(lo, lat))
    ax.plot(xs, ys, color=GRID, lw=0.4, ls=(0, (1, 4)), zorder=1.2)

ax.add_patch(PathPatch(nation_path, fc=LAND, ec="none", zorder=1))
ax.add_collection(LineCollection(prov_segs, colors=C_MID, linewidths=0.3, zorder=1.5))
ax.add_collection(LineCollection(nine_segs, colors=C_INK, linewidths=1.0, zorder=2.5))
for t in ["III", "II", "I"]:
    sub = df[df["tier"] == t]
    ax.scatter(sub["px"], sub["py"], s=sub["s"], c=TCOL[t],
               alpha=0.85 if t == "I" else (0.8 if t == "II" else 0.7),
               linewidths=0.28, edgecolors=TEDGE[t], zorder=4 if t == "I" else 3)

ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
ax.set_xticks([]); ax.set_yticks([])
for sp in ax.spines.values():
    sp.set_visible(False)

# --- South China Sea inset (nine-dash line) ----------------------------------
SX, SY = proj_limits(106, 123, 3, 23, padx=0.02, pady=0.02)
axin = ax.inset_axes([0.865, 0.045, 0.095, 0.238]); axin.set_facecolor("none")
axin.add_patch(PathPatch(nation_path, fc=LAND, ec="none", zorder=1))
axin.add_collection(LineCollection([s.copy() for s in prov_segs], colors=C_MID, linewidths=0.2, zorder=1.5))
axin.add_collection(LineCollection([s.copy() for s in nine_segs], colors=C_INK, linewidths=0.7, zorder=2.5))
axin.set_xlim(*SX); axin.set_ylim(*SY); axin.set_aspect("equal")
axin.set_xticks([]); axin.set_yticks([])
for sp in axin.spines.values():
    sp.set_visible(True); sp.set_linewidth(0.5); sp.set_color(C_LIGHT)

fig.tight_layout()

# =============================================================================
# LEGEND - point-calibrated: the inset is sized so 1 data unit == 1 point, so a
# circle of radius sqrt(s)/2 is exactly the size of the map symbol of area s.
# Docked directly above the (shrunk) South China Sea inset so the two form one
# compact information block in the bottom-right, clear of the eastern-China
# data cluster; rest of the map (esp. bottom-left) stays clear for data.
# =============================================================================
LW_PT, LH_PT = 100.0, 176.0
_pp = ax.get_position()
_axw_pt = _pp.width * fig.get_figwidth() * 72.0
_axh_pt = _pp.height * fig.get_figheight() * 72.0
_ain_x0, _ain_y0, _ain_w, _ain_h = 0.865, 0.045, 0.095, 0.238
_axG_w, _axG_h = LW_PT/_axw_pt, LH_PT/_axh_pt
axG = ax.inset_axes([_ain_x0, _ain_y0 + _ain_h + 0.02,
                     _axG_w, _axG_h], zorder=6)
axG.set_xlim(0, LW_PT); axG.set_ylim(0, LH_PT)
axG.set_facecolor("none"); axG.axis("off")
for sp in axG.spines.values():
    sp.set_visible(False)

# ---- size key ----
axG.text(0, 171, "Plant CH$_4$ potential", fontsize=8.8, fontweight="bold",
         color=C_INK, va="center", ha="left", path_effects=HALO)
axG.text(0, 160.5, "\u00d710$^4$ m$^3$ yr$^{-1}$", fontsize=7.4, color=C_MID,
         va="center", ha="left", path_effects=HALO)
KEYS = [10, 100, 1000]
XC = [10.0, 32.0, 62.0]
YB = 130.0                                       # common baseline (bottom tangent)
axG.plot([2, 74], [YB, YB], color=C_LIGHT, lw=0.7, zorder=2,
         path_effects=[pe.withStroke(linewidth=2.0, foreground="white")])
for v, xc in zip(KEYS, XC):
    r = radius_pt(v)
    axG.add_patch(Circle((xc, YB + r), r, facecolor=C_SIZEKEY, alpha=0.8,
                         edgecolor="white", linewidth=0.28, zorder=3))
    axG.text(xc, 121.5, f"{v:,}", fontsize=7.6, color=C_INK, va="center",
             ha="center", path_effects=HALO)
axG.text(0, 110.5, "symbol area $\\propto$ potential$^{1/2}$",
         fontsize=6.9, color=C_MID, style="italic", va="center", ha="left",
         path_effects=HALO)

# ---- tier key ----
axG.text(0, 92, "Deployment tier", fontsize=8.8, fontweight="bold",
         color=C_INK, va="center", ha="left", path_effects=HALO)
axG.text(0, 81, "design capacity, \u00d710$^4$ m$^3$ d$^{-1}$", fontsize=7.1,
         color=C_MID, va="center", ha="left", path_effects=HALO)
for yy, k, name, val in zip([64, 46, 28], ["I", "II", "III"],
                            ["Tier I", "Tier II", "Tier III"],
                            ["$\\geq$5", "2\u20135", "<2"]):
    axG.scatter([5], [yy], s=48, c=TCOL[k], edgecolors=TEDGE[k],
                linewidths=0.45, zorder=4)
    axG.text(14, yy, name, fontsize=7.8, color=C_INK, va="center", ha="left",
             path_effects=HALO)
    axG.text(48, yy, val, fontsize=7.8, color=C_INK, va="center", ha="left",
             path_effects=HALO)

# --- save --------------------------------------------------------------------
out = os.path.join(HERE, "Figure1")
fig.savefig(out + ".png", dpi=600, bbox_inches="tight")
fig.savefig(out + ".pdf", bbox_inches="tight")
print("saved:", out + ".png  (600 dpi)")
print("saved:", out + ".pdf  (vector)")
print("legend radii (pt):", {v: round(float(radius_pt(v)), 2) for v in KEYS})
