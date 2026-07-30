# WWTP Methane Concentration & Targeted Deployment

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15185301.svg)](https://doi.org/10.5281/zenodo.15185301)

Analysis code, data, and figure-generation scripts accompanying:

> Xiong, C., Tang, X., Fu, J., Liu, Y., Li, Q. *Concentrated distribution and targeted deployment of methane resources in China's municipal wastewater treatment plants.* Resources, Conservation & Recycling (2026).

## What's here

| Directory | Contents |
|---|---|
| `wwtp_ch4_analysis/` | Core model (`wwtp_model.py`), Monte Carlo, distribution fitting, recoverable analysis. `run_all.py` reproduces every quantitative result. |
| `Figure_wwtp_ch4/fig1_package/` | Figure 1 — spatial bubble map (requires `cnmaps`) |
| `Figure_wwtp_ch4/fig2_package/` | Figure 2 — treemap + Lorenz + raincloud |
| `Figure_wwtp_ch4/fig3_package/` | Figure 3 — distribution fit + robustness |
| `Figure_wwtp_ch4/fig4_package/` | Figure 4 — resource cascade |
| `Figure_wwtp_ch4/FigureS1_package/` | Figure S1 — cross-study comparison |
| `Figure_wwtp_ch4/FigureS2_package/` | Figure S2 — rank-correlation validation |

Each figure package is self-contained: a Python script reads a local CSV and writes `.png` + `.pdf`.

## Quick start

```bash
cd wwtp_ch4_analysis
pip install -r requirements.txt
python run_all.py          # ~90 seconds (2,000 MC iterations)
python run_all.py --quick  # 200 iterations, faster check
```

For individual figures:

```bash
cd Figure_wwtp_ch4/fig2_package
pip install -r ../wwtp_ch4_analysis/requirements.txt
python figure2.py
```

## Data

The primary WWTP dataset (`中国污水处理厂数据集.xlsx`) is from Zhou et al. (2024), *Scientific Data* 11, 941 (CC-BY). Sun et al. (2026) validation data are extracted from their *Science Advances* Supplementary Information. All derived CSVs are in the figure packages.

GIS boundary shapefiles are **not** included. Install `cnmaps` (`pip install cnmaps`) — it provides Chinese boundaries at runtime with the correct official basemap (审图号 GS(2019)1686).

## License

Code: MIT. Data: CC-BY-4.0 (attribution required; see `CITATION.cff`).

## Citation

```bibtex
@dataset{xiong2026wwtp,
  author = {Xiong, Can and Tang, Xifang and Fu, Jingwei and Liu, Yaqian and Li, Qian},
  title  = {Per-plant methane potential estimates and analysis code for China's above-ground municipal WWTPs},
  year   = {2026},
  doi    = {10.5281/zenodo.15185301},
}
```
