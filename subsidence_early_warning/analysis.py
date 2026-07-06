"""
Subsidence / ground-deformation early-warning demo
==================================================

Demonstrates a monitoring -> detection -> tiered-warning workflow of the kind used in
geodynamic (geohazard) monitoring, translated to a generic deformation early-warning setting.

Method
------
1. Ingest a displacement time-series per monitoring station (here: synthetic, InSAR/GNSS-like,
   with realistic seasonal signal + noise + a developing subsidence trend and an abrupt step).
2. Estimate deformation VELOCITY with a robust rolling linear fit.
3. Flag anomalies with a control-chart rule (robust z-score on residuals, MAD-based) AND a
   velocity-threshold rule (mm/year exceeding operational limits).
4. Emit a tiered ALERT LOG (WATCH / WARNING / CRITICAL) — the "dissemination" step.

All thresholds are explicit and configurable so the logic is auditable — the same principle as
audit-proof monitoring reporting for regulators.

Data: SYNTHETIC and generated deterministically (fixed seed) for demonstration. Replace
`load_series()` with real InSAR/GNSS/levelling data to operationalise.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

HERE = Path(__file__).resolve().parent
RNG = np.random.default_rng(42)

# ----- operational thresholds (configurable / auditable) -----
VELOCITY_WATCH = -10.0     # mm/year  (subsidence is negative)
VELOCITY_WARNING = -25.0
VELOCITY_CRITICAL = -50.0
ROBUST_Z_LIMIT = 3.5       # residual anomaly (step / sudden movement)
ROLLING_DAYS = 90          # window for velocity estimation


def load_series(n_days: int = 730) -> pd.DataFrame:
    """Synthetic daily displacement (mm) for 3 stations. Replace with real data."""
    t = np.arange(n_days)
    dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
    seasonal = lambda amp: amp * np.sin(2 * np.pi * t / 365.25)

    # Station A: stable
    a = seasonal(4) + RNG.normal(0, 2.0, n_days)
    # Station B: slow progressive subsidence (~ -30 mm/yr in second half)
    trend_b = np.where(t < 365, -0.02 * t, -0.02 * 365 - 0.08 * (t - 365))
    b = trend_b + seasonal(5) + RNG.normal(0, 2.5, n_days)
    # Station C: stable then abrupt step (fault slip / sudden movement) + fast subsidence
    c = seasonal(3) + RNG.normal(0, 2.0, n_days)
    c[500:] += -35.0                      # abrupt step at day 500
    c[500:] += -0.15 * (t[500:] - 500)    # then rapid subsidence

    return pd.DataFrame({"date": dates, "STA_A": a, "STA_B": b, "STA_C": c})


def rolling_velocity(y: np.ndarray, window: int) -> np.ndarray:
    """mm/year velocity from a rolling least-squares slope (slope per day * 365.25)."""
    v = np.full_like(y, np.nan, dtype=float)
    x = np.arange(window)
    xc = x - x.mean()
    denom = (xc ** 2).sum()
    for i in range(window - 1, len(y)):
        yy = y[i - window + 1: i + 1]
        slope = (xc * (yy - yy.mean())).sum() / denom
        v[i] = slope * 365.25
    return v


def robust_z(y: np.ndarray, window: int = 30) -> np.ndarray:
    """MAD-based robust z-score of detrended residuals to catch abrupt steps."""
    s = pd.Series(y)
    med = s.rolling(window, min_periods=window // 2).median()
    resid = (s - med)
    mad = (resid - resid.median()).abs().median() * 1.4826 + 1e-9
    return (resid / mad).to_numpy()


def classify(velocity: float, rz: float) -> str:
    if velocity <= VELOCITY_CRITICAL or abs(rz) >= ROBUST_Z_LIMIT * 2:
        return "CRITICAL"
    if velocity <= VELOCITY_WARNING or abs(rz) >= ROBUST_Z_LIMIT:
        return "WARNING"
    if velocity <= VELOCITY_WATCH:
        return "WATCH"
    return "OK"


def main() -> None:
    df = load_series()
    stations = [c for c in df.columns if c.startswith("STA_")]
    alerts = []

    fig, axes = plt.subplots(len(stations), 1, figsize=(10, 8), sharex=True)
    for ax, sta in zip(axes, stations):
        y = df[sta].to_numpy()
        v = rolling_velocity(y, ROLLING_DAYS)
        rz = robust_z(y)
        status = np.array([classify(vi if np.isfinite(vi) else 0.0, zi if np.isfinite(zi) else 0.0)
                           for vi, zi in zip(v, rz)])

        ax.plot(df["date"], y, lw=1.0, color="#1f375b", label=f"{sta} displacement (mm)")
        for tier, col in [("WATCH", "#f0ad4e"), ("WARNING", "#e8590c"), ("CRITICAL", "#c92a2a")]:
            m = status == tier
            if m.any():
                ax.scatter(df["date"][m], y[m], s=10, color=col, label=tier, zorder=3)
        ax.set_ylabel("mm"); ax.legend(loc="lower left", fontsize=7, ncol=4)
        ax.grid(alpha=0.3)

        # log first-onset of each escalating tier
        for tier in ["WATCH", "WARNING", "CRITICAL"]:
            idx = np.where(status == tier)[0]
            if idx.size:
                i = idx[0]
                alerts.append({
                    "station": sta, "tier": tier,
                    "date": df["date"].iloc[i].date().isoformat(),
                    "velocity_mm_yr": round(float(v[i]), 1) if np.isfinite(v[i]) else None,
                    "robust_z": round(float(rz[i]), 1) if np.isfinite(rz[i]) else None,
                })

    axes[0].set_title("Ground-deformation monitoring with tiered early-warning flags")
    fig.tight_layout()
    fig.savefig(HERE / "monitoring_alerts.png", dpi=130)

    alog = pd.DataFrame(alerts).sort_values(["date", "station"])
    alog.to_csv(HERE / "alert_log.csv", index=False)
    print("Alert log (first onset per tier):")
    print(alog.to_string(index=False))
    print(f"\nSaved: {HERE/'monitoring_alerts.png'}  and  {HERE/'alert_log.csv'}")


if __name__ == "__main__":
    main()
