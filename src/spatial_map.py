"""
Spatial view of the EW4All risk & readiness index
==================================================

Plots the composite index for the seven EW4All pilot countries on a longitude/latitude map
(bubble size & colour = index). Demonstrates handling and visualisation of spatial data — the
kind of GIS / geospatial step used in Climate Risk & Vulnerability Assessments (CRVA).

Coordinates are national-capital lat/lon (public, WGS84). Reads results/index.csv produced by
build_index.py. No heavy GIS dependency so it runs anywhere; swap in GeoPandas + a shapefile to
render full country polygons / choropleth.

Run:  python src/build_index.py && python src/spatial_map.py
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

# national-capital coordinates (lon, lat), WGS84
COORDS = {
    "ATG": (-61.85, 17.12), "KHM": (104.92, 11.56), "TCD": (15.06, 12.13),
    "ECU": (-78.47, -0.18), "ETH": (38.74, 9.03), "FJI": (178.44, -18.14),
    "SOM": (45.32, 2.05),
}


def main() -> None:
    df = pd.read_csv(RESULTS / "index.csv")
    df["lon"] = df["iso3"].map(lambda i: COORDS[i][0])
    df["lat"] = df["iso3"].map(lambda i: COORDS[i][1])

    fig, ax = plt.subplots(figsize=(11, 5.5))
    # light graticule as a simple spatial backdrop
    for x in range(-180, 181, 30):
        ax.axvline(x, color="#e8e8e8", lw=0.6, zorder=0)
    for y in range(-60, 91, 30):
        ax.axhline(y, color="#e8e8e8", lw=0.6, zorder=0)

    sizes = 60 + (df["INDEX_0_100"] / df["INDEX_0_100"].max()) * 900
    sc = ax.scatter(df["lon"], df["lat"], s=sizes, c=df["INDEX_0_100"],
                    cmap="YlOrRd", vmin=0, vmax=100, edgecolor="#333", linewidth=0.6, zorder=3)
    for _, r in df.iterrows():
        ax.annotate(f"{r['country']} ({r['INDEX_0_100']:.0f})",
                    (r["lon"], r["lat"]), textcoords="offset points", xytext=(8, 6),
                    fontsize=8, zorder=4)

    ax.set_xlim(-100, 190); ax.set_ylim(-40, 45)
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    ax.set_title("Spatial distribution of the EW4All Multi-Hazard Risk & Readiness Index\n"
                 "(bubble size & colour = index; national-capital coordinates)")
    fig.colorbar(sc, ax=ax, fraction=0.025, pad=0.02, label="Index (0–100)")
    fig.tight_layout()
    fig.savefig(RESULTS / "index_map.png", dpi=140)
    print(f"Saved {RESULTS/'index_map.png'}")


if __name__ == "__main__":
    main()
