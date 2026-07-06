"""
Robustness & uncertainty analysis (Monte Carlo)
===============================================

Composite indicators are only credible if the ranking survives reasonable changes in weights and
data noise (see the OECD/JRC *Handbook on Constructing Composite Indicators*). This module runs a
Monte-Carlo simulation over the EW4All Risk & Readiness Index and reports:

  * 90% uncertainty interval on each country's index, and
  * rank-stability — the probability each country lands in the top-3 priority set,

by repeatedly (default 5,000 runs):
  1. drawing the three dimension weights from a Dirichlet distribution centred on equal weights, and
  2. perturbing every normalised indicator with Gaussian measurement noise (sd 0.05, clipped 0-1).

Pure NumPy (no SciPy). Reads ../data/worldbank_indicators.csv; writes to ../results/.
Run:  python src/uncertainty.py
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
RESULTS = ROOT / "results"; RESULTS.mkdir(exist_ok=True)
RNG = np.random.default_rng(7)

DIMENSIONS = {
    "hazard": {"hazard_exposure_inform": "direct"},
    "vulnerability": {"gdp_pc_usd": "invert", "undernourishment_pct": "direct",
                      "under5_mortality": "direct", "rural_pct": "direct"},
    "readiness_gap": {"electricity_access_pct": "invert", "basic_water_pct": "invert",
                      "mobile_subs_per100": "invert"},
}
N_SIM = 5000
NOISE_SD = 0.05
TOPK = 3


def normalise(col: pd.Series, polarity: str) -> np.ndarray:
    x = col.astype(float).to_numpy().copy()
    if col.name == "mobile_subs_per100":
        x = np.clip(x, None, 100.0)
    if polarity == "invert":
        x = -x
    lo, hi = np.nanmin(x), np.nanmax(x)
    return np.zeros_like(x) if hi == lo else (x - lo) / (hi - lo)


def main() -> None:
    df = pd.read_csv(DATA)
    n = len(df)
    # base normalised indicators per dimension (list of arrays, NaNs preserved)
    dims = {name: np.column_stack([normalise(df[c], p) for c, p in spec.items()])
            for name, spec in DIMENSIONS.items()}

    idx_samples = np.zeros((N_SIM, n))
    top_hits = np.zeros(n)
    for s in range(N_SIM):
        w = RNG.dirichlet(np.full(len(DIMENSIONS), 6.0))  # ~equal weights, moderate spread
        dim_scores = []
        for arr in dims.values():
            noisy = np.clip(arr + RNG.normal(0, NOISE_SD, arr.shape), 0, 1)
            dim_scores.append(np.nanmean(noisy, axis=1))
        comp = (np.array(dim_scores).T * w).sum(axis=1) * 100.0
        idx_samples[s] = comp
        top_idx = np.argsort(-comp)[:TOPK]
        top_hits[top_idx] += 1

    out = df[["iso3", "country"]].copy()
    out["index_mean"] = idx_samples.mean(axis=0).round(1)
    out["ci05"] = np.percentile(idx_samples, 5, axis=0).round(1)
    out["ci95"] = np.percentile(idx_samples, 95, axis=0).round(1)
    out["p_top3_%"] = (100 * top_hits / N_SIM).round(1)
    out = out.sort_values("index_mean", ascending=False).reset_index(drop=True)
    out.to_csv(RESULTS / "uncertainty.csv", index=False)

    top3 = set(out["country"].head(3))
    print(f"Monte-Carlo robustness ({N_SIM:,} runs; Dirichlet weights + indicator noise):\n")
    print(out.to_string(index=False))
    print(f"\nStable top-3 priority set: {', '.join(sorted(top3))}")

    # chart: mean index with 90% CI, coloured by P(top-3)
    fig, ax = plt.subplots(figsize=(9.5, 5))
    y = np.arange(len(out))[::-1]
    err = np.vstack([out["index_mean"] - out["ci05"], out["ci95"] - out["index_mean"]])
    colors = plt.cm.YlOrRd(np.clip(out["p_top3_%"] / 100, 0.15, 0.95))
    ax.barh(y, out["index_mean"], color=colors, zorder=2)
    ax.errorbar(out["index_mean"], y, xerr=err, fmt="none", ecolor="#333", elinewidth=1, capsize=3, zorder=3)
    ax.set_yticks(y); ax.set_yticklabels(out["country"])
    for i, r in out.iterrows():
        ax.text(r["ci95"] + 1, y[i], f"P(top-3)={r['p_top3_%']:.0f}%", va="center", fontsize=8)
    ax.set_xlabel("Index (0–100), mean ± 90% Monte-Carlo interval")
    ax.set_title(f"Robustness of the EW4All priority ranking ({N_SIM:,} simulations)\n"
                 "weights ~ Dirichlet · indicator noise sd=0.05")
    ax.set_xlim(0, 105); ax.grid(axis="x", alpha=0.3)
    fig.tight_layout(); fig.savefig(RESULTS / "uncertainty.png", dpi=140)
    print(f"\nSaved {RESULTS/'uncertainty.png'} and {RESULTS/'uncertainty.csv'}")


if __name__ == "__main__":
    main()
