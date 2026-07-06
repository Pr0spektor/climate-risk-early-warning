# Subsidence / ground-deformation early-warning

Monitoring → detection → tiered-warning workflow for ground deformation (subsidence, sudden
movement), translated from geodynamic geohazard monitoring into a generic early-warning setting.

**Run:** `python analysis.py`

**Outputs:** `monitoring_alerts.png` (per-station series with WATCH/WARNING/CRITICAL flags) and
`alert_log.csv` (first onset of each tier per station).

**Method:** robust rolling velocity (mm/yr) + MAD-based control-chart anomaly score; explicit,
auditable thresholds; tiered alerting for dissemination. Data is synthetic (fixed seed) — replace
`load_series()` with real InSAR / GNSS / levelling data to operationalise.

Maps to EW4All Pillar 2 (detection & monitoring) and Pillar 3 (warning dissemination).
