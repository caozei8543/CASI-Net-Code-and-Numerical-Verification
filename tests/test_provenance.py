import contextlib
import csv
import io
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_provenance import audit, parse_bool, parse_date, good_sha  # noqa: E402


class AuditTests(unittest.TestCase):
    def test_iso_times_must_have_timezone(self):
        self.assertIsNone(parse_date("2024-06-20T11:30:00"))
        self.assertIsNotNone(parse_date("2024-06-20T11:30:00Z"))
        self.assertIsNotNone(parse_date("2024-06-20T11:30:00+08:00"))

    def test_hash_and_booleans(self):
        self.assertTrue(good_sha("a" * 64))
        self.assertFalse(good_sha("a" * 63))
        self.assertIsNone(parse_bool("maybe"))
        self.assertTrue(parse_bool("true"))

    def test_empty_repository_does_not_validate_as_real_data(self):
        with tempfile.TemporaryDirectory() as td:
            base = pathlib.Path(td) / "manifests"
            base.mkdir()
            for path in (ROOT / "templates").glob("*.csv"):
                (base / path.name).write_bytes(path.read_bytes())
            output = pathlib.Path(td) / "report"
            with contextlib.redirect_stdout(io.StringIO()):
                ok = audit(base, "submission", output, {})
            self.assertFalse(ok)
            report = json.loads((output / "audit_report.json").read_text("utf-8"))
            self.assertTrue(any(e["code"] == "EMPTY_CORE" for e in report["errors"]))

    def test_parent_cross_split_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            base = pathlib.Path(td) / "manifests"
            base.mkdir()
            for path in (ROOT / "templates").glob("*.csv"):
                with path.open(encoding="utf-8", newline="") as f:
                    headers = next(csv.reader(f))
                with (base / path.name).open("w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    if path.name == "reporting_units.csv":
                        for unit, split in (("u_train", "train"), ("u_test", "test")):
                            writer.writerow({"reporting_unit_id": unit, "parent_event_uid": "same_parent", "dataset": "CAU-Flood", "split": split})
                    elif path.name == "parent_events.csv":
                        writer.writerow({"parent_event_uid": "same_parent", "split": "train", "reporting_unit_ids": "u_train;u_test", "datasets_in_group": "CAU-Flood"})
                    elif path.name == "original_and_repaired_pairs.csv":
                        writer.writerow({"reporting_unit_id": "u_train", "parent_event_uid": "same_parent", "dataset": "CAU-Flood", "split": "train"})
                        writer.writerow({"reporting_unit_id": "u_test", "parent_event_uid": "same_parent", "dataset": "CAU-Flood", "split": "test"})
                    elif path.name == "benchmark_label_audit.csv":
                        writer.writerow({"label_audit_id": "test_fixture", "reporting_unit_id": "u_train"})
            output = pathlib.Path(td) / "report"
            with contextlib.redirect_stdout(io.StringIO()):
                ok = audit(base, "submission", output, {})
            self.assertFalse(ok)
            report = json.loads((output / "audit_report.json").read_text("utf-8"))
            self.assertTrue(any(e["code"] == "PARENT_CROSSES_SPLITS" for e in report["errors"]))


if __name__ == "__main__":
    unittest.main()
