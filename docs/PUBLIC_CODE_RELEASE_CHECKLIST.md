# Code-only public release checklist

- [ ] Obtain approval from project authors/rightsholders for the MIT license notice.
- [ ] Confirm original source code is permitted to be published, including any imported third-party code.
- [ ] Verify that no satellite images, private event IDs, spatial footprints, stage/gauge observations, calibrator score logs, HEC-RAS projects or checkpoints are committed.
- [ ] Check `reference/` contains only **reported aggregate** manuscript results; `templates/` are header-only.
- [ ] Run `python -m pip install -e . pytest` and `python -m pytest -q` in a clean environment.
- [ ] Run `python scripts/check_reported_arithmetic.py` and `python scripts/verify_repository_checksums.py`.
- [ ] Push to GitHub and confirm the `CI` check is green on a clean Linux runner.
- [ ] Cite the manuscript faithfully; do not describe these numerical references as an official pretrained or full paper-reproduction release.
- [ ] Confirm `CITATION.cff` metadata and authorship information before release.

The user-supplied original experiment records, if they exist in local workstations, should not be copied into this public code-only repository. A successful local unit test is not an experimental verification claim.
