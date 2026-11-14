#!/usr/bin/env python3
"""Check arithmetic consistency of published aggregate reference tables.

This does not independently verify experiments and must not be described as raw-data replication.
"""
from pathlib import Path
import csv, json, math,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from casinet_repro.fusion import override_margin

def load(name):
    with (ROOT/'reference'/name).open(encoding='utf8',newline='') as f:return list(csv.DictReader(f))
def main():
    t3={r['configuration']:r for r in load('main_table_III_reported.csv')}
    ans={}
    for col,key in [('cau_f1_percent','CAU-Flood'),('sen2gf3_f1_percent','Sen2GF3Floods')]:
        full=float(t3['Full CASI-Net'][col]); no_c=float(t3['w/o contour-consistency test'][col]);no_s=float(t3['w/o source-constrained reachability'][col]);no_both=float(t3['w/o contour test and source-constrained reachability'][col])
        ans[key]=round(full-no_c-no_s+no_both,9)
    assert math.isclose(ans['CAU-Flood'],0.18,abs_tol=1e-8)
    assert math.isclose(ans['Sen2GF3Floods'],0.11,abs_tol=1e-8)
    s11=load('supp_table_S11_reported.csv')
    sums={k:sum(int(r[k]) for r in s11) for k in ('stage_sites','depth_candidate_sites','depth_valid_sites','gauge_observations')}
    assert list(sums.values()) == [48,112,104,18]
    result={'kind':'CONSISTENCY_OF_REPORTED_AGGREGATES_ONLY','two_factor_interaction_pp':ans,
            'hecras_site_counts':sums, 'fusion_override_margin_positive':override_margin()>0}
    out=ROOT/'reports'/'reported_arithmetic.json';out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
