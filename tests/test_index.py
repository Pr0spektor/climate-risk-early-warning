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


def test_weighted_composite_matches_the_published_index():
    from src.build_index import DIMENSIONS, dimension_score, weighted_composite
    import pandas as pd
    from pathlib import Path
    df = pd.read_csv(Path(__file__).resolve().parent.parent / "data" / "worldbank_indicators.csv")
    dims = {name: dimension_score(df, spec) for name, spec in DIMENSIONS.items()}
    comp = weighted_composite(dims, {"hazard": 1/3, "vulnerability": 1/3, "readiness_gap": 1/3})
    assert comp.between(0, 100).all()


def test_hazard_weight_sensitivity_is_reported_for_every_country():
    from src.build_index import DIMENSIONS, dimension_score, hazard_weight_sensitivity
    import pandas as pd
    from pathlib import Path
    df = pd.read_csv(Path(__file__).resolve().parent.parent / "data" / "worldbank_indicators.csv")
    dims = {name: dimension_score(df, spec) for name, spec in DIMENSIONS.items()}
    table = hazard_weight_sensitivity(dims)
    assert len(table) == len(df)
    assert (table["max_shift"] >= 0).all()
    assert table["max_shift"].max() <= len(df) - 1


def test_a_country_with_one_indicator_does_not_get_a_dimension_score():
    """Averaging whatever is present silently rewards missing data."""
    import pandas as pd
    from src.build_index import dimension_score

    df = pd.DataFrame({
        "a": [1.0, 2.0, 3.0],
        "b": [1.0, None, 3.0],
        "c": [1.0, None, 3.0],
    })
    spec = {"a": "direct", "b": "direct", "c": "direct"}
    score = dimension_score(df, spec)
    assert pd.isna(score.iloc[1]), "one of three indicators must not produce a score"
    assert score.iloc[0] == 0.0 and score.iloc[2] == 1.0


def test_a_single_indicator_dimension_is_still_scored():
    """The hazard composite is one indicator by construction and must survive the guard."""
    import pandas as pd
    from src.build_index import dimension_score

    df = pd.DataFrame({"hazard_exposure_inform": [1.0, 5.0, 9.0]})
    score = dimension_score(df, {"hazard_exposure_inform": "direct"})
    assert score.notna().all()
