"""Hydraulic-model reference evaluation from genuine site-level tables."""
from __future__ import annotations
from collections import defaultdict
import math
import numpy as np

CONFIGS=('point_only','independent_state_errors','shared_pixelwise_errors','full_casinet')
OUTPUTS=('stage_rise','inundation_depth')

def validate_sites(rows):
    """Ensure every comparison uses identical VALID sites, keyed by parent event + site."""
    groups=defaultdict(lambda:defaultdict(dict))
    for row in rows:
        out=row['output_type']; cfg=row['configuration']
        if out not in OUTPUTS or cfg not in CONFIGS:raise ValueError(f'unknown {out}/{cfg}')
        key=(row['parent_event_uid'],row['site_id'])
        if key in groups[out][cfg]:raise ValueError(f'duplicate site {out}/{cfg}/{key}')
        groups[out][cfg][key]=row
    for out,cfgs in groups.items():
        if set(cfgs)!=set(CONFIGS):raise ValueError(f'{out}: missing comparison configuration(s)')
        sets={k:{key for key,r in v.items() if r['valid']} for k,v in cfgs.items()}
        if len({frozenset(v) for v in sets.values()})!=1:
            raise ValueError(f'{out}: comparisons use different valid site sets')
        ref={}
        for cfg,entries in cfgs.items():
            for key in sets[cfg]:
                truth=float(entries[key]['reference_m'])
                if key in ref and abs(ref[key]-truth)>1e-9:
                    raise ValueError(f'reference mismatch {out}/{key}')
                ref[key]=truth
    return groups

def evaluate_hydraulic(rows):
    groups=validate_sites(rows)
    report={}
    for out,cfgs in groups.items():
        report[out]={}
        for cfg,entries in cfgs.items():
            usable=[r for r in entries.values() if r['valid']]
            if not usable:raise ValueError(f'{out}/{cfg}: zero valid sites')
            true=np.array([float(x['reference_m']) for x in usable])
            pred=np.array([float(x['pred_m']) for x in usable])
            residual=pred-true
            result={'n':len(usable),'mae_m':float(np.abs(residual).mean()),
                    'rmse_m':float(np.sqrt(np.mean(residual**2))),
                    'bias_m':float(residual.mean())}
            if cfg!='point_only':
                lower=np.array([float(x['lower90_m']) for x in usable]);upper=np.array([float(x['upper90_m']) for x in usable])
                if np.any(lower>upper):raise ValueError('inverted interval bounds')
                result['picp90_percent']=float(100*np.mean((lower<=true)&(true<=upper)))
                result['mpiw90_m']=float(np.mean(upper-lower))
            report[out][cfg]=result
    return report

# Bookkeeping from Supplement Table S11; values here are literature/manuscript claims,
# NOT substitutes for site-level reference observations.
REPORTED_VALID_COUNTS={'stage_rise':48,'inundation_depth':104,'candidate_depth':112,'gauges':18,'events':8}
