"""
EW4All Vulnerability & Readiness Index
======================================

Builds a transparent, INFORM-style composite index for the seven Green Climate Fund
Early-Warnings-for-All (EW4All) pilot countries, from **real World Bank Open Data**
(see ../data/sources.md). It answers a concrete question for programme prioritisation:

    Where are people most vulnerable to climate hazards AND least served by the basic
    systems an early-warning chain relies on (power, water, mobile reach)?

Method
------
Two INFORM dimensions, built only from openly-available authoritative data:

  VULNERABILITY   : GDP per capita (inverted), undernourishment, under-5 mortality,
                    rural population share (harder-to-reach).
  READINESS GAP   : access to electricity (inverted), basic drinking water (inverted),
                    mobile subscriptions / 100 (inverted; capped at 100 = saturated reach).

Steps:
  1. Set each indicator's polarity so HIGHER = WORSE.
  2. Min-max normalise each indicator to 0-1 ACROSS the seven countries (relative index).
  3. Dimension score = mean of available (non-missing) indicators.
  4. Composite = geometric mean(vulnerability, readiness_gap) x 100  -> 0-100.
  5. Rank; the highest scores are the priority countries.

Outputs (written to ../results/):
  vulnerability_readiness_index.csv, index_ranking.png, indicator_heatmap.png
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "worldbank_indicators.csv"
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

# indicator -> ("direct" means higher=worse already, "invert" means higher=better -> flip)
VULNERABILITY = {
    "gdp_pc_usd": "invert",
    "undernourishment_pct": "direct",
    "under5_mortality": "direct",
    "rural_pct": "direct",
}
READINESS = {
    "electricity_access_pct": "invert",
    "basic_water_pct": "invert",
    "mobile_subs_per100": "invert",
}
MOBILE_CAP = 100.0


def normalise(col: pd.Series, polarity: str) -> pd.Series:
    x = col.astype(float).copy()
    if col.name == "mobile_subs_per100":
        x = x.clip(upper=MOBILE_CAP)
    if polarity == "invert":
        x = -x
    lo, hi = x.min(), x.max()
    if hi == lo:
        return pd.Series(np.zeros(len(x)), index=x.index)
    return (x - lo) / (hi - lo)  # 0 = best, 1 = worst (NaNs preserved)


def dimension_score(df: pd.DataFrame, spec: dict) -> pd.Series:
    parts = [normalise(df[c], pol) for c, pol in spec.items()]
    return pd.concat(parts, axis=1).mean(axis=1, skipna=True)  # mean of available indicators


def main() -> None:
    df = pd.read_csv(DATA)

    vuln = dimension_score(df, VULNERABILITY)
    ready_gap = dimension_score(df, READINESS)
    composite = np.sqrt(vuln.clip(1e-9) * ready_gap.clip(1e-9)) * 100.0

    out = df[["iso3", "country", "population"]].copy()
    out["vulnerability_0_1"] = vuln.round(3)
    out["readiness_gap_0_1"] = ready_gap.round(3)
    out["INDEX_0_100"] = composite.round(1)
    out = out.sort_values("INDEX_0_100", ascending=False).reset_index(drop=True)
    out["priority_rank"] = np.arange(1, len(out) + 1)
    out.to_csv(RESULTS / "vulnerability_readiness_index.csv", index=False)

    print("EW4All Vulnerability & Readiness Index (real World Bank data):\n")
    print(out.to_string(index=False))

    # ---- ranking chart ----
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = plt.cm.YlOrRd(np.linspace(0.35, 0.92, len(out)))
    ax.barh(out["country"][::-1], out["INDEX_0_100"][::-1], color=colors)
    for i, v in enumerate(out["INDEX_0_100"][::-1]):
        ax.text(v + 0.6, i, f"{v:.1f}", va="center", fontsize=8)
    ax.set_xlabel("Vulnerability & Readiness Index (0–100, higher = higher priority)")
    ax.set_title("EW4All pilot countries — early-warning prioritisation\n(real World Bank data, accessed 2026-07-06)")
    ax.set_xlim(0, 100)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS / "index_ranking.png", dpi=140)

    # ---- indicator heatmap (normalised, higher = worse) ----
    all_spec = {**VULNERABILITY, **READINESS}
    norm = pd.DataFrame({c: normalise(df[c], p) for c, p in all_spec.items()})
    norm.index = df["country"]
    norm = norm.loc[out["country"]]  # order by rank
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    im = ax2.imshow(norm.values, cmap="YlOrRd", aspect="auto", vmin=0, vmax=1)
    ax2.set_xticks(range(len(all_spec)))
    ax2.set_xticklabels(list(all_spec), rotation=40, ha="right", fontsize=8)
    ax2.set_yticks(range(len(norm))); ax2.set_yticklabels(norm.index, fontsize=9)
    for (r, c), val in np.ndenumerate(norm.values):
        txt = "n/a" if np.isnan(val) else f"{val:.2f}"
        ax2.text(c, r, txt, ha="center", va="center", fontsize=7,
                 color="black" if (np.isnan(val) or val < 0.6) else "white")
    ax2.set_title("Normalised indicators (0 = best, 1 = worst among the seven)")
    fig2.colorbar(im, ax=ax2, fraction=0.025, pad=0.02)
    fig2.tight_layout()
    fig2.savefig(RESULTS / "indicator_heatmap.png", dpi=140)

    print(f"\nSaved results to {RESULTS}/")


if __name__ == "__main__":
    main()
