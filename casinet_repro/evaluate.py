"""Single, explicit implementation of binary flood-change metrics."""
from __future__ import annotations
import numpy as np

METRICS = ('precision', 'recall', 'f1', 'iou_positive', 'iou_negative', 'miou', 'oa')

def confusion(y_true, y_pred, valid_mask=None) -> dict:
    y = np.asarray(y_true); p = np.asarray(y_pred)
    if y.shape != p.shape: raise ValueError('truth/prediction shape mismatch')
    if valid_mask is None: m = np.ones(y.shape, dtype=bool)
    else:
        m = np.asarray(valid_mask, dtype=bool)
        if m.shape != y.shape: raise ValueError('mask shape mismatch')
    y, p = y[m], p[m]
    if not len(y): raise ValueError('no valid pixels')
    if not np.all(np.isin(y, [0,1])) or not np.all(np.isin(p,[0,1])):
        raise ValueError('binary masks must contain only 0 and 1')
    return {'tp':int(np.sum((y==1)&(p==1))), 'fp':int(np.sum((y==0)&(p==1))),
            'tn':int(np.sum((y==0)&(p==0))), 'fn':int(np.sum((y==1)&(p==0)))}

def metrics_from_counts(tp:int, fp:int, tn:int, fn:int, absent_class='nan') -> dict:
    counts=(tp, fp, tn, fn)
    if any(int(v)!=v or v<0 for v in counts): raise ValueError('counts must be nonnegative integers')
    if sum(counts)==0: raise ValueError('no valid pixels')
    def div(n,d):
        return (np.nan if absent_class=='nan' else 0.0) if d==0 else n/d
    prec=div(tp,tp+fp); rec=div(tp,tp+fn)
    iou_p=div(tp,tp+fp+fn); iou_n=div(tn,tn+fp+fn)
    f1=div(2*tp,2*tp+fp+fn)
    return {'precision':prec,'recall':rec,'f1':f1,'iou_positive':iou_p,
            'iou_negative':iou_n, 'miou':(iou_p+iou_n)/2,
            'oa':(tp+tn)/sum(counts), 'n_valid':sum(counts)}

def per_event_metrics(rows, absent_class='nan'):
    """rows: iterable of dicts with tp,fp,tn,fn and grouping fields. No pooling across events."""
    out=[]
    for r in rows:
        m=metrics_from_counts(*(int(r[k]) for k in ('tp','fp','tn','fn')),absent_class)
        out.append({**r, **m})
    return out
