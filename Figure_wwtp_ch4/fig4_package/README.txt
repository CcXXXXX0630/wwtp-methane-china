Figure 4 - corrected header (deterministic national total)
==========================================================

WHAT WAS WRONG
--------------
The figure printed the Monte Carlo median (7.04e8) as the THEORETICAL header,
while every ribbon, tier share and the "27%" recovery rate in the same figure
were computed from the deterministic total (7.32e8). The figure was therefore
internally inconsistent: 2.00 / 7.04 = 28.4%, not 27%.
The Figure 4 caption in 03_Figures.docx already says 7.32e8 (deterministic),
so the caption was right and the figure was wrong.

WHAT CHANGED IN figure4.py (3 lines, no change to any plotted geometry)
-----------------------------------------------------------------------
line 32   font fallback reordered: Liberation Sans placed before DejaVu Sans.
          Arial still comes first, so this has no effect on a machine that has
          Arial. It only makes the fallback closer to Arial elsewhere.

line 52   -  MC_MED = 7.04
          +  theo_1e8 = tot * 1e4 / 1e8   # deterministic national total

line 123  -  f'{MC_MED:.2f}\u00d710$^8$ Nm$^3$ yr$^{{-1}}$'
          +  f'{theo_1e8:.2f}\u00d710$^8$ Nm$^3$ yr$^{{-1}}$'

The THEORETICAL header now reads 7.32x10^8 Nm3 yr-1 and matches both the
caption and the 27% shown on the RECOVERABLE header.

HOW TO RUN LOCALLY
------------------
Put figure4.py and fig1_plants.csv in the same folder, then:

    python figure4.py

Requires numpy, pandas, matplotlib only. Writes Figure4.png and Figure4.pdf
at 600 dpi into the same folder.

Expected console output:
    wrote Figure4.{png,pdf} | theo={'I': 75.6, 'II': 20.2, 'III': 4.2}
    | rec Tier I=86.4% | rec total=2.00e8 (27%) | n={'I': 724, 'II': 1004, 'III': 729}

Expected image size: 4500 x 2430 px at 600 dpi.

IMPORTANT - RUN THIS LOCALLY, DO NOT USE THE BUNDLED PNG FOR SUBMISSION
-----------------------------------------------------------------------
The bundled Figure4.png was rendered on a machine WITHOUT Arial, so it fell
back to Liberation Sans (Arial-metric-compatible: identical layout and identical
4500x2430 output size, but slightly different glyph outlines). Compared with the
Figure 4 currently embedded in 03_Figures.docx, about 0.47% of pixels differ,
all of it on text glyphs.

Your original Figure 4 was rendered with Arial, and Figures 1-3 were too. So the
bundled PNG is a verification render only. Re-run figure4.py on your own machine
to get an Arial version that is consistent with the rest of the figure set.

WHAT TO CHANGE IN 03_Figures.docx
---------------------------------
Replace the Figure 4 image only. The Figure 4 caption needs NO edit: it already
reads "7.32 x 10^8 Nm3 yr-1, deterministic estimate" and "2.00 x 10^8 Nm3 yr-1,
27.3%", both of which now match the corrected figure.
