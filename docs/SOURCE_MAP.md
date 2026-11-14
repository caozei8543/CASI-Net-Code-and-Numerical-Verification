# Traceability from manuscript to computational audit

| Main text / supplement | Implemented check | Verifiable input | Boundaries of the check |
|---|---|---|---|
| IV-A / S2-S3 | `audit_provenance.py` | original event lineage and paired scene IDs | flags suspicious overlap; needs source review to resolve |
| IV-A-B / S12 | `evaluate.py`, `bootstrap.py` | mask confusion counts per seed × independent event | cannot infer archived predictions from Table I means |
| III-E / S7, IV-C | `contour_calibration.py`, `contour_crossfit.py` | true anchors, p-values, event eligibility | valid only with exchangeable events and same sampling rule |
| III-D / S6 | `surface_solver.py` | interpolation matrix, anchors, grid graph | numerical reference only; check production solver parity |
| III-F–G / S8 | `pair_sampling.py`, `priority_flood.py` | matched DEM and candidate surfaces | constrained model nesting, not guaranteed true flood dynamics |
| III-G / S9 | `fusion.py` | bounded pre/post logits, source-constrained hydrology | cannot recover candidates omitted upstream by image decoders |
| IV-D / S10–S12 | `ablation.py` | aligned event-by-configuration F1 | interaction needs event bootstrap for significance |
| IV-E / S13 | `hydraulic_validation.py` | reference site positions, model predictions, intervals | HEC-RAS references are not absolute field truth |
| IV-F / S14 | `runtime_logs.csv` schema | original hardware/scene timing | no runtime performance inferred from script unit tests |
| S15 | `failure_cases.csv` schema | actual source-image examples | no qualitative scenes invented in this archive |

## Reported-protocol values captured

- Full protocol: `configs/paper_frozen_protocol.json`
- S2 event allocations and primary claims: `reference/manuscript_claims.json`
- Published result rows: `reference/main_table_{I,II,III,IV}_reported.csv`
- Extra HAND baseline: `reference/supp_table_S10_reported.csv`
- HEC-RAS event-site counts: `reference/supp_table_S11_reported.csv`

A reported reference row is a *target for independent recalculation*, not evidence of its own experimental origin.
