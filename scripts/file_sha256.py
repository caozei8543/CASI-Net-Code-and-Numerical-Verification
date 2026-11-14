#!/usr/bin/env python3
"""Compute cryptographic checksums of real files. Does not validate their scientific meaning."""
import argparse,hashlib,pathlib,json,sys
p=argparse.ArgumentParser();p.add_argument('files',nargs='+',type=pathlib.Path);a=p.parse_args()
ok=True
for f in a.files:
 if not f.is_file():print(f'MISSING: {f}',file=sys.stderr);ok=False;continue
 h=hashlib.sha256()
 with f.open('rb') as fp:
  for chunk in iter(lambda:fp.read(1024*1024),b''):h.update(chunk)
 print(f'{h.hexdigest()}  {f}')
sys.exit(0 if ok else 2)
