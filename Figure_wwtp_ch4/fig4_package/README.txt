Figure 4 - reproducible package
===============================

Contents
    figure4.py       self-contained plotting script (no external modules)
    fig1_plants.csv  input data: 2,457 above-ground WWTPs (tier + ch4_y are used;
                     the file also carries prov/city/lon/lat/scale/proc/ch4_d)
    Figure4.png      output, 600 dpi raster
    Figure4.pdf      output, vector (editable text, pdf.fonttype=42)

Run
    pip install numpy pandas matplotlib
    python figure4.py

Paths are resolved relative to the script, so it runs from any working
directory. It regenerates Figure4.png and Figure4.pdf next to itself.
Output is deterministic (no random component).

What the script computes
    Tier CH4 sums come straight from fig1_plants.csv. The recoverable model is
    applied per plant:
        recoverable = theoretical  x  AD_coverage[tier]  x  biogas(0.60)  x  operating(0.80)
        AD_coverage = {Tier I 0.65, Tier II 0.35, Tier III 0.15}
    biogas x operating = 0.48 is tier-uniform, so it cancels in every share; the
    tier-differentiated AD coverage is what amplifies Tier I's share.

    Reproduces: theoretical shares 75.6 / 20.2 / 4.2 %; recoverable Tier I share
    86.4 %; recoverable total 2.00e8 Nm3/yr (27 % of theoretical); tier plant
    counts 724 / 1004 / 729. The theoretical headline total 7.04e8 Nm3/yr is the
    Monte-Carlo median (constant MC_MED in the script).

The figure
    A hand-built resource cascade: THEORETICAL -> RECOVERABLE -> VALUE LADDER.
    Tier I's scale carries it across the whole value ladder (CHP -> pipeline
    biomethane -> single-cell protein); Tier II reaches CHP; Tier III is hauled
    for centralized disposal. Tier I's share amplifies 75.6 % -> 86.4 % (+10.8 pp)
    from theoretical to recoverable.

Colour semantics (harmonised with Figures 1-3)
    Tier I = deep teal #2C5A6B, Tier II = clay #C08A5E, Tier III = stone #CBC7BC.
    The value ladder is Tier I's high-value destination, so its rungs use a TEAL
    gradient (pale -> deep = low -> high value); clay is reserved for Tier II
    throughout so the value column never clashes with a tier colour.

Caption (suggested)
    Figure 4. Tiered resource cascade from theoretical to recoverable methane and
    on to end-use value. A small number of large (Tier I) plants hold most of the
    recoverable methane and are the only ones whose scale supports the
    highest-value pathways.
