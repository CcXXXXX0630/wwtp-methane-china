Figure 1 - reproducible package
===============================

Contents
    figure1_map.py     self-contained plotting script (no external modules)
    fig1_plants.csv    input data: 2,457 above-ground WWTPs
                       columns: prov, city, lon, lat, scale, proc, tier, ch4_d, ch4_y
    gis_shapefiles/    WGS84 boundary shapefiles
                       国家 (national) / 省 (provinces) / 九段线 (nine-dash line)
    Figure1.png        output, 600 dpi raster
    Figure1.pdf        output, vector (editable text, pdf.fonttype=42)

Run
    pip install numpy pandas matplotlib pyshp pyproj
    python figure1_map.py

Paths are resolved relative to the script, so it runs from any working
directory. It regenerates Figure1.png and Figure1.pdf next to itself.
The random jitter applied to plant coordinates uses a fixed seed (42), so
output is bit-for-bit reproducible.

Caption (attribution belongs here, not on the canvas)
    Figure 1. Spatial distribution of theoretical CH4 potential across 2,457
    above-ground municipal WWTPs in China. Symbol area scales with the square
    root of plant-level CH4 potential; colours denote deployment tier by design
    capacity. Base map: standard map GS(2019)1686, Standard Map Service,
    Ministry of Natural Resources of China (boundaries unmodified).
