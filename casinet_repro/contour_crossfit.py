"""Held-out contiguous shoreline-arc statistic from Eqs (14)-(15).

Input shoreline anchors MUST arrive sorted around the same contour; full-scene
candidates with several disconnected curves require independent arc handling.
"""
import numpy as np
from scipy.spatial import cKDTree
from scipy.special import huber

def crossfit_statistic(positions_xy_m, z, sigma, fit_predict, n_arcs=5,
                       exclusion_buffer_m=300.0, trim_fraction=0.10,
                       min_fit_anchors=30,huber_delta=1.345):
    pos=np.asarray(positions_xy_m,dtype=float);y=np.asarray(z,dtype=float);sig=np.asarray(sigma,dtype=float)
    if pos.ndim!=2 or pos.shape[1]!=2 or len(pos)!=len(y) or len(y)!=len(sig):raise ValueError('invalid anchor arrays')
    if (sig<=0).any():raise ValueError('positive errors required')
    if n_arcs<2 or len(y)<n_arcs:raise ValueError('not enough anchors for arcs')
    if not (0<=trim_fraction<1):raise ValueError('invalid trimmed fraction')
    values=[];arc_indices=np.array_split(np.arange(len(y)),n_arcs)
    for arc in arc_indices:
        near=cKDTree(pos[arc]).query(pos,k=1)[0] <= exclusion_buffer_m
        train=np.where(~near)[0]
        if len(train)<min_fit_anchors:raise ValueError('INCONCLUSIVE: insufficient retained anchors')
        predictions=np.asarray(fit_predict(train,arc),dtype=float)
        if predictions.shape != (len(arc),):raise ValueError('fit_predict must return one value per held-out anchor')
        r=(y[arc]-predictions)/sig[arc]
        values.extend(huber(huber_delta,r))
    vals=np.sort(np.asarray(values))
    retain=max(1,int(np.floor((1-trim_fraction)*len(vals))))
    return float(vals[:retain].mean())
