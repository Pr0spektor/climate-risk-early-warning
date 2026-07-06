"""
EW4All Multi-Hazard Risk & Readiness Index
==========================================

A transparent, INFORM-style composite index for the seven Green Climate Fund
Early-Warnings-for-All (EW4All) pilot countries, built entirely from **real, open data**:

  * Hazard & Exposure   -> JRC INFORM Risk 2023 "Hazard & Exposure" component (0-10)
  * Vulnerability       -> World Bank Open Data (GDP/capita, undernourishment,
                           under-5 mortality, rural share)
  * Readiness gap       -> World Bank Open Data (electricity, basic water,
                           mobile reach) -- proxies for the systems an early-warning
                           chain depends on

See ../data/sources.md for every indicator code, year and URL.

Method
------
  1. Set each indicator's polarity so HIGHER = WORSE.
  2. Min-max normalise each indicator to 0-1 ACROSS the seven countries (a relative,
     prioritisation index).
  3. Dimension score = mean of available (non-missing) indicators.
  4. Composite = **arithmetic mean of the three dimension scores x 100** (0-100).
     (An arithmetic mean is used rather than a geometric mean so that a country which is
     best-in-class on one dimension is not forced to an artificial 0 overall.)
  5. Rank. The independent INFORM overall risk score is carried through as an external
     cross-check (not part of the composite).

Outputs (../results/): index.csv, index_ranking.png, indicator_heatmap.png
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

# dimension -> {column: polarity}. "direct" = higher already worse; "invert" = flip.
DIMENSIONS = {
    "hazard": {
        "hazard_exposure_inform": "direct",
    },
    "vulnerability": {
        "gdp_pc_usd": "invert",
        "undernourishment_pct": "direct",
        "under5_mortality": "direct",
        "rural_pct": "direct",
    },
    "readiness_gap": {
        "electricity_access_pct": "invert",
        "basic_water_pct": "invert",
        "mobile_subs_per100": "invert",
    },
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
    return pd.concat(parts, axis=1).mean(axis=1, skipna=True)


def main() -> None:
    df = pd.read_csv(DATA)

    dim_scores = {name: dimension_score(df, spec) for name, spec in DIMENSIONS.items()}
    composite = pd.concat(dim_scores.values(), axis=1).mean(axis=1) * 100.0

    out = df[["iso3", "country", "population"]].copy()
    for name, s in dim_scores.items():
        out[name] = s.round(3)
    out["INDEX_0_100"] = composite.round(1)
    out["inform_overall_ref"] = df["inform_risk_overall"]
    out = out.sort_values("INDEX_0_100", ascending=False).reset_index(drop=True)
    out["priority_rank"] = np.arange(1, len(out) + 1)
    out.to_csv(RESULTS / "index.csv", index=False)

    # rank-agreement with the independent INFORM overall score (Spearman = Pearson on ranks)
    rho = out["INDEX_0_100"].rank().corr(out["inform_overall_ref"].rank())

    print("EW4All Multi-Hazard Risk & Readiness Index (real data)\n")
    print(out.to_string(index=False))
    print(f"\nRank correlation with INFORM overall risk (independent check): Spearman rho = {rho:.2f}")

    # ---- ranking chart ----
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = plt.cm.YlOrRd(np.linspace(0.35, 0.92, len(out)))
    ax.barh(out["country"][::-1], out["INDEX_0_100"][::-1], color=colors)
    for i, v in enumerate(out["INDEX_0_100"][::-1]):
        ax.text(v + 0.6, i, f"{v:.1f}", va="center", fontsize=8)
    ax.set_xlabel("Multi-Hazard Risk & Readiness Index (0–100, higher = higher priority)")
    ax.set_title("EW4All pilot countries — early-warning prioritisation\n"
                 "INFORM Risk 2023 + World Bank Open Data (accessed 2026-07-06)")
    ax.set_xlim(0, 100)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS / "index_ranking.png", dpi=140)

    # ---- indicator heatmap ----
    all_spec = {c: p for spec in DIMENSIONS.values() for c, p in spec.items()}
    norm = pd.DataFrame({c: normalise(df[c], p) for c, p in all_spec.items()})
    norm.index = df["country"]
    norm = norm.loc[out["country"]]
    fig2, ax2 = plt.subplots(figsize=(11, 5))
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
