"""Convex IRLS / ADMM reference solver for Eq. (9), optionally the monotone W1 >= W0 bound.

This is a transparent numerical reference for small-to-medium CONTROL grids,
not a claimed bitwise reproduction of an unpublished GPU production backend.
Requires assembled sparse interpolation matrix A and edge graph B; physical units
and the graph's edge lengths are caller inputs. Assert convergence before use.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

@dataclass
class SolveInfo:
    irls_iterations:int
    admm_iterations:int
    primal_residual:float
    dual_residual:float
    edge_violation_m:float
    stage_violation_m:float
    converged:bool

def grid_edges(n_rows, n_cols, grid_m=90.0):
    if min(n_rows,n_cols)<1 or grid_m<=0:raise ValueError('invalid grid')
    ix=[];jx=[];data=[];r=0
    for i in range(n_rows):
        for j in range(n_cols):
            at=i*n_cols+j
            for di,dj in ((1,0),(0,1)):
                ni,nj=i+di,j+dj
                if ni<n_rows and nj<n_cols:
                    ix.extend([r,r]); jx.extend([at,ni*n_cols+nj]);data.extend([1.0,-1.0]);r+=1
    B=sparse.csr_matrix((data,(ix,jx)),shape=(r,n_rows*n_cols))
    return B,np.full(r,grid_m)

def solve_surface(A,z,sigma,q,B,edge_lengths, gradient_max=0.003,
                  laplacian_weight=0.010,huber_delta=1.345,
                  admm_rho=1.0,irls_max=25,admm_max=500,
                  tol=1e-4,feasibility_tol=1e-6,normal_lower=None,require_convergence=True):
    A=sparse.csr_matrix(A); B=sparse.csr_matrix(B)
    z=np.asarray(z,dtype=float).ravel();sigma=np.asarray(sigma,dtype=float).ravel()
    q=np.asarray(q,dtype=float).ravel(); length=np.asarray(edge_lengths,dtype=float).ravel()
    m,n=A.shape
    if not (len(z)==len(sigma)==len(q)==m and B.shape[1]==n and len(length)==B.shape[0]):
        raise ValueError('incompatible operator/anchor dimensions')
    if m==0 or (sigma<=0).any() or (q<0).any() or not np.isfinite(z).all():raise ValueError('invalid anchor measurements')
    if (length<=0).any() or gradient_max<0:raise ValueError('invalid gradient')
    if laplacian_weight<0 or admm_rho<=0:raise ValueError('invalid penalty')
    lower=None if normal_lower is None else np.asarray(normal_lower,dtype=float).ravel()
    if lower is not None and len(lower)!=n:raise ValueError('normal-state lower bound shape mismatch')
    # Translate all terms by constant without affecting the solution numerically.
    datum=float(np.median(z)); z0=z-datum
    low0=lower-datum if lower is not None else None
    w=np.full(n,float(np.median(z0))) if low0 is None else np.maximum(np.full(n,np.median(z0)),low0)
    limit=gradient_max*length
    E=B.T@B
    smooth=laplacian_weight*E
    last_info=None
    outer_converged=False
    for it in range(1,irls_max+1):
        resid=A@w-z0
        weights=q/sigma**2*np.minimum(1.0,huber_delta*sigma/np.maximum(np.abs(resid),1e-12))
        D=sparse.diags(weights)
        K=A.T@D@A+smooth+admm_rho*E
        if low0 is not None: K=K+admm_rho*sparse.eye(n)
        # Some isolated control nodes have no anchor/edges; no unique solution there.
        lu=splu(K.tocsc())
        base=A.T@(weights*z0)
        bw=B@w; d=np.clip(bw,-limit,limit);u=np.zeros(B.shape[0])
        if low0 is not None: v=np.maximum(w,low0); u2=np.zeros(n)
        converged=False
        for j in range(1,admm_max+1):
            rhs=base+admm_rho*(B.T@(d-u))
            if low0 is not None: rhs+=admm_rho*(v-u2)
            w=lu.solve(rhs)
            bw=B@w
            d0=d.copy();d=np.clip(bw+u,-limit,limit)
            u+=bw-d
            p1=np.linalg.norm(bw-d)
            s1=admm_rho*np.linalg.norm(B.T@(d-d0))
            if low0 is not None:
                v0=v.copy();v=np.maximum(w+u2,low0);u2+=w-v
                p1=np.hypot(p1,np.linalg.norm(w-v))
                s1=np.hypot(s1,admm_rho*np.linalg.norm(v-v0))
            if p1<=tol and s1<=tol:
                converged=True;break
        edge_violation=float(np.max(np.maximum(np.abs(B@w)-limit,0))) if B.shape[0] else 0.0
        stage_violation=0.0 if low0 is None else float(max(0,np.max(low0-w)))
        last_info=SolveInfo(it,j,float(p1),float(s1),edge_violation,stage_violation,converged)
        new_resid=A@w-z0
        new_weights=q/sigma**2*np.minimum(1.0,huber_delta*sigma/np.maximum(np.abs(new_resid),1e-12))
        if converged and np.max(np.abs(new_weights-weights)) < 1e-5:
            outer_converged=True; break
    last_info.converged=bool(outer_converged and last_info.edge_violation_m<=feasibility_tol and last_info.stage_violation_m<=feasibility_tol)
    if require_convergence and not last_info.converged:
        raise RuntimeError(f'IRLS/ADMM not converged: {last_info}')
    return w+datum,last_info
