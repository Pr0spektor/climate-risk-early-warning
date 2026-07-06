# Data sources & provenance

All values are **real, official open data**, for the seven Green Climate Fund *Early Warnings for
All* (EW4All) pilot countries, from two authoritative sources:

- **World Bank Open Data API** (`api.worldbank.org`) — socioeconomic & service indicators.
- **JRC INFORM Risk 2023** (`drmkc.jrc.ec.europa.eu/Inform-Index`, API WorkflowId 464) — the
  Hazard & Exposure component and the overall INFORM risk score.

- **Accessed:** 2026-07-06
- **World Bank "last updated" stamp:** 2026-07-01
- **INFORM release:** INFORM Risk 2023 (latest edition exposed through the public API at access
  time; 2024/2025 workflows exist but are not yet published via the API).
- **Reproduce:** run `python src/fetch_data.py` to regenerate `worldbank_indicators.csv` live
  from both APIs.

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
| `hazard_exposure_inform` | INFORM Hazard & Exposure component (0–10) | INFORM `HA` (WF 464) | 2023 | hazard |
| `inform_risk_overall` | INFORM overall risk score (0–10) | INFORM `INFORM` (WF 464) | 2023 | external cross-check |

### Missing values (reported honestly, not imputed)
- **Antigua and Barbuda** — `undernourishment_pct` and `mobile_subs_per100` are not reported by
  the source for the latest years, so they are left blank. The index averages only the available
  indicators within each dimension for that country (see `src/build_index.py`).

### Notes / limitations
- The composite combines three real dimensions: **Hazard & Exposure** (INFORM), **Vulnerability**
  and **Readiness gap** (World Bank). The INFORM overall score is kept separate as an independent
  cross-check on the ranking (Spearman ρ ≈ 0.99).
- Mobile subscriptions are capped at 100/100 before normalisation (values above 100 reflect
  multiple SIMs per person, not additional population reach).
- Index values are **relative across these seven countries**, for prioritisation — not absolute
  global risk scores.
- INFORM hazard data is the 2023 edition (latest via API); World Bank values are 2022–2024 as
  noted per indicator. Re-running `fetch_data.py` will pick up newer data as it is published.
