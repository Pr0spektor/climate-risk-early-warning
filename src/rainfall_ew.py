"""
Rainfall early-warning demonstrator (live ERA5 reanalysis)
==========================================================

A working detection layer for EW4All Pillar 2 (observation/monitoring) and Pillar 3 (warning),
built on **real ERA5 reanalysis rainfall** served free (no key) by the Open-Meteo Historical
Weather API. For each EW4All pilot-country capital it flags:

  * FLOOD watch/warning — rolling 3-day rainfall accumulation exceeding the location's own
    historical p95 / p99 (climatological, self-calibrating percentile thresholds), and
  * DROUGHT flag — runs of consecutive "dry" days (< 1 mm) exceeding a configurable length.

Design notes
------------
* Thresholds are **relative to each site's own climatology** (percentiles), so the method
  transfers across very different rainfall regimes (Sahel vs Pacific) without hand-tuning —
  the same principle used in operational impact-based forecasting.
* Data is fetched **live** at run time (reproducible; nothing hard-coded). Run offline with
  `--selftest` to validate the alerting logic on a controlled synthetic series.

Usage
-----
    python src/rainfall_ew.py            # live: fetch ERA5 for the 7 capitals, write results/
    python src/rainfall_ew.py --selftest # offline: verify the detection logic

Source: Open-Meteo Historical Weather API (ERA5). https://open-meteo.com/
"""
from __future__ import annotations
import sys, json, urllib.request, urllib.parse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"; RESULTS.mkdir(exist_ok=True)

CAPITALS = {  # ISO3: (name, lat, lon)
    "ATG": ("Antigua and Barbuda", 17.12, -61.85), "KHM": ("Cambodia", 11.56, 104.92),
    "TCD": ("Chad", 12.13, 15.06), "ECU": ("Ecuador", -0.18, -78.47),
    "ETH": ("Ethiopia", 9.03, 38.74), "FJI": ("Fiji", -18.14, 178.44),
    "SOM": ("Somalia", 2.05, 45.32),
}
ACCUM_WINDOW = 3        # days of rolling accumulation for flood signal
DRY_MM = 1.0            # threshold defining a "dry" day
DROUGHT_RUN = 20        # consecutive dry days -> drought flag


def fetch_rainfall(lat: float, lon: float, start: str, end: str) -> pd.DataFrame:
    q = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
        "daily": "precipitation_sum", "timezone": "UTC",
    })
    url = f"https://archive-api.open-meteo.com/v1/archive?{q}"
    with urllib.request.urlopen(url, timeout=60) as r:
        d = json.loads(r.read().decode("utf-8"))
    return pd.DataFrame({"date": pd.to_datetime(d["daily"]["time"]),
                         "precip_mm": d["daily"]["precipitation_sum"]})


def detect(precip: np.ndarray, p95: float, p99: float):
    """Return (flood_level array in {0,1,2}, drought_flag boolean array)."""
    precip = np.nan_to_num(precip, nan=0.0)
    acc = pd.Series(precip).rolling(ACCUM_WINDOW, min_periods=1).sum().to_numpy()
    flood = np.where(acc >= p99, 2, np.where(acc >= p95, 1, 0))
    dry = precip < DRY_MM
    run = np.zeros(len(precip), dtype=int); c = 0
    for i, x in enumerate(dry):
        c = c + 1 if x else 0
        run[i] = c
    drought = run >= DROUGHT_RUN
    return flood, drought


def analyse(df: pd.DataFrame):
    p = df["precip_mm"].to_numpy()
    acc = pd.Series(np.nan_to_num(p)).rolling(ACCUM_WINDOW, min_periods=1).sum().to_numpy()
    p95, p99 = np.nanpercentile(acc, 95), np.nanpercentile(acc, 99)
    flood, drought = detect(p, p95, p99)
    return flood, drought, p95, p99


def run_live(years: int = 6):
    end = pd.Timestamp.utcnow().normalize() - pd.Timedelta(days=6)
    start = end - pd.Timedelta(days=365 * years)
    s, e = start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    rows, fig, axes = [], None, None
    fig, axes = plt.subplots(len(CAPITALS), 1, figsize=(11, 12), sharex=True)
    for ax, (iso, (name, lat, lon)) in zip(axes, CAPITALS.items()):
        try:
            df = fetch_rainfall(lat, lon, s, e)
        except Exception as ex:
            print(f"[warn] {name}: fetch failed ({ex})"); continue
        flood, drought, p95, p99 = analyse(df)
        ax.plot(df["date"], df["precip_mm"], lw=0.5, color="#3b6fb0")
        ax.scatter(df["date"][flood == 1], df["precip_mm"][flood == 1], s=8, color="#e8590c", label="flood watch")
        ax.scatter(df["date"][flood == 2], df["precip_mm"][flood == 2], s=14, color="#c92a2a", label="flood warning")
        if drought.any():
            ax.scatter(df["date"][drought], np.zeros(drought.sum()), s=6, color="#b8860b", marker="s", label="drought")
        ax.set_ylabel(iso); ax.grid(alpha=0.3)
        rows.append({"country": name, "days": len(df),
                     "flood_watch_days": int((flood == 1).sum()),
                     "flood_warning_days": int((flood == 2).sum()),
                     "drought_days": int(drought.sum()),
                     "p95_3day_mm": round(float(p95), 1), "p99_3day_mm": round(float(p99), 1)})
    axes[0].legend(loc="upper right", fontsize=7)
    axes[0].set_title(f"ERA5 daily rainfall with self-calibrating flood/drought alerts ({s} to {e})")
    fig.tight_layout(); fig.savefig(RESULTS / "rainfall_alerts.png", dpi=130)
    out = pd.DataFrame(rows); out.to_csv(RESULTS / "rainfall_alerts.csv", index=False)
    print(out.to_string(index=False)); print(f"\nSaved {RESULTS/'rainfall_alerts.png'} and .csv")


def selftest():
    """Validate detection logic on a controlled synthetic series (no network)."""
    rng = np.random.default_rng(0)
    p = np.abs(rng.gamma(0.3, 6.0, 400))          # skewed daily rainfall
    p[100:103] += 80                               # engineered 3-day extreme -> should warn
    p[200:230] = 0.0                               # 30 dry days -> drought
    acc = pd.Series(p).rolling(ACCUM_WINDOW, min_periods=1).sum().to_numpy()
    p95, p99 = np.percentile(acc, 95), np.percentile(acc, 99)
    flood, drought = detect(p, p95, p99)
    assert flood[102] == 2, "expected a flood warning at the engineered extreme"
    assert drought[229], "expected a drought flag after 30 dry days"
    assert flood.max() == 2 and drought.sum() >= 10
    print("selftest OK — flood warning fired at day 102; drought flagged in the 30-day dry run.")
    print(f"thresholds: p95(3-day)={p95:.1f} mm, p99(3-day)={p99:.1f} mm; "
          f"flood-warning days={int((flood==2).sum())}, drought days={int(drought.sum())}")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        run_live()
