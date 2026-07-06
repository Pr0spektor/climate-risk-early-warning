# Data sources & provenance

All values are **real, official data from the World Bank Open Data API** (`api.worldbank.org`),
for the seven Green Climate Fund *Early Warnings for All* (EW4All) pilot countries.

- **Accessed:** 2026-07-06
- **API "last updated" stamp returned by World Bank:** 2026-07-01
- **Reproduce:** run `python src/fetch_data.py` to regenerate `worldbank_indicators.csv` live.

Each indicator uses the most recent year with data available for these countries at access time:

| Column | Indicator | World Bank code | Year used | Dimension |
|---|---|---|---|---|
| `population` | Population, total | SP.POP.TOTL | 2024 | context |
| `gdp_pc_usd` | GDP per capita (current US$) | NY.GDP.PCAP.CD | 2024 | vulnerability (inverted) |
| `undernourishment_pct` | Prevalence of undernourishment (% pop.) | SN.ITK.DEFC.ZS | 2023 | vulnerability |
| `under5_mortality` | Mortality rate, under-5 (per 1,000) | SH.DYN.MORT | 2024 | vulnerability |
| `rural_pct` | Rural population (% of total) | SP.RUR.TOTL.ZS | 2024 | vulnerability (hard-to-reach) |
| `electricity_access_pct` | Access to electricity (% pop.) | EG.ELC.ACCS.ZS | 2022 | readiness (inverted) |
| `basic_water_pct` | At least basic drinking water (% pop.) | SH.H2O.BASW.ZS | 2022 | readiness (inverted) |
| `mobile_subs_per100` | Mobile cellular subscriptions (per 100) | IT.CEL.SETS.P2 | 2023 | readiness / warning reach (inverted) |

### Missing values (reported honestly, not imputed)
- **Antigua and Barbuda** — `undernourishment_pct` and `mobile_subs_per100` are not reported by
  the source for the latest years, so they are left blank. The index averages only the available
  indicators within each dimension for that country (see `src/build_index.py`).

### Notes / limitations
- This uses the **vulnerability** and **coping-capacity/readiness** dimensions of the
  INFORM-style risk logic, for which authoritative country data is openly available. It does
  **not** include a physical **hazard/exposure** term — for that, combine with the JRC
  [INFORM Risk Index](https://drmkc.jrc.ec.europa.eu/inform-index) or
  [EM-DAT](https://www.emdat.be/). The code is structured so a hazard column can be added directly.
- Mobile subscriptions are capped at 100/100 before normalisation (values above 100 reflect
  multiple SIMs per person, not additional population reach).
- Index values are **relative across these seven countries**, for prioritisation — not absolute
  global risk scores.
