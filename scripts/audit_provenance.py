#!/usr/bin/env python3
"""Audit reported CASI-Net data provenance before release. This is a structural validator, not ground-truth authentication."""
import argparse, collections, csv, datetime as dt, hashlib, json, math, pathlib, re, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
FILES=['reporting_units.csv','parent_events.csv','original_and_repaired_pairs.csv','benchmark_label_audit.csv']
EXPECTED={
 'Kuro Siwo': {'train':21,'validation':6,'calibration':10,'test':6},
 'MMFlood': {'train':46,'validation':15,'calibration':20,'test':14},
 'CAU-Flood': {'train':7,'validation':2,'calibration':3,'test':6},
 'Sen2GF3Floods': {'train':3,'validation':1,'calibration':2,'test':3},
}
MISSING={'','n/a','na','unknown','none','null','tbd','to_fill','placeholder'}
def parse_bool(s):
 t=str(s).strip().lower()
 if t in ('true','1','yes'):return True
 if t in ('false','0','no'):return False
 return None
def parse_date(s):
 try:
  raw=str(s).strip()
  value=dt.datetime.fromisoformat(raw.replace('Z','+00:00'))
  if value.tzinfo is None: return None
  return value.astimezone(dt.timezone.utc)
 except (TypeError, ValueError, OverflowError): return None
def normal(s):return str(s or '').strip()
def is_missing(s):return normal(s).lower() in MISSING
def synthetic(s):return 'synthetic' in normal(s).lower()
def good_sha(s):return bool(re.fullmatch(r'[0-9a-fA-F]{64}',normal(s)))
def geo_bbox(row,mode):
 try:
  b=[float(row[z]) for z in ('bbox_min_x','bbox_min_y','bbox_max_x','bbox_max_y')]
  if not b[0]<b[2] or not b[1]<b[3]:return None
  if mode=='submission' and (normal(row.get('bbox_crs'))!='EPSG:4326' or not(-180<=b[0]<b[2]<=180 and -90<=b[1]<b[3]<=90)):
   return None
  return b
 except Exception:return None
def intersect(b1,b2,buff_deg=0):
 return b1[0]<=b2[2]+buff_deg and b1[2]>=b2[0]-buff_deg and b1[1]<=b2[3]+buff_deg and b1[3]>=b2[1]-buff_deg
