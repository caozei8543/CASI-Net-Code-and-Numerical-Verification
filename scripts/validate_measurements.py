#!/usr/bin/env python3
"""Reject missing/inconsistent research records before any public verification claim."""
import argparse,csv,collections,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
EXPECTED={'event_confusions.csv':['dataset','parent_event_uid','split','seed','method','tp','fp','tn','fn'],
          'ablation_per_event.csv':['dataset','parent_event_uid','seed','configuration','f1'],
          'contour_candidates.csv':['parent_event_uid','split','state','candidate_id','p_value','is_genuine','is_test_eligible'],
          'hecras_reference_sites.csv':['parent_event_uid','site_id','output_type','configuration','reference_m','pred_m','valid'],
          'hecras_models.csv':['parent_event_uid','model_archive_sha256','hecras_version'],
          'gauge_checks.csv':['parent_event_uid','gauge_id','observed_stage_m','simulated_stage_m','used_for_forcing','used_for_calibration']}
def read(path):
    with path.open(newline='',encoding='utf8') as f:
        reader=csv.DictReader(f)
        return reader.fieldnames,list(reader)
def main():
    p=argparse.ArgumentParser();p.add_argument('--input',default='data/measurements');p.add_argument('--output',default='outputs/input_validation.json');p.add_argument('--strict',action='store_true');a=p.parse_args()
    base=ROOT/a.input if not pathlib.Path(a.input).is_absolute() else pathlib.Path(a.input)
    checks=[];tables={}
    for name,required in EXPECTED.items():
        f=base/name
        if not f.exists():
            checks.append({'file':name,'status':'MISSING','reason':'no original records supplied'});continue
        try:cols,rows=read(f)
        except Exception as exc:checks.append({'file':name,'status':'ERROR','reason':str(exc)});continue
        tables[name]=rows
        missing=set(required)-set(cols or [])
        if missing:checks.append({'file':name,'status':'ERROR','reason':f'missing headers: {sorted(missing)}'})
        elif not rows:checks.append({'file':name,'status':'MISSING','reason':'header-only; no empirical rows'})
        else:checks.append({'file':name,'status':'PRESENT_UNAUTHENTICATED','rows':len(rows)})
    gauges=tables.get('gauge_checks.csv',[])
    if gauges and any(r.get(k,'').strip().lower() in ('true','1','yes') for r in gauges for k in ('used_for_forcing','used_for_calibration')):
        checks.append({'status':'ERROR','reason':'gauge consistency observations are marked as used for forcing/calibration; reconcile manuscript claim'})
    sites=tables.get('hecras_reference_sites.csv',[])
    if sites:
        expected={'stage_rise':48,'inundation_depth':104}
        for output,n in expected.items():
            rows=[r for r in sites if r.get('output_type')==output and r.get('configuration')=='full_casinet' and r.get('valid','').lower() in ('1','yes','true')]
            if len(rows)!=n:checks.append({'status':'ERROR','reason':f'{output} has {len(rows)} full-casinet valid references; manuscript reports {n}'})
    allok=all(x['status']=='PRESENT_UNAUTHENTICATED' for x in checks)
    result={'status':'STRUCTURE_PRESENT_UNAUTHENTICATED' if allok else 'NOT_READY_FOR_EMPIRICAL_VERIFICATION','checks':checks}
    out=ROOT/a.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2))
    if a.strict and not allok:sys.exit(2)
if __name__=='__main__':main()
