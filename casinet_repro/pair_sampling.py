"""Spatially correlated DEM-error draws with one SHARED field per paired state.

C(x,x') = sigma(x)sigma(x')exp(-||x-x'||/L) + nugget^2 I.
Uses validated circulant embedding; signals an error rather than quietly using an
invalid embedding. Arrays are in metres and shape (H,W).
"""
from __future__ import annotations
import numpy as np
from scipy.fft import rfft2, irfft2

def _embed_spectrum(h,w,resolution_m,correlation_m,max_doublings=4):
    if resolution_m<=0 or correlation_m<=0: raise ValueError('positive distances required')
    for d in range(max_doublings+1):
        H,W=(2**(d+1)*h),(2**(d+1)*w)
        y=np.minimum(np.arange(H),H-np.arange(H))*resolution_m
        x=np.minimum(np.arange(W),W-np.arange(W))*resolution_m
        dist=np.hypot(y[:,None],x[None,:])
        kernel=np.exp(-dist/correlation_m)
        spec=rfft2(kernel).real
        mn=spec.min()
        if mn >= -1e-9*max(1.0,spec.max()):
            return np.maximum(spec,0),H,W
    raise ValueError('Covariance embedding not positive semidefinite; enlarge support or use a PSD reference solver')

def spatial_dem_errors(sigma_map, n, resolution_m=10.0, correlation_m=250.0,
                       nugget_m=0.35, seed=2026):
    sig=np.asarray(sigma_map,dtype=float)
    if sig.ndim!=2 or (sig<0).any() or not np.isfinite(sig).all():raise ValueError('invalid sigma map')
    if n<1 or nugget_m<0:raise ValueError('invalid draw count/nugget')
    h,w=sig.shape
    eig,H,W=_embed_spectrum(h,w,resolution_m,correlation_m)
    rng=np.random.default_rng(seed)
    out=np.empty((n,h,w),dtype=float)
    for i in range(n):
        white=rng.normal(size=(H,W))
        correlated=irfft2(rfft2(white)*np.sqrt(eig),s=(H,W)).real[:h,:w]
        out[i]=correlated*sig + rng.normal(scale=nugget_m,size=(h,w))
    return out

def paired_terrain_and_anchors(z_obs, anchors_z, anchor_ij, sigmap, n=200, seed=2026,
                               sigma_loc=None, sigma_repr=None, **kwargs):
    """Shared DEM error at identical grid coordinates; state-specific independent anchor errors.

    anchors_z: dict[state] of original anchor Z measurements; anchor_ij dict[state]
    of (N,2) row/column integer indices; state in {'optical','sar'}.
    Return (perturbed DEM realizations, per-state perturbed anchor realizations).
    """
    z=np.asarray(z_obs,dtype=float)
    if z.shape != np.asarray(sigmap).shape:raise ValueError('DEM/sigma shapes disagree')
    field=spatial_dem_errors(sigmap,n,seed=seed,**kwargs)
    rng=np.random.default_rng(seed+1)
    anchors={}
    for state in ('optical','sar'):
        coords=np.asarray(anchor_ij[state],dtype=int)
        orig=np.asarray(anchors_z[state],dtype=float)
        if coords.shape!=(len(orig),2):raise ValueError('invalid anchor coordinates')
        if np.any(coords[:,0]<0) or np.any(coords[:,0]>=z.shape[0]) or np.any(coords[:,1]<0) or np.any(coords[:,1]>=z.shape[1]):
            raise ValueError('anchor indices outside DEM')
        ls=0 if sigma_loc is None else sigma_loc.get(state,0)
        rs=0 if sigma_repr is None else sigma_repr.get(state,0)
        anchors[state]=orig[None,:]-field[:,coords[:,0],coords[:,1]]-rng.normal(scale=ls,size=(n,len(orig)))-rng.normal(scale=rs,size=(n,len(orig)))
    return z[None,:,:]-field,anchors
