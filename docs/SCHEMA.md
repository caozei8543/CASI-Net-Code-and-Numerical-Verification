# Manifest schemas

| File | Row granularity | Primary key |
|---|---|---|
| `reporting_units.csv` | Dataset reporting/acquisition unit | `reporting_unit_id` |
| `parent_events.csv` | Distinct physical flood event / hydrological system | `parent_event_uid` |
| `original_and_repaired_pairs.csv` | Optical–SAR pairing of a reporting unit | `reporting_unit_id` |
| `benchmark_label_audit.csv` | Independently reviewed optical-replacement scene | `label_audit_id` |

`parent_events.reporting_unit_ids` is a semicolon-separated list of all member reporting-unit IDs. The complete fields and their meanings are documented in [`FIELD_DICTIONARY.csv`](FIELD_DICTIONARY.csv).

Source provenance is recorded in `source_record_uri` and `decision_record_path`; the source IDs and recorded author decisions are *not* inferred automatically by the validator. The `record_status` field denotes the local source-review workflow and does not itself prove authenticity.

The reference allocations appear in `configs/paper_reported_constants.json`. A mismatch with source records is a **finding**, not a reason to alter observations.
