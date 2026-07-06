# EW4All Multi-Hazard Risk & Readiness Index

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Pr0spektor/climate-risk-early-warning/blob/main/notebook.ipynb)

A reproducible, **real-data** analysis for the seven Green Climate Fund
**Early Warnings for All (EW4All)** pilot countries — Antigua and Barbuda, Cambodia, Chad,
Ecuador, Ethiopia, Fiji and Somalia.

It answers a concrete prioritisation question:

> **Where do high hazard & exposure, high human vulnerability, and weak basic systems
> (power, water, mobile reach) coincide — so an early-warning programme should act first?**

Every input is **official open data**, fetched live:

- **Hazard & Exposure** — [JRC INFORM Risk 2023](https://drmkc.jrc.ec.europa.eu/inform-index)
  (Hazard & Exposure component, 0–10).
- **Vulnerability & Readiness** — [World Bank Open Data](https://data.worldbank.org/)
  (GDP/capita, undernourishment, under-5 mortality, rural share; electricity, water, mobile reach).

Accessed 2026-07-06. Full indicator codes, years and URLs in [`data/sources.md`](data/sources.md).

## Result

![Index ranking](results/index_ranking.png)

| Rank | Country | Index (0–100) | Hazard | Vulnerability | Readiness gap | INFORM (ref) |
|---|---|---|---|---|---|---|
| 1 | Somalia | 84.4 | 1.00 | 0.80 | 0.73 | 8.9 |
| 2 | Chad | 67.1 | 0.28 | 0.86 | 0.88 | 6.5 |
| 3 | Ethiopia | 65.9 | 0.52 | 0.67 | 0.79 | 6.5 |
| 4 | Cambodia | 25.6 | 0.22 | 0.39 | 0.16 | 4.7 |
| 5 | Ecuador | 20.4 | 0.33 | 0.23 | 0.05 | 4.1 |
| 6 | Fiji | 11.9 | 0.03 | 0.27 | 0.05 | 2.9 |
| 7 | Antigua and Barbuda | 10.9 | 0.00 | 0.33 | 0.00 | 2.5 |

**Independent validation:** the ranking matches the JRC INFORM *overall* risk score — which is
**not** used in the composite — at a Spearman rank correlation of **ρ ≈ 0.99**. The two were
built from different inputs, so the agreement is a genuine cross-check, not circular.

![Indicator heatmap](results/indicator_heatmap.png)

## Method

Three INFORM-style dimensions, each from real open data:

- **Hazard & Exposure** — INFORM Risk 2023 Hazard & Exposure component.
- **Vulnerability** — GDP/capita (inverted), undernourishment, under-5 mortality, rural share
  (harder-to-reach populations).
- **Readiness gap** — access to electricity (inverted), basic drinking water (inverted), mobile
  subscriptions per 100 (inverted, capped at 100 = saturated reach — a proxy for how far a mobile
  warning can travel, EW4All Pillar 3).

Steps: set each indicator's polarity so higher = worse → min-max normalise 0–1 across the seven
countries → average the available indicators per dimension → composite =
**arithmetic mean of the three dimensions × 100** → rank. An arithmetic mean is used (rather than
a geometric mean) so a country that is best-in-class on one dimension is not forced to an
artificial 0. Missing values (Antigua's undernourishment and mobile figures) are left blank and
excluded from that country's dimension average — never imputed.

Index values are **relative across these seven countries** (a prioritisation tool), not absolute
global scores.

## How this maps to EW4All

| EW4All pillar | Lead agency | This repo |
|---|---|---|
| 1. Risk knowledge | UNDRR | hazard + vulnerability dimensions & country ranking |
| 2. Detection / monitoring | WMO | hazard dimension (INFORM) |
| 3. Warning dissemination | ITU | mobile-reach indicator in the readiness gap |
| 4. Preparedness & response | IFRC | readiness gap → where basic systems are weakest |

## Run it

```bash
pip install -r requirements.txt
python src/fetch_data.py      # re-fetch the latest real data from the World Bank + INFORM APIs
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
│   ├── fetch_data.py              # live fetch from World Bank + JRC INFORM APIs
│   └── build_index.py             # computes index + charts + validation
├── results/
│   ├── index.csv
│   ├── index_ranking.png
│   └── indicator_heatmap.png
├── notebook.ipynb
├── requirements.txt
└── LICENSE
```

## Data & licence

World Bank data © World Bank ([CC BY 4.0](https://data.worldbank.org/)). INFORM Risk © European
Commission Joint Research Centre / INFORM. Code released under the MIT Licence.
