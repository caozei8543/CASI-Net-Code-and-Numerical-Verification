#!/usr/bin/env python3
"""Public release gate. Ensures measurements exist and excludes test fixtures.
Never interprets mere structural checks as independent source authentication.
"""
from pathlib import Path
import argparse,csv,json,sys,subprocess
ROOT=Path(__file__).resolve().parents[1]
MANIFESTS=("reporting_units.csv","parent_events.csv","original_and_repaired_pairs.csv","benchmark_label_audit.csv")
MEASUREMENTS=("event_confusions.csv","ablation_per_event.csv","contour_candidates.csv","hecras_reference_sites.csv","hecras_models.csv","gauge_checks.csv")
BAD_TOKENS=("synthetic","fixture","placeholder","to_fill","demo_not_data","illustrative")
def scan_csv(path):
    if not path.is_file():return "MISSING"
    with path.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        rows=list(reader)
    if not rows:return "HEADER_ONLY"
    for row in rows:
        for val in row.values():
            value=str(val or "").lower()
            if any(token in value for token in BAD_TOKENS):return "EXAMPLE_RECORD_DETECTED"
    return "PRESENT_NOT_SOURCE_VERIFIED"
def check(root=ROOT, require_weights=False):
    details={}
    for name in MANIFESTS:details["data/manifests/"+name]=scan_csv(root/"data"/"manifests"/name)
    for name in MEASUREMENTS:details["data/measurements/"+name]=scan_csv(root/"data"/"measurements"/name)
    details["LICENSE"]="PRESENT" if (root/"LICENSE").is_file() else "MISSING"
    details["checkpoints/checkpoint_manifest.json"]="PRESENT" if (root/"checkpoints"/"checkpoint_manifest.json").is_file() else "MISSING"
    blockers=[k+": "+v for k,v in details.items() if v in {"MISSING","HEADER_ONLY","EXAMPLE_RECORD_DETECTED"}]
    if not require_weights:blockers=[x for x in blockers if not x.startswith("checkpoints/")]
    return {"status":"STRUCTURE_ELIGIBLE_FOR_FURTHER_AUTHENTICATION" if not blockers else "NOT_READY_FOR_FULL_EMPIRICAL_RELEASE", "blockers":blockers, "checks":details, "disclaimer":"Passing structural checks cannot independently establish that reported experimental measurements are authentic."}
def main():
    p=argparse.ArgumentParser();p.add_argument("--require-weights",action="store_true");p.add_argument("--output",default="outputs/release_gate.json");p.add_argument("--strict",action="store_true");a=p.parse_args()
    result=check(require_weights=a.require_weights)
    out=ROOT/a.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2),encoding="utf8")
    print(json.dumps({"status":result["status"],"blockers":result["blockers"],"report":str(out)},ensure_ascii=False,indent=2))
    if a.strict and result["blockers"]:sys.exit(2)
if __name__=="__main__":main()