def read_csv(path):
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def audit(base,mode,output,config):
 problems=[]; warnings=[]; info=[]
 def error(code,msg,ids=''):problems.append({'code':code,'message':msg,'affected_ids':ids})
 def warn(code,msg,ids=''):warnings.append({'code':code,'message':msg,'affected_ids':ids})
 def passinfo(code,msg):info.append({'code':code,'message':msg})
 data={}
 for file in FILES:
  path=base/file
  if not path.exists():error('MISSING_FILE',f'Missing required CSV {file}');data[file]=[];continue
  try: data[file]=read_csv(path)
  except Exception as e:error('CSV_READ',f'{file}: {e}');data[file]=[]
 units=data[FILES[0]];parents=data[FILES[1]];pairs=data[FILES[2]];labels=data[FILES[3]]
 if not units or not parents or not pairs or not labels:
  error('EMPTY_CORE','One or more required input tables contain no records')
 for name,rows in data.items():
  if any(synthetic(v) for r in rows for v in r.values() if v is not None):
   error('NON_SOURCE_VALUES', f'{name} contains example-generated identifiers or marker values; use source records before release.')
  seen=set()
  key={'reporting_units.csv':'reporting_unit_id','parent_events.csv':'parent_event_uid','original_and_repaired_pairs.csv':'reporting_unit_id','benchmark_label_audit.csv':'label_audit_id'}[name]
  for i,r in enumerate(rows,2):
   if is_missing(r.get(key,'')):error('MISSING_KEY',f'{name} line {i}: missing {key}')
   if r.get(key,'') in seen:error('DUPLICATE_KEY',f'{name} duplicates {key}',r.get(key,''))
   seen.add(r.get(key,''))
   if mode=='submission' and normal(r.get('record_status')).lower()!='verified_actual':error('STATUS_NOT_VERIFIED',f'{name} row {i}: record_status must be verified_actual')
 counts=collections.Counter((r.get('dataset'),r.get('split')) for r in units)
 totals=collections.Counter(r.get('split') for r in units)
 for ds,splits in EXPECTED.items():
  for sp,n in splits.items():
   if counts[(ds,sp)]!=n:error('COUNT_MISMATCH',f'{ds}/{sp}: observed {counts[(ds,sp)]}, paper allocation {n}')
 for sp,n in {'train':77,'validation':24,'calibration':35,'test':29}.items():
  if totals[sp]!=n:error('TOTAL_MISMATCH',f'{sp}: {totals[sp]} vs {n}')
 if len(units)!=165:error('GRAND_TOTAL',f'Expected 165 dataset reporting units, found {len(units)}')
 pidx={r.get('parent_event_uid'):r for r in parents}
 uidx={r.get('reporting_unit_id'):r for r in units}
 pair_idx={r.get('reporting_unit_id'):r for r in pairs}
 byparent=collections.defaultdict(list);bygroup=collections.defaultdict(list)
 for r in units:
  uid=r.get('reporting_unit_id','');pid=r.get('parent_event_uid','');sp=r.get('split','')
  byparent[pid].append(r)
  if pid not in pidx:error('UNMATCHED_PARENT',f'{uid} references unknown physical parent',uid)
  if uid not in pair_idx:error('MISSING_PAIR',f'{uid} missing from original_and_repaired_pairs',uid)
  else:
   pp=pair_idx[uid]
   for a,b in [('parent_event_uid','parent_event_uid'),('dataset','dataset'),('split','split'),('sar_product_id','sar_product_id'),('sar_acquired_utc','sar_utc'),('optical_original_product_id','original_optical_product_id'),('optical_original_acquired_utc','original_optical_utc'),('optical_used_product_id','used_optical_product_id'),('optical_used_acquired_utc','used_optical_utc')]:
    if normal(r.get(a))!=normal(pp.get(b)):error('PAIR_MISMATCH',f'{uid}: reporting_units.{a} != pairing.{b}',uid)
   if parse_bool(r.get('optical_replaced'))!=parse_bool(pp.get('replaced')):error('REPLACEMENT_FLAG_MISMATCH',f'{uid}: replacement flag differs across tables',uid)
   try:
    med=float(pp.get('registration_median_px'));p95=float(pp.get('registration_p95_px'))
    if med<0 or p95<med:error('BAD_REGISTRATION_DIAGNOSTIC',f'{uid}: invalid median/P95 registration displacement',uid)
    if med>0.5 or p95>1.0:warn('REGISTRATION_QC_REVIEW',f'{uid}: median/P95 exceed manuscript acceptance guideline 0.5/1.0 px',uid)
   except (ValueError,TypeError):error('REGISTRATION_MISSING',f'{uid}: missing numeric registration diagnostics',uid)
   if mode=='submission' and parse_bool(pp.get('replaced')):
    for z in ('original_mask_sha256','used_mask_sha256'):
     if not good_sha(pp.get(z)):error('PAIR_MASK_HASH_MISSING',f'{uid}: {z} missing for replaced scene',uid)
    if is_missing(pp.get('approval_record')) or synthetic(pp.get('approval_record')):
     error('PAIR_APPROVAL_MISSING',f'{uid}: independent re-pairing approval record missing',uid)
  if r.get('duplicate_group_id'):bygroup[r['duplicate_group_id']].append(r)
  dates=[parse_date(r.get(z)) for z in ('sar_acquired_utc','optical_original_acquired_utc','optical_used_acquired_utc')]
  if any(v is None for v in dates):error('INVALID_DATE',f'{uid}: missing/invalid UTC ISO timestamps',uid)
  else:
   day=(dates[0]-dates[2]).total_seconds()/86400
   if day<=0: error('OPTICAL_NOT_PRE_EVENT',f'{uid}: used optical observation is not pre-SAR',uid)
   elif parse_bool(r.get('optical_replaced')) and not(3<=day<=60):warn('OPTICAL_WINDOW_REVIEW',f'{uid}: replacement optical-SAR interval {day:.2f} days outside preferred 3-60',uid)
  b=geo_bbox(r,mode)
  if b is None:error('INVALID_FOOTPRINT',f'{uid}: invalid bbox or CRS. Submission requires real EPSG:4326 bounding box',uid)
  if mode=='submission':
   for f in ['original_event_id','study_region','sar_product_id','optical_original_product_id','optical_used_product_id','original_optical_native_bands','used_optical_native_bands','sar_native_polarizations','optical_input_mapping','sar_input_mapping','incidence_angle_source','label_reference_id','source_record_uri']:
    if is_missing(r.get(f)) or synthetic(r.get(f)):error('MISSING_PROVENANCE',f'{uid}: invalid source field {f}',uid)
   for f in ['footprint_sha256','valid_mask_sha256']:
    if not good_sha(r.get(f)):error('MISSING_HASH',f'{uid}: missing/invalid {f}',uid)
   if is_missing(r.get('valid_mask_path')) or synthetic(r.get('valid_mask_path')):error('MISSING_MASK',f'{uid}: valid_mask_path missing',uid)
  try:
   vf=float(r.get('optical_valid_fraction','0'))
   if not(0<=vf<=1):error('INVALID_VALID_FRACTION',f'{uid}: valid fraction outside 0..1',uid)
   if parse_bool(r.get('optical_replaced')) and vf<0.85:
    warn('LOW_VALID_OPTICAL',f'{uid}: replacement has <85% optical valid coverage',uid)
  except Exception:error('INVALID_VALID_FRACTION',f'{uid}: invalid optical_valid_fraction',uid)
 for pid,group in byparent.items():
  if len(set(x['split'] for x in group))>1:error('PARENT_CROSSES_SPLITS',f'Physical parent {pid} spans multiple partitions',pid)
  parent=pidx.get(pid)
  if parent:
   if normal(parent.get('split'))!=group[0]['split']:error('PARENT_SPLIT_MISMATCH',f'Parent {pid} declared split mismatches children',pid)
   doc_ids={x.strip() for x in normal(parent.get('reporting_unit_ids')).split(';') if x.strip()}
   real_ids={x['reporting_unit_id'] for x in group}
   if doc_ids!=real_ids:error('PARENT_MEMBERSHIP_MISMATCH',f'Parent {pid} child IDs not matched',pid)
   doc_ds={x.strip() for x in normal(parent.get('datasets_in_group')).split(';') if x.strip()}
   real_ds={x['dataset'] for x in group}
   if doc_ds!=real_ds:error('PARENT_DATASET_MISMATCH',f'Parent {pid} grouped dataset identities differ',pid)
 for pid in pidx:
  if pid not in byparent:error('ORPHAN_PARENT',f'No reporting units reference parent {pid}',pid)
 for gid,rs in bygroup.items():
  if len({r['split'] for r in rs})>1:error('DUP_GROUP_CROSS_SPLIT',f'Duplicate group {gid} crosses partitions',gid)
 for field in ['sar_product_id','optical_used_product_id','optical_original_product_id','label_reference_id']:
  by=collections.defaultdict(list)
  for r in units:
   if normal(r.get(field)):by[r[field]].append(r)
  for val,rows in by.items():
   if len({r['split'] for r in rows})>1:error('SHARED_PRODUCT_CROSS_SPLIT',f'{field} reused across splits: {val}',val)
 # eligible event counts must be based on independent parents, not reporting-unit count
 for sp,flag,want in [('calibration','eligible_optical',32),('calibration','eligible_sar',34),('test','eligible_optical',24),('test','eligible_sar',26)]:
  matched={r['parent_event_uid'] for r in units if r.get('split')==sp and parse_bool(r.get(flag))}
  if len(matched)!=want:
   error('ELIGIBLE_PARENT_COUNT',f'{sp} {flag}: {len(matched)} independent parents vs reported {want}')
 if len(pairs)!=len(units):error('PAIR_ROWS',f'{len(pairs)} pair rows for {len(units)} units')
 replaced={r['reporting_unit_id']:r for r in units if parse_bool(r.get('optical_replaced'))}
 auditmap={r['reporting_unit_id']:r for r in labels}
 if len(replaced)!=12: error('REPLACEMENT_COUNT',f'12 optically replaced scenes reported; manifest has {len(replaced)}')
 for ds,want in [('CAU-Flood',7),('Sen2GF3Floods',5)]:
  actual=sum(x['dataset']==ds for x in replaced.values())
  if actual!=want:error('REPLACEMENT_DATASET_COUNT',f'{ds} replacements {actual} vs reported {want}')
 if len(labels)!=12:error('AUDIT_RECORDS',f'Expected 12 scene-level label-audit records, got {len(labels)}')
 for uid,ru in replaced.items():
  if uid not in auditmap:error('MISSING_AUDIT',f'Replaced scene {uid} missing label-audit record',uid)
  if ru.get('optical_used_product_id')==ru.get('optical_original_product_id'):error('REPLACEMENT_ID_EQUAL',f'{uid}: replacement product equals original',uid)
 for r in labels:
  uid=r.get('reporting_unit_id','')
  if uid not in replaced:error('AUDIT_NOT_REPLACED',f'Label audit refers to non-replaced scene {uid}',uid)
  if uid in uidx and r.get('parent_event_uid')!=uidx[uid].get('parent_event_uid'):error('AUDIT_PARENT_MISMATCH',f'{uid}: wrong parent_event_uid',uid)
  try:
   v,d,p,f,c,corr,excl=[int(r[z]) for z in ['valid_joint_px','initial_disagree_px','original_positive_label_px','flagged_positive_px','confirmed_inconsistent_px','corrected_px','excluded_px']]
   if not(0<=d<=v and 0<=f<=p<=v and 0<=c<=f and 0<=corr<=v and 0<=excl<=v):error('INVALID_LABEL_COUNTS',f'{uid}: invalid count hierarchy',uid)
  except Exception:error('INVALID_LABEL_COUNTS',f'{uid}: missing or noninteger audit counts',uid)
  if mode=='submission':
   for z in ['corrected_label_sha256','valid_mask_sha256']:
    if not good_sha(r.get(z)):error('AUDIT_HASH_MISSING',f'{uid}: missing {z}',uid)
   for z in ['corrected_label_path','valid_mask_path','decision_record_path','review_freeze_utc']:
    if is_missing(r.get(z)) or synthetic(r.get(z)):error('AUDIT_EVIDENCE_MISSING',f'{uid}: missing {z}',uid)
 totals_a={key:sum(int(r[key]) for r in labels if str(r.get(key,'')).isdigit()) for key in ['valid_joint_px','initial_disagree_px','original_positive_label_px','flagged_positive_px','confirmed_inconsistent_px','corrected_px','excluded_px']}
 if totals_a['valid_joint_px']:
  frac={
   'initial_disagreement_percent':100*totals_a['initial_disagree_px']/totals_a['valid_joint_px'],
   'flagged_of_original_positives_percent':100*totals_a['flagged_positive_px']/totals_a['original_positive_label_px'] if totals_a['original_positive_label_px'] else None,
   'confirmed_of_original_positives_percent':100*totals_a['confirmed_inconsistent_px']/totals_a['original_positive_label_px'] if totals_a['original_positive_label_px'] else None,
  }
  for key,want in [('initial_disagreement_percent',1.60),('flagged_of_original_positives_percent',0.24),('confirmed_of_original_positives_percent',0.07)]:
   val=frac.get(key)
   if val is None or abs(val-want)>0.0055:warn('PAPER_PERCENT_REVIEW',f'{key}: calculated {val} vs reported rounded {want}%')
 else:frac={}
 # Pairwise geo-time overlap and near-duplicate screening (screening = not proof of same event)
 # Use a sweep on x for efficient candidate pairs; report all unresolved cross-split candidates.
 exceptions={}
 expath=base/'reviewed_overlap_exceptions.csv'
 if expath.exists():
  for ex in read_csv(expath):
   ids=tuple(sorted([ex.get('reporting_unit_id_a',''),ex.get('reporting_unit_id_b','')]))
   exceptions[ids]=ex
 bufm=config.get('spatial_buffer_m',500)
 sorted_units=sorted([r for r in units if geo_bbox(r,mode)],key=lambda r:float(r['bbox_min_x']))
 for i,a in enumerate(sorted_units):
  ba=geo_bbox(a,mode)
  for b in sorted_units[i+1:]:
   if a['split']==b['split']:continue
   bb=geo_bbox(b,mode)
   if mode=='submission':
    lat=(ba[1]+ba[3]+bb[1]+bb[3])/4
    buffx=bufm/(111320*max(0.1,math.cos(math.radians(lat))));buff=bufm/110540
   else: buffx=buff=bufm
   if bb[0]>ba[2]+buffx:break
   if not intersect(ba,bb, max(buff,buffx)):continue
   sar_a=parse_date(a.get('sar_acquired_utc'));sar_b=parse_date(b.get('sar_acquired_utc'))
   if sar_a is None or sar_b is None:continue
   days=abs((sar_a-sar_b).total_seconds())/86400
   ids=tuple(sorted([a['reporting_unit_id'],b['reporting_unit_id']]))
   if days<=config.get('temporal_window_days',14):
    review=exceptions.get(ids,{})
    if (review.get('decision')=='verified_distinct' and normal(review.get('evidence_uri')) and normal(review.get('reviewer'))):
     warn('REVIEWED_GEO_TIME_OVERLAP',f'{ids}: reviewer-confirmed distinct event; manual evidence required',','.join(ids))
    else:
     error('UNRESOLVED_GEO_TIME_OVERLAP',f'{ids}: overlapping buffered footprints within {days:.1f} d. Requires review',','.join(ids))
   else:warn('SPATIAL_REVISIT_REVIEW',f'{ids}: same/near region across splits, but separated {days:.1f} d',','.join(ids))
   h1=normal(a.get('scene_phash64'));h2=normal(b.get('scene_phash64'))
   if re.fullmatch('[0-9a-fA-F]{16}',h1) and re.fullmatch('[0-9a-fA-F]{16}',h2):
    sim=1-(int(h1,16)^int(h2,16)).bit_count()/64
    if sim>=config.get('phash_similarity_warning',0.95):
     error('PHASH_NEAR_DUPLICATE',f'{ids}: spatially overlapping perceptual hash similarity {sim:.3f}',','.join(ids))
 result={'report_title':'CASI-Net P0 event provenance validation','mode':mode,'DATA_EVIDENCE_STATUS':'STRUCTURAL_CHECK_ONLY_NOT_EXTERNAL_SOURCE_AUTHENTICATION','summary':{'total_reporting_units':len(units),'total_parent_events':len(parents),'total_pair_records':len(pairs),'total_replacements':len(replaced),'total_label_audits':len(labels),'splits':dict(totals),'counts_by_dataset_split':{ds:{sp:counts[(ds,sp)] for sp in splits} for ds,splits in EXPECTED.items()},'label_audit_counts':totals_a,'label_audit_rates_percent':frac,'errors':len(problems),'warnings':len(warnings)},'errors':problems,'warnings':warnings,'informational':info}
 output.mkdir(parents=True,exist_ok=True)
 (output/'audit_report.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
 lines=['# CASI-Net P0 Provenance Audit',f'**Mode:** `{mode}`',f'**Evidence status:** `{result["DATA_EVIDENCE_STATUS"]}`','',f'- Reporting units: {len(units)}','- Physical parent events (manifest rows): '+str(len(parents)),f'- Optical replacements: {len(replaced)}',f'- Label-audited replacement scenes: {len(labels)}',f'- Errors: {len(problems)}',f'- Warnings: {len(warnings)}','','## Dataset allocation']
 for ds,dd in result['summary']['counts_by_dataset_split'].items():lines.append(f'- {ds}: train {dd["train"]}, validation {dd["validation"]}, calibration {dd["calibration"]}, test {dd["test"]}')
 lines += ['','## Audit totals',json.dumps(totals_a,ensure_ascii=False),'', '## Errors']
 if not problems:lines.append('- No structural errors found. This does NOT independently certify scientific authenticity.')
 for p in problems:lines.append(f'- **{p["code"]}**: {p["message"]}')
 lines+=['','## Warnings']
 if not warnings:lines.append('- None')
 for p in warnings[:150]:lines.append(f'- **{p["code"]}**: {p["message"]}')
 if len(warnings)>150:lines.append(f'- ... {len(warnings)-150} more in audit_report.json')
 lines+=['','## Interpretation','A PASS checks internal structure and basic duplication indicators only; it cannot prove that acquisitions, labels, identities, or HEC-RAS results are genuine. Independent source verification is still necessary.']
 (output/'audit_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps({'mode':mode,'errors':len(problems),'warnings':len(warnings),'report':str(output/'audit_report.md')},ensure_ascii=False))
 return not problems
if __name__=='__main__':
 p=argparse.ArgumentParser(description='Audit provenance manifests prior to public data release.')
 p.add_argument('--input',type=pathlib.Path,required=True);p.add_argument('--mode',choices=['submission'],default='submission');p.add_argument('--output',type=pathlib.Path,required=True)
 p.add_argument('--config',type=pathlib.Path,default=ROOT/'configs'/'screening_config.json');args=p.parse_args()
 cfg=json.loads(args.config.read_text(encoding='utf-8')) if args.config.exists() else {}
 ok=audit(args.input,args.mode,args.output,cfg);sys.exit(0 if ok else 2)
