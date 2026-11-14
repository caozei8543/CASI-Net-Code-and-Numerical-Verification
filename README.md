# CASI-Net: Code and Numerical Verification

[中文说明](README.zh-CN.md)

Companion **code-only** repository for the manuscript **“Observability-Aware Counterfactual Water-Surface Inference for Heterogeneous SAR–Optical Flood Change Detection.”**

This release provides executable reference implementations of selected mathematical components, parameter configurations, manuscript-reported aggregate reference tables, input schemas, and automated software tests. **No satellite images, event-level records, raw HEC-RAS results, calibration-score logs, or trained checkpoints are distributed.** The full neural-network training/inference implementation is not included. The physical solver is a stand-alone numerical reference and has not been independently matched to the authors' production checkpoint/solver.

## Quick start

Requires Python 3.10+.

```bash
python -m pip install -e . pytest
python -m pytest -q
python scripts/check_reported_arithmetic.py
python scripts/verify_repository_checksums.py
```

The unit tests use small mathematical arrays created within the test code; they do not require research data or network access. Passing the tests verifies **software behavior on those test cases**, not the paper's empirical F1 scores, physical-model accuracy, or the authenticity of experimental records.

## What is published

| Component | Source |
|---|---|
| Hydraulically bounded surface inversion (IRLS/ADMM numerical reference) | `casinet_repro/surface_solver.py` |
| Candidate/shoreline helpers and contour hold-out statistic | `casinet_repro/make_candidates.py`, `casinet_repro/contour_crossfit.py` |
| Monte Carlo p-values and event-level conformal calibration | `casinet_repro/contour_calibration.py` |
| Spatially correlated, shared-state terrain perturbations | `casinet_repro/pair_sampling.py` |
| Source-constrained 8-connected minimax reachability | `casinet_repro/priority_flood.py` |
| Physically informed logit fusion | `casinet_repro/fusion.py` |
| Evaluation metrics, event bootstrap and ablation checks | `casinet_repro/evaluate.py`, `casinet_repro/bootstrap.py`, `casinet_repro/ablation.py` |
| HEC-RAS site-metric evaluation logic | `casinet_repro/hydraulic_validation.py` |
| Frozen manuscript settings and *reported* numerical results | `configs/`, `reference/` |
| Automated tests, GitHub Actions and repository SHA-256 checks | `tests/`, `.github/workflows/ci.yml`, `SHA256SUMS.txt` |

## Reproducibility boundaries

`reference/` contains aggregate values reported in the manuscript, *not* generated raw observations. `templates/` contains **empty CSV schemas only** for researchers who have legitimate access to their own data. Local verification scripts (`scripts/audit_provenance.py`, `scripts/recompute_experiments.py`, `scripts/compute_conformal.py`) accept such inputs when supplied by the user; no experiment-level data are bundled here.

The `scripts/check_reported_arithmetic.py` command checks arithmetic consistency of published aggregates, including the two-factor ablation interaction and hydraulic-site count totals. This is **not** independent reproduction of Tables I–IV.

The experiment-level scripts intentionally cannot verify Table I–IV in a fresh download without the research records. This is expected, not a build failure. The `scripts/release_gate.py` command is only for checking whether a local private working copy has the inputs required for a different, *full empirical* release; it is not the gate for publishing this code-only repository.

### Reported protocol highlights

- Analysis grid: **10 m**; water-surface grid: **90 m**.
- Hydraulic gradient cap: **0.003 m/m**.
- Contour cross-fitting: **five** arcs, **300 m** exclusion buffer, **199** reference simulations.
- Paired spatial DEM perturbations: **200** draws; correlation length **250 m**, nugget scale **0.35 m**.
- Primary event-level conformal false-rejection target: **0.10**.
- Fusion parameters: `L_max=4`, `gamma=0.7`, `epsilon=0.0025`.

The frozen configurations in `configs/` and detailed source mappings in `docs/` contain further values and scope qualifications. They describe reported protocol settings and do not constitute author-trained weights.

## Integrity and CI

`SHA256SUMS.txt` covers published repository files, except itself. Verify with `python scripts/verify_repository_checksums.py`, or `sha256sum -c SHA256SUMS.txt` on systems that provide `sha256sum`. Every push/PR runs unit tests, arithmetic checks and the integrity command in GitHub Actions. Rebuild the checksum manifest **after any authorized edits**.

## Rights and citation

This repository includes an MIT license text for **original repository code only**; project rights holders must approve this grant before publication. Third-party datasets and software retain their respective license terms. No datasets, model weights, or hydraulic project artifacts are licensed or redistributed here. See `CITATION.cff` and [publication checklist](docs/PUBLIC_CODE_RELEASE_CHECKLIST.md).

**Scope:** numerical reference code and verification utilities, **not** a trained end-to-end CASI-Net release and **not** a complete paper-reproduction deposit.
