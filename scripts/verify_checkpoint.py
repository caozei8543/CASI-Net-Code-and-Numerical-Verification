#!/usr/bin/env python3
"""Verify actual author model artifact SHA-256. No synthetic/random weights are accepted."""
from pathlib import Path
import argparse,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def verify(manifest,strict=False):
    info=json.loads(Path(manifest).read_text(encoding="utf8"))
    errors=[]
    fp=ROOT/str(info.get("checkpoint_file", ""))
    expected=str(info.get("sha256", "")).strip().lower()
    if not expected or len(expected)!=64 or any(c not in "0123456789abcdef" for c in expected):errors.append("Missing valid author checkpoint SHA-256")
    if not fp.is_file():errors.append("Missing original checkpoint file")
    elif expected:
        hasher=hashlib.sha256()
        with fp.open("rb") as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b""):hasher.update(chunk)
        if hasher.hexdigest()!=expected:errors.append("Checkpoint checksum mismatch")
    for key in ("training_manifest_sha256","training_code_commit","authors_redistribution_approval"):
        if not info.get(key):errors.append("Missing attestation: "+key)
    return {"status":"INTEGRITY_CHECK_PASSED_NOT_TRAINING_AUTHENTICATED" if not errors else "NOT_VERIFIED", "errors":errors,"checkpoint_file":str(fp)}
def main():
    p=argparse.ArgumentParser();p.add_argument("--manifest",default="checkpoints/checkpoint_manifest.json");p.add_argument("--strict",action="store_true");a=p.parse_args()
    path=ROOT/a.manifest if not Path(a.manifest).is_absolute() else Path(a.manifest)
    if not path.is_file():print("NOT_VERIFIED: supply original checkpoint_manifest.json");sys.exit(2 if a.strict else 0)
    r=verify(path);print(json.dumps(r,indent=2))
    if a.strict and r["errors"]:sys.exit(2)
if __name__=="__main__":main()
