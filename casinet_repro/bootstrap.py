"""Paired event bootstrap and leave-one-event-out influence, with event as unit."""
from __future__ import annotations
from collections import defaultdict
import numpy as np

def paired_event_differences(rows, proposed='CASI-Net', baseline='CISRMamba', metric='f1'):
    # First average over seeds within each independently identified event.
    grouped=defaultdict(list)
    for r in rows:
        key=(r['dataset'],r['parent_event_uid'],r['method'])
        grouped[key].append(float(r[metric]))
    per={k:float(np.mean(v)) for k,v in grouped.items()}
    events=sorted({(d,e) for d,e,m in grouped})
    out={}
    for d,e in events:
        a=per.get((d,e,proposed)); b=per.get((d,e,baseline))
        if a is None or b is None: raise ValueError(f'missing paired method on {d}/{e}')
        out[(d,e)] = a-b
    return out

def bootstrap(differences, repeats=10_000, seed=2026, alpha=0.05):
    arr=np.asarray(list(differences.values()),dtype=float)
    if len(arr)<2: raise ValueError('at least two independent events required')
    if not np.isfinite(arr).all(): raise ValueError('nonfinite paired difference')
    rng=np.random.default_rng(seed)
    means=np.empty(repeats)
    for i in range(repeats): means[i]=np.mean(arr[rng.integers(0,len(arr),len(arr))])
    # Percentile bootstrap; unit for all draws is independent parent event.
    lo,hi=np.quantile(means,[alpha/2,1-alpha/2],method='linear')
    loo=[np.mean(np.delete(arr,j)) for j in range(len(arr))]
    return {'n_events':len(arr),'gain_mean':float(arr.mean()),'ci_low':float(lo),'ci_high':float(hi),
            'events_won':int(np.sum(arr>0)), 'loo_min':float(min(loo)), 'loo_max':float(max(loo)),
            'bootstrap_seed':seed, 'bootstrap_repeats':repeats}
