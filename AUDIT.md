# Methodology audit — EW4All Risk & Readiness Index

A reviewer-grade pass over the index: what is defensible, what is not, what was changed in
this pass, and what a critical reader should still discount. Written to be read alongside
`results/index.csv`.

## Findings

| # | Severity | Finding | Status |
|---|---|---|---|
| 1 | High | The hazard dimension is a single imported composite (INFORM Hazard & Exposure) carrying a third of the weight, with no internal structure this repository can inspect. | **Quantified.** Hazard weight swept 0–0.5: max rank shift 2 positions, 5 of 7 countries move at most one place. Table in `results/weight_sensitivity.csv`. Not replaced — the underlying sub-indicators are not in the dataset. |
| 2 | High | Dimension scores averaged whatever indicators were present. A country with one of three readiness indicators would have been scored on that one, on the same 0–1 scale as a country built from three — a silent reward for missing data. | **Fixed.** `dimension_score` now requires at least two indicators (or all, if the dimension has only one), otherwise the dimension is reported missing and the composite re-weights. Coverage is written per country to `index.csv`. On the current seven countries the rule changes nothing; it exists so the next data refresh cannot introduce the bias unnoticed. |
| 3 | Medium | Min–max normalisation is relative to this seven-country sample. Adding or removing a country moves every score, so the 0–100 index is a ranking device, not an absolute risk level. | **Open, by design.** Stated in the README. An absolute version would need fixed anchor values per indicator, which is a different (and much larger) data collection. |
| 4 | Medium | Mixed vintages: INFORM 2023 hazard against World Bank indicators from different years (some 2021–2023, some 2024). | **Open.** Documented per indicator in `data/sources.md`. A vintage-aligned rebuild should wait for the next INFORM release rather than mix further. |
| 5 | Medium | Equal weights across the three dimensions are an assumption, not a measurement. | **Partially addressed.** Only the hazard weight is swept. Sweeping all three is a 2-simplex; the current single-axis sweep is the part that matters because hazard is the borrowed one. |
| 6 | Low | No population weighting. Antigua and Barbuda (94k) counts as much as Ethiopia (132M). | **Open, by design.** The index answers "where is the gap largest relative to the country's own capacity", not "where are most people affected". A population-weighted variant is a one-line change and would answer a different question. |
| 7 | Low | External validation rests on a single correlation with INFORM's overall risk (Spearman 0.99). | **Open.** Agreement with one related composite is weak evidence: both share the INFORM hazard input. An independent check against, say, actual EW4All disbursements would be stronger and is not available publicly. |

## What a top-tier reviewer would still say

The index is a prioritisation tool built on nine public indicators for seven countries. That is
a defensible piece of analysis and an indefensible piece of measurement: with seven units, a
two-position rank shift is within noise, and no amount of weighting discipline fixes a sample
that small. The honest framing — used in the README — is that the index orders seven named
countries for a programme decision, not that it estimates climate risk.

The gap to a top-five consulting deliverable is not in the arithmetic. It is in the missing
primary layer: no in-country validation, no stakeholder weighting elicitation, no
disbursement data to test the ranking against outcomes. Those are fieldwork, not code.

## Reproduce

```bash
pip install -r requirements.txt
python src/build_index.py     # writes results/index.csv, weight_sensitivity.csv, figures
python -m pytest -q           # 8 tests
```
