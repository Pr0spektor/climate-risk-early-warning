"""
Test suite — validates the index construction, normalisation and known results.

Runs with pytest (`pytest -q`) or standalone (`python -m tests.test_index`). Pure NumPy/pandas.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path
import importlib

bi = importlib.import_module("src.build_index")
ROOT = Path(__file__).resolve().parent.parent


def _run_pipeline():
    bi.main()
    return pd.read_csv(ROOT / "results" / "index.csv")


def test_normalise_polarity_and_bounds():
    """Min-max normalisation is in [0,1]; 'invert' flips best/worst correctly."""
    s = pd.Series([1.0, 2.0, 3.0, 4.0], name="gdp_pc_usd")
    direct = bi.normalise(pd.Series([1.0, 2.0, 3.0, 4.0], name="under5_mortality"), "direct")
    inv = bi.normalise(s, "invert")
    assert direct.min() == 0 and direct.max() == 1
    assert inv.iloc[0] == 1.0 and inv.iloc[-1] == 0.0        # lowest GDP -> worst (1)


def test_missing_values_not_imputed():
    """Antigua's blank indicators stay NaN in the raw data (never filled)."""
    df = pd.read_csv(ROOT / "data" / "worldbank_indicators.csv")
    row = df[df["iso3"] == "ATG"].iloc[0]
    assert pd.isna(row["undernourishment_pct"]) and pd.isna(row["mobile_subs_per100"])


def test_index_bounds_and_ranking():
    out = _run_pipeline()
    assert out["INDEX_0_100"].between(0, 100).all()
    # highest-risk countries lead; Antigua lowest
    top3 = set(out.sort_values("INDEX_0_100", ascending=False).head(3)["iso3"])
    assert top3 == {"SOM", "TCD", "ETH"}
    assert out.sort_values("INDEX_0_100").iloc[0]["iso3"] == "ATG"


def test_validation_against_inform():
    """Composite ranking agrees with the independent INFORM overall score (Spearman >= 0.9)."""
    out = _run_pipeline()
    rho = out["INDEX_0_100"].rank().corr(out["inform_overall_ref"].rank())
    assert rho >= 0.9, f"weak agreement with INFORM: rho={rho:.2f}"


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print(f"PASS  {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")


if __name__ == "__main__":
    _run_all()
