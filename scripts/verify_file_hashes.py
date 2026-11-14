#!/usr/bin/env python3
"""Verify actual on-disk mask/label file bytes against CSV SHA-256 fields."""
import argparse,csv,hashlib,json,pathlib,re,sys,urllib.parse
TASKS=[
 ('reporting_units.csv','valid_mask_path','valid_mask_sha256'),
 ('original_and_repaired_pairs.csv','original_mask_path','original_mask_sha256'),
 ('original_and_repaired_pairs.csv','used_mask_path','used_mask_sha256'),
 ('benchmark_label_audit.csv','corrected_label_path','corrected_label_sha256'),
 ('benchmark_label_audit.csv','valid_mask_path','valid_mask_sha256'),
]
p=argparse.ArgumentParser();p.add_argument('--input',type=pathlib.Path,required=True);p.add_argument('--files-root',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
cache={};result={'verified_files':0,'mismatched':[],'missing':[],'remote_unverified':[],'missing_sha256':[]}
def sha(path):
 if path not in cache:
  h=hashlib.sha256()
  with path.open('rb') as f:
   for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
  cache[path]=h.hexdigest()
 return cache[path]
for csvname,col,hcol in TASKS:
 pth=a.input/csvname
 if not pth.exists():result['missing'].append(f'{csvname} file absent');continue
 with pth.open(encoding='utf-8-sig',newline='') as f:
  for rownum,row in enumerate(csv.DictReader(f),2):
   val=(row.get(col) or '').strip();want=(row.get(hcol) or '').strip().lower()
   if not val or val.startswith('SYNTHETIC'):
    result['missing'].append(f'{csvname}:{rownum} {col} missing/source is synthetic');continue
   if val.startswith(('https://','http://','s3://','gs://')):
    result['remote_unverified'].append(f'{csvname}:{rownum} {col}: {val}');continue
   if not re.fullmatch('[0-9a-f]{64}',want):
    result['missing_sha256'].append(f'{csvname}:{rownum} {hcol}');continue
   file=pathlib.Path(val)
   if not file.is_absolute():file=a.files_root/file
   if not file.is_file():result['missing'].append(f'{csvname}:{rownum} {col}: {file}');continue
   got=sha(file)
   if got!=want:result['mismatched'].append(f'{csvname}:{rownum}: {file} expected {want}, got {got}')
   else:result['verified_files']+=1
ok=not any(result[k] for k in ('missing','mismatched','missing_sha256','remote_unverified'))
result['verdict']='LOCAL_CHECKSUMS_VERIFIED' if ok else 'NOT_FULLY_VERIFIED'
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(f'{result["verdict"]}: verified={result["verified_files"]}, missing={len(result["missing"])}, mismatch={len(result["mismatched"])}, remote_unverified={len(result["remote_unverified"])}')
sys.exit(0 if ok else 2)
