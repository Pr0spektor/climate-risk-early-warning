# Multi-hazard risk index (EW4All pilot countries)

Transparent INFORM-style composite risk index across the seven EW4All GCF countries, used to
prioritise where early-warning investment matters most.

**Run:** `python risk_index.py`

**Outputs:** `risk_ranking.png` (ranked bar chart) and `risk_index_results.csv`.

**Method:** geometric-mean aggregation of Hazard & Exposure, Vulnerability, and Lack of Coping
Capacity (so no dimension is masked), rescaled 0–10 and ranked.

**Data:** `data.csv` holds ILLUSTRATIVE 0–10 indicator scores set to well-known public relative
patterns. Swap in official INFORM / ND-GAIN / EM-DAT values to operationalise — the method is
unchanged.

Maps to EW4All Pillar 1 (risk knowledge) and Pillar 4 (preparedness prioritisation).
