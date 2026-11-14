"""Candidate extraction, simple 4-edge shoreline anchors, persistent source cores.

Reference code for Eqs (5)–(7); DEM sampling/validity masks must match the
original image preprocessing and analysis-grid conventions.
"""
import numpy as np
from scipy.ndimage import label

def candidates(p_water, tau=0.50, min_pixels=25, valid=None):
    p=np.asarray(p_water,dtype=float)
    v=np.ones(p.shape,dtype=bool) if valid is None else np.asarray(valid,dtype=bool)
    if p.shape!=v.shape or p.ndim!=2:raise ValueError('invalid shapes')
    labels,n=label((p>=tau)&v,structure=np.ones((3,3),dtype=bool))
    counts=np.bincount(labels.ravel());kept=[]
    for idx in range(1,n+1):
        if counts[idx]>=min_pixels:kept.append({'candidate_id':idx,'mask':labels==idx,'area_pixels':int(counts[idx])})
    return kept

def anchors(candidate_mask,p_water,dem,valid=None):
    """Half-sum elevation and adjacent image contrast for 4-neighbor boundary pairs."""
    m=np.asarray(candidate_mask,dtype=bool);p=np.asarray(p_water,dtype=float);z=np.asarray(dem,dtype=float)
    if not(m.shape==p.shape==z.shape):raise ValueError('shape mismatch')
    v=np.ones(m.shape,dtype=bool) if valid is None else np.asarray(valid,dtype=bool)
    pts=[]
    for di,dj in ((1,0),(0,1)):
        # Slice along one axis to avoid diagonal candidate boundaries.
        sl1=(slice(0,-1),slice(None)) if di==1 else (slice(None),slice(0,-1))
        sl2=(slice(1,None),slice(None)) if di==1 else (slice(None),slice(1,None))
        edge=(m[sl1]!=m[sl2])&v[sl1]&v[sl2]&np.isfinite(z[sl1])&np.isfinite(z[sl2])
        for i,j in np.argwhere(edge):
            ii,jj=(i+1,j) if di else (i,j+1)
            pts.append(((i+ii)/2,(j+jj)/2,float((z[i,j]+z[ii,jj])/2),float(abs(p[i,j]-p[ii,jj]))))
    return np.array(pts,dtype=float).reshape(-1,4)

def source_core(candidate_mask, pre_prob, post_prob, reference_network_mask,
                threshold=0.80, min_size=8):
    m=np.asarray(candidate_mask,dtype=bool);a=np.asarray(pre_prob);b=np.asarray(post_prob)
    n=np.asarray(reference_network_mask,dtype=bool)
    if not(m.shape==a.shape==b.shape==n.shape):raise ValueError('shape mismatch')
    src=m&n&(a>=threshold)&(b>=threshold)
    return src if src.sum()>=min_size else np.zeros_like(src)
