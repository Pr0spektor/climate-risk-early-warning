"""
Uncertainty, rank-stability & sensitivity analysis
==================================================

A composite-indicator ranking is only decision-useful if we characterise (a) how uncertain each
score is, (b) how stable each rank position is — not just coarse "top-k membership" — and (c) what
drives the uncertainty. Following the OECD/JRC *Handbook on Constructing Composite Indicators*,
this module produces:

  1. Monte-Carlo uncertainty   — 90% intervals on each country's score
                                 (weights ~ Dirichlet; indicators + Gaussian noise).
  2. Full rank-probability     — P(country holds rank r) for every r  (results/rank_stability.png),
                                 which reveals the genuinely contested positions (near-ties) that a
                                 coarse "P(top-3)" hides.
  3. Pairwise dominance        — P(country i ranks above country j)    (results/dominance_matrix.png).
  4. Weight sensitivity (OAT)  — how each country's score responds as each dimension weight is swept
                                 0 -> 0.8                              (results/weight_sensitivity.png).
  5. Structural robustness     — Kendall's tau of the ranking under alternative aggregation
                                 (arithmetic vs geometric) and normalisation (min-max vs z-score).

Pure NumPy/pandas (no SciPy). Reads ../data/worldbank_indicators.csv; writes ../results/.
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
N_SIM = 20000
NOISE_SD = 0.05


# ---------- normalisation ----------
def minmax(col: pd.Series, polarity: str) -> np.ndarray:
    x = col.astype(float).to_numpy().copy()
    if col.name == "mobile_subs_per100":
        x = np.clip(x, None, 100.0)
    if polarity == "invert":
        x = -x
    lo, hi = np.nanmin(x), np.nanmax(x)
    return np.zeros_like(x) if hi == lo else (x - lo) / (hi - lo)


def zscore(col: pd.Series, polarity: str) -> np.ndarray:
    x = col.astype(float).to_numpy().copy()
    if col.name == "mobile_subs_per100":
        x = np.clip(x, None, 100.0)
    if polarity == "invert":
        x = -x
    mu, sd = np.nanmean(x), np.nanstd(x)
    z = (x - mu) / (sd if sd else 1.0)
    return (z - np.nanmin(z)) / (np.nanmax(z) - np.nanmin(z))  # rescale 0-1 for comparability


def dim_matrix(df, norm):
    return {name: np.column_stack([norm(df[c], p) for c, p in spec.items()])
            for name, spec in DIMENSIONS.items()}


def composite(dims, weights, agg="arith"):
    scores = np.array([np.nanmean(a, axis=1) for a in dims.values()]).T  # n x 3
    if agg == "geom":
        s = np.exp((np.log(np.clip(scores, 1e-9, None)) * weights).sum(axis=1))
    else:
        s = (scores * weights).sum(axis=1)
    return s * 100.0


def ranks_desc(x):  # rank 1 = highest
    order = np.argsort(-x)
    r = np.empty_like(order); r[order] = np.arange(1, len(x) + 1)
    return r


def kendall_tau(a, b):
    n = len(a); c = d = 0
    for i in range(n):
        for j in range(i + 1, n):
            s = np.sign(a[i] - a[j]) * np.sign(b[i] - b[j])
            c += s > 0; d += s < 0
    return (c - d) / (n * (n - 1) / 2)


def main():
    df = pd.read_csv(DATA); n = len(df); names = df["country"].to_list()
    dims = dim_matrix(df, minmax)
    base_w = np.full(len(DIMENSIONS), 1 / len(DIMENSIONS))
    base_score = composite(dims, base_w)

    # ---------- Monte Carlo ----------
    scores = np.zeros((N_SIM, n)); rank_counts = np.zeros((n, n))
    dom = np.zeros((n, n))
    for s in range(N_SIM):
        w = RNG.dirichlet(np.full(len(DIMENSIONS), 6.0))
        noisy = {k: np.clip(a + RNG.normal(0, NOISE_SD, a.shape), 0, 1) for k, a in dims.items()}
        comp = composite(noisy, w)
        scores[s] = comp
        r = ranks_desc(comp)
        for i in range(n):
            rank_counts[i, r[i] - 1] += 1
        dom += (comp[:, None] > comp[None, :])
    rank_prob = rank_counts / N_SIM
    dom /= N_SIM

    # ---------- variance decomposition: weighting choice vs data-perturbation ----------
    M = 10000
    sc_w = np.zeros((M, n)); sc_n = np.zeros((M, n))
    for s in range(M):
        w = RNG.dirichlet(np.full(len(DIMENSIONS), 6.0))
        sc_w[s] = composite(dims, w)                              # weights vary, no noise
        noisy = {k: np.clip(a + RNG.normal(0, NOISE_SD, a.shape), 0, 1) for k, a in dims.items()}
        sc_n[s] = composite(noisy, base_w)                        # noise varies, weights fixed
    var_w, var_n = sc_w.var(0), sc_n.var(0)
    share_w = np.where(var_w + var_n > 0, var_w / (var_w + var_n), 0)

    unc = pd.DataFrame({
        "iso3": df["iso3"], "country": names,
        "index_mean": scores.mean(0).round(1),
        "band05": np.percentile(scores, 5, 0).round(1),
        "band95": np.percentile(scores, 95, 0).round(1),
        "p_rank1_%": (100 * rank_prob[:, 0]).round(1),
        "modal_rank": rank_prob.argmax(1) + 1,
        "var_from_weighting_%": (100 * share_w).round(0),
        "var_from_data_noise_%": (100 * (1 - share_w)).round(0),
    }).sort_values("index_mean", ascending=False).reset_index(drop=True)
    unc.to_csv(RESULTS / "uncertainty.csv", index=False)

    order = np.argsort(-scores.mean(0))
    gap34 = np.sort(scores.mean(0))[::-1]
    print("Sensitivity band & rank-stability (", f"{N_SIM:,} runs):\n", sep="")
    print(unc.to_string(index=False))
    print(f"\nMean score gap rank3->rank4 = {gap34[2]-gap34[3]:.1f} pts; "
          f"typical band half-width = {((unc['band95']-unc['band05'])/2).mean():.1f} pts. "
          "This is an ASSUMPTION-driven band (weighting + 5% data stress), not a statistical CI. "
          "For most countries the spread is dominated by the WEIGHTING choice "
          "(see var_from_weighting_%), largest where the dimension profile is uneven (e.g. Chad).")

    # ---------- 1) sensitivity band chart ----------
    fig, ax = plt.subplots(figsize=(9.5, 5))
    y = np.arange(len(unc))[::-1]
    err = np.vstack([unc["index_mean"] - unc["band05"], unc["band95"] - unc["index_mean"]])
    ax.barh(y, unc["index_mean"], color=plt.cm.YlOrRd(np.clip(unc["index_mean"]/100,0.15,0.95)), zorder=2)
    ax.errorbar(unc["index_mean"], y, xerr=err, fmt="none", ecolor="#333", elinewidth=1, capsize=3, zorder=3)
    ax.set_yticks(y); ax.set_yticklabels(unc["country"])
    ax.set_xlabel("Index (0–100): point estimate + 5–95% sensitivity band (weighting + 5% data stress)")
    ax.set_title(f"Score sensitivity band, not a statistical CI ({N_SIM:,} scenarios)")
    ax.set_xlim(0, 100); ax.grid(axis="x", alpha=0.3)
    fig.tight_layout(); fig.savefig(RESULTS / "uncertainty.png", dpi=140)

    # ---------- 1b) variance-source decomposition ----------
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    sw = unc["var_from_weighting_%"].to_numpy(); sn = unc["var_from_data_noise_%"].to_numpy()
    ax.barh(y, sw, color="#1f3864", label="weighting choice", zorder=2)
    ax.barh(y, sn, left=sw, color="#c9a227", label="data-perturbation (5%)", zorder=2)
    ax.set_yticks(y); ax.set_yticklabels(unc["country"])
    ax.set_xlabel("Share of score-band variance (%)"); ax.set_xlim(0, 100)
    ax.set_title("What drives each country's band: weighting choice vs data stress")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout(); fig.savefig(RESULTS / "uncertainty_sources.png", dpi=140)

    # ---------- 2) rank-probability heatmap ----------
    rp = rank_prob[order]
    fig, ax = plt.subplots(figsize=(9, 5))
    im = ax.imshow(rp, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(n)); ax.set_xticklabels([f"#{i+1}" for i in range(n)])
    ax.set_yticks(range(n)); ax.set_yticklabels([names[i] for i in order])
    for i in range(n):
        for j in range(n):
            if rp[i, j] > 0.005:
                ax.text(j, i, f"{100*rp[i,j]:.0f}", ha="center", va="center", fontsize=8,
                        color="white" if rp[i, j] > 0.5 else "black")
    ax.set_title("Rank-probability (%) — P(country holds rank r) over simulations")
    ax.set_xlabel("Rank position"); fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    fig.tight_layout(); fig.savefig(RESULTS / "rank_stability.png", dpi=140)
    pd.DataFrame(100*rp, index=[names[i] for i in order],
                 columns=[f"rank{i+1}_%" for i in range(n)]).round(1).to_csv(RESULTS / "rank_stability.csv")

    # ---------- 3) pairwise dominance ----------
    dm = dom[np.ix_(order, order)]
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    im = ax.imshow(dm, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    labs = [names[i] for i in order]
    ax.set_xticks(range(n)); ax.set_xticklabels(labs, rotation=40, ha="right", fontsize=8)
    ax.set_yticks(range(n)); ax.set_yticklabels(labs, fontsize=8)
    for i in range(n):
        for j in range(n):
            ax.text(j, i, "—" if i == j else f"{100*dm[i,j]:.0f}", ha="center", va="center",
                    fontsize=7, color="black")
    ax.set_title("Pairwise dominance: P(row ranks above column) %")
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    fig.tight_layout(); fig.savefig(RESULTS / "dominance_matrix.png", dpi=140)

    # ---------- 4) one-at-a-time weight sensitivity ----------
    sweep = np.linspace(0, 0.8, 33)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
    def _declutter(ys, min_gap):
        """Nudge end-labels apart so they never overlap, preserving order."""
        idx = sorted(range(len(ys)), key=lambda i: ys[i])
        pos = list(ys)
        for k in range(1, len(idx)):
            lo, hi = idx[k - 1], idx[k]
            if pos[hi] - pos[lo] < min_gap:
                pos[hi] = pos[lo] + min_gap
        return pos
    for ax, (di, dname) in zip(axes, enumerate(DIMENSIONS)):
        traj = []
        for wv in sweep:
            w = np.full(len(DIMENSIONS), (1 - wv) / (len(DIMENSIONS) - 1)); w[di] = wv
            traj.append(composite(dims, w))
        traj = np.array(traj)  # sweep x n
        for c in range(n):
            ax.plot(sweep, traj[:, c], lw=1.6)
        # place country codes at the right edge, spread vertically so they never collide
        ends = traj[-1, :]
        label_y = _declutter(list(ends), min_gap=3.4)
        for c in range(n):
            ax.annotate(df["iso3"][c], xy=(sweep[-1], ends[c]),
                        xytext=(sweep[-1] + 0.03, label_y[c]), fontsize=7, va="center",
                        arrowprops=dict(arrowstyle="-", lw=0.4, color="#999",
                                        shrinkA=0, shrinkB=0))
        ax.set_xlim(0, 0.94)
        ax.set_title(f"weight on: {dname}"); ax.set_xlabel("dimension weight"); ax.grid(alpha=0.3)
    axes[0].set_ylabel("Index (0–100)")
    fig.suptitle("One-at-a-time weight sensitivity (other two weights kept equal)")
    fig.tight_layout(); fig.savefig(RESULTS / "weight_sensitivity.png", dpi=140)

    # ---------- 5) structural robustness (Kendall tau vs baseline) ----------
    variants = {
        "baseline (min-max, arithmetic)": base_score,
        "geometric aggregation": composite(dims, base_w, agg="geom"),
        "z-score normalisation": composite(dim_matrix(df, zscore), base_w),
        "hazard-weighted (0.5/0.25/0.25)": composite(dims, np.array([0.5, 0.25, 0.25])),
        "readiness-weighted (0.25/0.25/0.5)": composite(dims, np.array([0.25, 0.25, 0.5])),
    }
    rows = []
    for name, sc in variants.items():
        rows.append({"variant": name,
                     "kendall_tau_vs_baseline": round(kendall_tau(base_score, sc), 3),
                     "ranking": " > ".join(df["iso3"][np.argsort(-sc)].to_list())})
    struct = pd.DataFrame(rows); struct.to_csv(RESULTS / "structural_sensitivity.csv", index=False)
    print("\nStructural robustness (Kendall tau of ranking vs baseline):")
    print(struct[["variant", "kendall_tau_vs_baseline"]].to_string(index=False))
    print(f"\nSaved: uncertainty.png/csv, rank_stability.png/csv, dominance_matrix.png, "
          "weight_sensitivity.png, structural_sensitivity.csv")


if __name__ == "__main__":
    main()
