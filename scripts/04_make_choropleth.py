"""
Render the under-5 mortality choropleth to figures/mortality_choropleth.png.

Pure matplotlib: country polygons come from a world GeoJSON keyed by ISO3
code (downloaded once into data/raw/), filled with the sequential blue ramp.
We first tried plotly+kaleido, but its Chrome-based PNG export timed out
repeatedly on this machine, so the map is drawn natively instead.
"""
import json
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
NO_DATA = "#eceae3"
SEQ_BLUES = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
             "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
GEOJSON_URL = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
GEOJSON_PATH = os.path.join(ROOT, "data", "raw", "world_countries.geo.json")

# --- world geometry (download once, keep in data/raw for reproducibility) ---
if not os.path.exists(GEOJSON_PATH):
    print("Downloading world GeoJSON...")
    r = requests.get(GEOJSON_URL, timeout=120)
    r.raise_for_status()
    with open(GEOJSON_PATH, "wb") as f:
        f.write(r.content)
with open(GEOJSON_PATH, encoding="utf-8") as f:
    world = json.load(f)

latest = pd.read_csv(os.path.join(ROOT, "data", "clean", "country_latest.csv"))
mort = latest.set_index("iso3c")["under5_mortality_per_1000"]

cmap = LinearSegmentedColormap.from_list("seq_blues", SEQ_BLUES)
norm = Normalize(vmin=0, vmax=float(np.ceil(mort.max() / 10) * 10))

polys, colors = [], []
matched = set()
for feat in world["features"]:
    iso = feat.get("id")
    if iso == "ATA":  # Antarctica: no data, dominates the frame
        continue
    geom = feat["geometry"]
    rings = geom["coordinates"] if geom["type"] == "Polygon" else \
            [ring for part in geom["coordinates"] for ring in part]
    if geom["type"] == "MultiPolygon":
        parts = [p[0] for p in geom["coordinates"]]   # outer ring of each part
    else:
        parts = [geom["coordinates"][0]]
    if iso in mort.index and pd.notna(mort[iso]):
        c = cmap(norm(mort[iso]))
        matched.add(iso)
    else:
        c = NO_DATA
    for ring in parts:
        polys.append(np.asarray(ring))
        colors.append(c)

fig, ax = plt.subplots(figsize=(11, 5.6))
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)
ax.add_collection(PolyCollection(polys, facecolors=colors,
                                 edgecolors=SURFACE, linewidths=0.4))
ax.set_xlim(-180, 180)
ax.set_ylim(-60, 85)
ax.set_aspect(1.15)  # mild vertical compression ~ plate carree at mid-latitudes
ax.set_axis_off()

ax.set_title("Under-5 mortality by country, 2023",
             loc="left", fontsize=15, fontweight="bold", color=INK,
             fontfamily="Segoe UI", pad=18)
ax.text(0, 1.015, "Deaths before age 5 per 1,000 live births · gray = no data",
        transform=ax.transAxes, fontsize=9.5, color=INK2, fontfamily="Segoe UI")

sm = ScalarMappable(norm=norm, cmap=cmap)
cbar = fig.colorbar(sm, ax=ax, shrink=0.65, pad=0.01, aspect=28)
cbar.outline.set_visible(False)
cbar.ax.tick_params(color=MUTED, labelcolor=MUTED, labelsize=9, length=0)
cbar.set_label("deaths per 1,000", color=INK2, fontsize=9.5, fontfamily="Segoe UI")

out = os.path.join(ROOT, "figures", "mortality_choropleth.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
fig.savefig(out, dpi=200, bbox_inches="tight", facecolor=SURFACE)
print(f"Saved {out} - {len(matched)} of {mort.notna().sum()} countries matched to map geometry")
