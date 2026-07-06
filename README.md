# EW4All Vulnerability & Readiness Index

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Pr0spektor/climate-risk-early-warning/blob/main/notebook.ipynb)

A reproducible, **real-data** analysis for the seven Green Climate Fund
**Early Warnings for All (EW4All)** pilot countries — Antigua and Barbuda, Cambodia, Chad,
Ecuador, Ethiopia, Fiji and Somalia.

It answers a concrete prioritisation question:

> **Where are people most vulnerable to climate hazards *and* least served by the basic systems
> an early-warning chain depends on (power, water, mobile reach)?**

All inputs are **official World Bank Open Data**, fetched live from `api.worldbank.org`
(accessed 2026-07-06; World Bank "last updated" 2026-07-01). No synthetic data. See
[`data/sources.md`](data/sources.md) for every indicator code, year and definition.

## Result

![Index ranking](results/index_ranking.png)

| Rank | Country | Index (0–100) | Vulnerability | Readiness gap |
|---|---|---|---|---|
| 1 | Chad | 86.8 | 0.86 | 0.88 |
| 2 | Somalia | 76.6 | 0.80 | 0.73 |
| 3 | Ethiopia | 72.4 | 0.67 | 0.79 |
| 4 | Cambodia | 24.9 | 0.39 | 0.16 |
| 5 | Fiji | 12.2 | 0.27 | 0.05 |
| 6 | Ecuador | 10.8 | 0.23 | 0.05 |
| 7 | Antigua and Barbuda | 0.0 | 0.33 | 0.00 |

![Indicator heatmap](results/indicator_heatmap.png)

The ranking aligns with independent assessments (Sahel / Horn of Africa show the highest
combined vulnerability and lowest service coverage), which is a sanity check on the method — but
the numbers here are computed only from the cited open data.

## Method

Two INFORM-style dimensions, each built only from openly-available authoritative data:

- **Vulnerability** — GDP per capita (inverted), undernourishment, under-5 mortality, rural
  population share (harder-to-reach).
- **Readiness gap** — access to electricity (inverted), basic drinking water (inverted), mobile
  subscriptions per 100 (inverted; capped at 100 = saturated reach — a proxy for how far a mobile
  warning can travel, EW4All Pillar 3).

Steps: set each indicator's polarity so higher = worse → min-max normalise 0–1 across the seven
countries → average available indicators per dimension → composite =
`geometric_mean(vulnerability, readiness_gap) × 100` → rank. Missing values (Antigua's
undernourishment and mobile figures) are left blank and simply excluded from that country's
dimension average — never imputed.

Index values are **relative across these seven countries** (a prioritisation tool), not absolute
global risk scores. A physical hazard/exposure term is intentionally out of scope here; the code
is structured so a hazard column (e.g. from the JRC INFORM Risk Index or EM-DAT) can be added
directly.

## How this maps to EW4All

| EW4All pillar | Lead agency | This repo |
|---|---|---|
| 1. Risk knowledge | UNDRR | vulnerability dimension + country ranking |
| 2. Detection / monitoring | WMO | (out of scope — hazard term is pluggable) |
| 3. Warning dissemination | ITU | mobile-reach indicator in the readiness gap |
| 4. Preparedness & response | IFRC | readiness gap → where basic systems are weakest |

## Run it

```bash
pip install -r requirements.txt
python src/fetch_data.py      # re-fetch the latest real data from the World Bank API
python src/build_index.py     # compute the index + write results/ charts and CSV
```

Or open the notebook in Google Colab via the badge above (zero setup).

## Repository layout

```
climate-risk-early-warning/
├── data/
│   ├── worldbank_indicators.csv   # real values (committed snapshot, accessed 2026-07-06)
│   └── sources.md                 # indicator codes, years, definitions, limitations
├── src/
│   ├── fetch_data.py              # live fetch from api.worldbank.org (reproduces the CSV)
│   └── build_index.py             # computes index + charts
├── results/
│   ├── vulnerability_readiness_index.csv
│   ├── index_ranking.png
│   └── indicator_heatmap.png
├── notebook.ipynb
├── requirements.txt
└── LICENSE
```

## Data & licence

Data © World Bank, [Open Data](https://data.worldbank.org/) (CC BY 4.0). Code released under the
MIT Licence.
