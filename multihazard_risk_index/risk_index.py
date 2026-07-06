"""
Multi-hazard risk index for the EW4All pilot countries
======================================================

Builds a transparent composite risk index in the spirit of the INFORM Risk framework:

    RISK = f(HAZARD & EXPOSURE, VULNERABILITY, LACK OF COPING CAPACITY)

Method
------
1. Load per-country indicators (0-10 illustrative scores; see note on data below).
2. Aggregate the three INFORM dimensions:
     - Hazard & Exposure  : geometric mean of hazard components, weighted by exposure.
     - Vulnerability      : socio-economic vulnerability.
     - Lack of coping cap.: institutional/coping-capacity gap.
3. Combine dimensions with a geometric mean (so no single dimension can be masked) and
   rescale 0-10. Rank countries to prioritise where early-warning investment matters most.

This mirrors "risk knowledge" (EW4All Pillar 1) and supports prioritisation for preparedness
(Pillar 4).

Data note: the values in data.csv are ILLUSTRATIVE, hand-set to public, well-known relative
patterns (e.g. Somalia/Chad drought exposure, SIDS cyclone exposure). Swap in official INFORM /
ND-GAIN / EM-DAT values to operationalise; the method is unchanged.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

HERE = Path(__file__).resolve().parent


def geomean(a: np.ndarray, axis=None) -> np.ndarray:
    a = np.clip(a, 1e-6, None)
    return np.exp(np.log(a).mean(axis=axis))


def main() -> None:
    df = pd.read_csv(HERE / "data.csv")

    hazard_cols = ["hazard_flood", "hazard_drought", "hazard_cyclone_storm"]
    # Hazard & Exposure: combine hazards (geometric mean), lift by exposure of low-lying areas
    hazard = geomean(df[hazard_cols].to_numpy(), axis=1)
    exposure = df["exposure_coastal_lowland"].to_numpy()
    haz_exp = geomean(np.column_stack([hazard, 0.5 * hazard + 0.5 * exposure]), axis=1)

    vulnerability = df["vulnerability_socioecon"].to_numpy()
    lack_coping = df["coping_capacity_lack"].to_numpy()

    # INFORM-style composite: geometric mean of the three dimensions
    risk = geomean(np.column_stack([haz_exp, vulnerability, lack_coping]), axis=1)

    out = df[["country", "population_millions"]].copy()
    out["hazard_exposure"] = haz_exp.round(2)
    out["vulnerability"] = vulnerability.round(2)
    out["lack_of_coping_capacity"] = lack_coping.round(2)
    out["RISK_INDEX"] = risk.round(2)
    out["priority_rank"] = out["RISK_INDEX"].rank(ascending=False).astype(int)
    out = out.sort_values("RISK_INDEX", ascending=False).reset_index(drop=True)

    out.to_csv(HERE / "risk_index_results.csv", index=False)
    print("Multi-hazard risk index (EW4All pilot countries):")
    print(out.to_string(index=False))

    # Chart
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = plt.cm.YlOrRd(np.linspace(0.35, 0.9, len(out)))
    ax.barh(out["country"][::-1], out["RISK_INDEX"][::-1], color=colors)
    ax.set_xlabel("Composite multi-hazard risk index (0-10)")
    ax.set_title("Where to prioritise early-warning investment (higher = greater risk)")
    for i, v in enumerate(out["RISK_INDEX"][::-1]):
        ax.text(v + 0.05, i, f"{v:.2f}", va="center", fontsize=8)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(HERE / "risk_ranking.png", dpi=130)
    print(f"\nSaved: {HERE/'risk_ranking.png'}  and  {HERE/'risk_index_results.csv'}")


if __name__ == "__main__":
    main()
