#!/usr/bin/env python3
"""Calibrate conformal thresholds from event-level candidate records; no trial p-values included."""
import csv, argparse, json, pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from casinet_repro.contour_calibration import select_event_candidates,calibrate,mean_event_frr

def boolean(x):return str(x).strip().lower() in ('true','1','yes')
def main():
    p=argparse.ArgumentParser();p.add_argument('--input',default='data/measurements/contour_candidates.csv');p.add_argument('--output',default='outputs/conformal_recomputed.json');p.add_argument('--alpha',type=float,default=.10);p.add_argument('--seed',type=int,default=2026)
    a=p.parse_args()
    with open(a.input,encoding='utf8',newline='') as f:rows=list(csv.DictReader(f))
    for r in rows:
        for b in ('is_genuine','is_false','is_test_eligible','rejected'):r[b]=boolean(r[b])
        r['p_value']=float(r['p_value'])
    res={}
    for state in ('optical','sar'):
        state_rows=[r for r in rows if r['state']==state]
        chosen=select_event_candidates(state_rows,a.seed)
        result=calibrate(chosen,a.alpha)
        result['test_event_frr']=mean_event_frr(state_rows,result) if any(r['split']=='test' and r['is_genuine'] and r['is_test_eligible'] for r in state_rows) else None
        res[state]=result
    out=pathlib.Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(res,indent=2),encoding='utf8');print(f'Saved {out}')
if __name__=='__main__':main()
