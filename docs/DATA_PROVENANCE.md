# Data provenance and review conventions

## Identity and unit of analysis

1. `reporting_unit_id` identifies a dataset-level reporting / acquisition unit, **not a physical event**.
2. `parent_event_uid` groups acquisitions, tiles, near-duplicates and alternate optical pairings of the same disaster + hydrological system + acquisition window. One parent must belong to one partition.
3. A scene published in multiple benchmarks is linked to the same parent unless independently documented as a distinct physical event.
4. Use original archive product IDs and immutable time stamps. No placeholder or guessed identifiers may be used in released rows.

## Optical re-pairing

For each of the 12 manuscript-reported replaced scenes, retain: released optical product ID and date; used pre-flood Sentinel-2 product ID and date; SAR product ID and date; GEE query/export record; cloud/valid masks; co-registration diagnostics; original positive-change reference; adjudication decision; retained, corrected and excluded pixel counts. The first 1.60% disagreement denominator is 2.40 million jointly valid pixels; 0.24% flagged and 0.07% confirmed use *original positive-change pixels* as denominator.

## Checking duplicates

A spatial–temporal screening hit is **not proof of leakage**. Check exact source IDs and parent event identity. The 14-day window and 0.95 hash-warning threshold are from the supplementary protocol; a 500-m footprint proximity buffer is only a screening convention. Record human resolution in `reviewed_overlap_exceptions.csv` with supporting external evidence. Different sensors or spectral renderings are not directly comparable using naive perceptual hashes.

## Asset checks

Compute SHA-256 from real file bytes (mask, footprint, corrected labels), not from a guessed string. If referenced assets are remote or cannot be read locally, report them as unverified; never claim checksum-verified status.

## Scope of the checks

These tools test internal consistency, overlap indications, declared metadata, and file integrity. They **do not** attest that an external scene ID, experiment, model or ground-truth label is authentic. Public claims must be supported by independently checkable underlying sources.
