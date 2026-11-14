# CASI-Net verification protocol

## Claims, inputs and computed evidence

**Manuscript-reported values** in `reference/` are targets. **Source measurements** belong in `data/measurements/` and `data/manifests/` after provenance checks. **Computed results** are written in `outputs/` and are never backfilled from targets.

1. **Event provenance (P0)**: complete `reporting_units.csv`, `parent_events.csv`, `original_and_repaired_pairs.csv`, and `benchmark_label_audit.csv`. Check source identifiers, UTC timestamps, 10-m grid footprints, masks, hashes, and lineage. Distinguish 165 dataset-level reporting units from independent parent physical floods. Run `audit_provenance.py --mode submission`; investigate every flagged overlap rather than deleting it to pass validation.
2. **SOTA and ablations (P0)**: import confusion counts per event × model × seed, preserving the exact valid-mask hashes. `recompute_experiments.py` recomputes F1/mIoU, equal-event paired 10,000-draw bootstrap (seed 2026) and LOEO. Separate five-run SD from event-level bootstrap. The 2×2 contrast is `Full − No contour − No source + No both` using aligned events.
3. **Conformal (P1)**: import candidate-level Monte Carlo p-values, eligible labels and exact parent event split. In calibration, uniformly draw one verified eligible genuine candidate per independent calibration event, use `C = −log(p)`, order-statistic index `ceil((n+1)(1−alpha))`, and strict rejection `C > tau`. Discrete MC null (199 replicates) p spacing is 0.005. Guarantee is marginal over event-level sampling, not pixelwise/classwise.
4. **Hydraulics (P1)**: import four configurations for the same 48 stage-rise and 104 depth-reference sites, with the exact HEC-RAS acquisition matching, reference height datum and exclusion reasons. The `point_only` variant has no interval. Never infer stage change by differencing gauges at different stations. Confirm 18 independent gauges were excluded from forcing/calibration. Report that HEC-RAS results are model-based references rather than independent depth field measurements.
5. **Core physics (P1)**: use `surface_solver.py` / `pair_sampling.py` / `priority_flood.py` with real input grids and saved random seeds. Assert gradient feasibility, datum equivariance, paired monotone extents, crossfit buffer disjointness, and source-connected change. `surface_solver.py` is a numerical reference implementation and requires solver trace comparison to the training-time production backend before claiming exact algorithmic reproducibility.
6. **Failures (P2)**: archive real masks/observations for urban DEM uncertainty, stage recession (A5), river-network omission and vegetated SAR miss. Examples must be traceable to actual events and reference imagery; not selected using unavailable field-truth values.

## Important protocol distinctions

- Kuro Siwo/MMFlood may require additional optical pairing; do not treat their native SAR-only measurements as native optical.
- Native CAU-Flood and Sen2GF3 bands are often 4 optical channels, not ten; fixed zero-fill is used only after training-derived normalization for missing channels. GF-3 HH/HV and Sentinel-1 VV map to co-/cross-polarized input positions according to the frozen preprocessing rules.
- FABDEM ~30 m interpolated to the 10-m analysis grid is not 10-m independent terrain accuracy.
- `p_change` reachability is computed per PAIR of DEM draws; do not subtract unrelated MC sets.
- Nominal 90% water-depth intervals are terrain-model/candidate-geometry conditional; conformal FRR calibration is a separate guarantee.
- The 92.9% ratio is HEC-RAS depth-reference site validity (104/112), not final mapped-product availability.

## What this archive cannot independently verify without source files

True parent-event identities, raw GEE product IDs, image registration shifts, original mask edits, original learned weights, actual five-run predictions, baseline input parity, contour p-values, ATL08 semivariograms, gauge observations, HEC-RAS meshes and boundary hydrographs, scene-scale timing, or spatial examples. A green unit-test badge means tested software operators passed controlled inputs; it does not certify these empirical claims.
