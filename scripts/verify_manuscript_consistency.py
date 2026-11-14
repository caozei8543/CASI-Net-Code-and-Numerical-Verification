#!/usr/bin/env python3
"""Compare recomputed outputs against REPORTED manuscript targets only when real inputs exist.

This does not label a number verified merely because it appears in reference tables.
"""
import argparse,json,math,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--recomputed',default='outputs/recomputed.json');p.add_argument('--targets',default='reference/manuscript_claims.json');p.add_argument('--output',default='outputs/claim_comparison.json');a=p.parse_args()
    target=json.loads((ROOT/a.targets).read_text())
    path=ROOT/a.recomputed
    if not path.exists():
        print('NOT_VERIFIED: no recomputed experiment output exists');sys.exit(2)
    actual=json.loads(path.read_text());checks=[]
    if actual.get('status')=='INCOMPLETE':
        checks.append({'status':'NOT_VERIFIED','reason':'required raw inputs missing'})
    else:
        # Paired F1 claims are in percentage points; inputs are 0..1 fractions.
        paired=actual['analyses']['event_confusions.csv']['paired_F1']
        for ds,claimed in target['paired_f1_gain_percentage_points'].items():
            observed=paired.get(ds)
            if not observed or 'gain_mean' not in observed:
                checks.append({'dataset':ds,'status':'NOT_VERIFIED','reason':'missing dataset'});continue
            pp=observed['gain_mean']*100
            checks.append({'claim':f'{ds} paired F1 improvement (pp)', 'reported':claimed,'recomputed':pp,
                           'absolute_difference_pp':abs(pp-claimed),
                           'status':'MATCH_WITHIN_ROUNDING' if abs(pp-claimed)<=0.011 else 'DISCREPANCY'})
    out=ROOT/a.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'checks':checks},indent=2),encoding='utf8')
    print(f'Saved {out}; {len(checks)} checks')
    if any(v['status'] in ('DISCREPANCY','NOT_VERIFIED') for v in checks):sys.exit(2)
if __name__=='__main__':main()
