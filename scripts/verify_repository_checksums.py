#!/usr/bin/env python3
"""Verify SHA-256 of all published tracked files listed by the release manifest.

This check proves file integrity only, not experimental authenticity.
"""
from pathlib import Path
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'SHA256SUMS.txt'

def main():
    if not MANIFEST.exists():
        print('ERROR: SHA256SUMS.txt not found'); return 2
    lines=[s.strip() for s in MANIFEST.read_text(encoding='utf8').splitlines() if s.strip()]
    failures=[]
    for line in lines:
        try:expected, rel=line.split('  ',1)
        except ValueError:
            failures.append('malformed manifest entry'); continue
        file=ROOT/rel
        if not file.is_file():
            failures.append(f'missing: {rel}'); continue
        actual=hashlib.sha256(file.read_bytes()).hexdigest()
        if actual!=expected:failures.append(f'checksum mismatch: {rel}')
    prohibited=[p for p in ('data','checkpoints','tests/fixtures','docs/TEST_INPUT_PREVIEW.html') if (ROOT/p).exists()]
    if prohibited:failures.append('excluded records present: '+', '.join(prohibited))
    if failures:
        for issue in failures: print('FAIL:',issue)
        return 2
    print(f'PASS: {len(lines)} repository files match SHA-256; no excluded records or checkpoints present.')
    return 0
if __name__=='__main__':sys.exit(main())
