"""Four-cell paired event interaction: full - no_contour - no_source + no_both."""
from collections import defaultdict
import numpy as np
from .bootstrap import bootstrap
REQUIRED=('full_casinet','no_contour','no_source','no_both')

def interaction_by_event(rows):
    grouped=defaultdict(lambda:defaultdict(list))
    for r in rows:
        key=(r['dataset'],r['parent_event_uid'])
        grouped[key][r['configuration']].append(float(r['f1']))
    out={}
    for k,v in grouped.items():
        if not all(s in v for s in REQUIRED):
            raise ValueError(f'incomplete 2x2 cells on event {k}')
        p={c:float(np.mean(v[c])) for c in REQUIRED}
        out[k]=p['full_casinet']-p['no_contour']-p['no_source']+p['no_both']
    return out

def summary_by_dataset(rows, repeats=10000, seed=2026):
    diffs=interaction_by_event(rows);results={}
    for ds in sorted({a for a,b in diffs}):
        subset={k:v for k,v in diffs.items() if k[0]==ds}
        results[ds]=bootstrap(subset,repeats,seed) if len(subset)>1 else {'interaction':next(iter(subset.values()))}
    return results
