"""Event-level split conformal calibration of geometric null p-values.

The guarantee is marginal for uniformly sampled eligible genuine candidates
from exchangeable independent parent events, NOT per-pixel or per-class.
"""
from __future__ import annotations
import math, random
from collections import defaultdict


def mc_pvalue(null_statistics, observed):
    if len(null_statistics)==0: raise ValueError('need reference replicates')
    return (1 + sum(float(x) >= observed for x in null_statistics)) / (len(null_statistics)+1)

def select_event_candidates(rows, seed=2026):
    """Rows must already be restricted to a single sensor state and calibration partition."""
    groups=defaultdict(list)
    for r in rows:
        if r['split']!='calibration' or not r['is_genuine'] or not r['is_test_eligible']:
            continue
        if not 0 < float(r['p_value']) <= 1: raise ValueError('invalid p-value')
        groups[r['parent_event_uid']].append(r)
    rng=random.Random(seed)
    selected=[]
    for event_uid in sorted(groups):
        candidates=sorted(groups[event_uid],key=lambda x:str(x['candidate_id']))
        selected.append(candidates[rng.randrange(len(candidates))])
    return selected

def calibrate(selected, alpha=0.10):
    if not 0 < alpha < 1: raise ValueError('alpha must be in (0,1)')
    if len({r['parent_event_uid'] for r in selected}) != len(selected):
        raise ValueError('at most one candidate per independent parent event')
    p=[float(r['p_value']) for r in selected]
    if any(not 0 < x <= 1 for x in p): raise ValueError('invalid Monte Carlo p-values')
    n=len(p)
    if not n: raise ValueError('no calibration events')
    k=math.ceil((n+1)*(1-alpha))
    if k>n:
        return {'n':n,'k':k,'alpha':alpha,'nonconformity_threshold':math.inf,
                'reject_if_p_lt':0.0, 'selected_events':[r['parent_event_uid'] for r in selected]}
    threshold=sorted(-math.log(x) for x in p)[k-1]
    return {'n':n,'k':k,'alpha':alpha,'nonconformity_threshold':threshold,
            'reject_if_p_lt':math.exp(-threshold),
            'selected_events':[r['parent_event_uid'] for r in selected]}

def is_rejected(p_value, calibration):
    # Strict inequality means exact-threshold ties are not rejected.
    return -math.log(float(p_value)) > calibration['nonconformity_threshold']

def mean_event_frr(rows, calibration):
    """Evaluate among testable genuine candidates, event-averaged, not pixel-weighted."""
    grouped=defaultdict(list)
    for r in rows:
        if r['split']=='test' and r['is_genuine'] and r['is_test_eligible']:
            grouped[r['parent_event_uid']].append(is_rejected(r['p_value'],calibration))
    if not grouped: raise ValueError('no eligible genuine test candidates')
    return sum(sum(vals)/len(vals) for vals in grouped.values())/len(grouped)
