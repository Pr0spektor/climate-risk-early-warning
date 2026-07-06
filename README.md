# Climate Risk & Early-Warning — Technical Portfolio

Author: **Pr0spektor**

A small set of **reproducible technical investigations** that demonstrate methods relevant to
multi-hazard early-warning systems (MHEWS) and climate-risk analysis — the problem space of
initiatives such as the UN **Early Warnings for All (EW4All)**.

> **Honest framing.** These are demonstration analyses built to show method and code quality.
> They use **public or clearly-synthetic illustrative data** (noted in each folder), not
> confidential project data. They translate methods I applied in 10+ years of **geodynamic
> (geohazard) monitoring and subsurface risk management** into the climate / disaster-risk
> context. Every technique here is one I can explain and defend in an interview.

## How this maps to the EW4All value chain

| EW4All pillar | Lead agency | Investigation in this repo |
|---|---|---|
| 1. Risk knowledge | UNDRR | `multihazard_risk_index/` — normalised multi-hazard exposure/vulnerability index & ranking |
| 2. Detection, observation, monitoring, forecasting | WMO | `subsidence_early_warning/` — monitoring time-series + anomaly/velocity threshold detection |
| 3. Warning dissemination & communication | ITU | alert-log output + severity tiers in `subsidence_early_warning/` |
| 4. Preparedness & response | IFRC | risk ranking to prioritise where to act first (`multihazard_risk_index/`) |

## Background this builds on (real experience)

- Designed and supervised **geodynamic monitoring / early-warning systems** for geohazards
  (ground deformation, subsidence, technology-induced seismicity) protecting populations,
  infrastructure and the environment — presented at IGU, Samarkand 2018.
- **Programme leadership** across 17 licence areas (>7,000 km²) with full CAPEX/OPEX ownership.
- **Risk & uncertainty frameworks**, audit-proof regulatory reporting, national standard authorship.
- **Python** analytical workflows (NumPy / SciPy / pandas / matplotlib) for processing, anomaly
  detection and automated reporting.

## Contents

```
climate-risk-early-warning/
├── subsidence_early_warning/     # monitoring time-series → anomaly detection → tiered alerts
├── multihazard_risk_index/       # composite risk index across the 7 EW4All pilot countries
├── requirements.txt
├── LICENSE
└── .gitignore
```

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python subsidence_early_warning/analysis.py
python multihazard_risk_index/risk_index.py
```

Each script writes its figures and a results table into its own folder.

## Countries in scope (EW4All GCF multi-country project)

Antigua and Barbuda · Cambodia · Chad · Ecuador · Ethiopia · Fiji · Somalia.
