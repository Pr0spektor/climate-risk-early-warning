"""
Fetch real indicators for the EW4All pilot countries from the World Bank Open Data API.

Regenerates ../data/worldbank_indicators.csv with the latest available value per indicator.
No API key required. Run:  python src/fetch_data.py

Source: https://api.worldbank.org  (World Bank Open Data)
"""

from __future__ import annotations
import io
import json
import urllib.request
from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
BASE = "https://api.worldbank.org/v2"

COUNTRIES = {  # ISO2 used by the API -> ISO3 label we store
    "AG": "ATG", "KH": "KHM", "TD": "TCD", "EC": "ECU",
    "ET": "ETH", "FJ": "FJI", "SO": "SOM",
}
ISO2 = ";".join(COUNTRIES)

# indicator code -> (output column, most-recent year to try, fallback range)
INDICATORS = {
    "SP.POP.TOTL":     ("population",             "2024", "2018:2024"),
    "NY.GDP.PCAP.CD":  ("gdp_pc_usd",             "2024", "2018:2024"),
    "SN.ITK.DEFC.ZS":  ("undernourishment_pct",   "2023", "2018:2023"),
    "SH.DYN.MORT":     ("under5_mortality",       "2024", "2018:2024"),
    "SP.RUR.TOTL.ZS":  ("rural_pct",              "2024", "2018:2024"),
    "EG.ELC.ACCS.ZS":  ("electricity_access_pct", "2022", "2015:2022"),
    "SH.H2O.BASW.ZS":  ("basic_water_pct",        "2022", "2015:2022"),
    "IT.CEL.SETS.P2":  ("mobile_subs_per100",     "2023", "2015:2023"),
}

NAMES = {
    "ATG": "Antigua and Barbuda", "KHM": "Cambodia", "TCD": "Chad", "ECU": "Ecuador",
    "ETH": "Ethiopia", "FJI": "Fiji", "SOM": "Somalia",
}


def _get(url: str):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def latest_values(code: str, year: str, rng: str) -> dict:
    """Return {iso3: value} using `year`, filling gaps from the fallback range."""
    out: dict[str, float] = {}
    for date in (year, rng):
        url = f"{BASE}/country/{ISO2}/indicator/{code}?format=json&date={date}&per_page=500"
        payload = _get(url)
        if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
            continue
        # rows are newest-first within a range; keep first non-null per country
        for row in payload[1]:
            iso3 = row.get("countryiso3code")
            val = row.get("value")
            if iso3 and val is not None and iso3 not in out:
                out[iso3] = val
        if len(out) == len(COUNTRIES):
            break
    return out


def main() -> None:
    frame = {"iso3": list(NAMES), "country": [NAMES[i] for i in NAMES]}
    cols = {}
    for code, (col, year, rng) in INDICATORS.items():
        vals = latest_values(code, year, rng)
        cols[col] = [vals.get(i) for i in NAMES]
        print(f"{code:16s} -> {col:22s} {sum(v is not None for v in cols[col])}/7 countries")
    df = pd.DataFrame({**frame, **cols})
    DATA.mkdir(exist_ok=True)
    df.to_csv(DATA / "worldbank_indicators.csv", index=False)
    print(f"\nSaved {DATA/'worldbank_indicators.csv'}")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
