"""Eight-connected minimax hydraulic deficit; diagonal corner connections are allowed.

For each source-to-pixel path P, Δ(x)=min_P max_{y in P} cost(y).
On observed pre-event water, cost(y)=-inf for BOTH water states.
"""
import heapq
import numpy as np

def minimax_deficit(source_mask, terrain_minus_surface, domain=None, prewater_mask=None):
    cost=np.asarray(terrain_minus_surface,dtype=float).copy()
    if cost.ndim!=2: raise ValueError('2-D only')
    shape=cost.shape
    src=np.asarray(source_mask,dtype=bool)
    if src.shape!=shape: raise ValueError('source/domain shape mismatch')
    valid=np.ones(shape,dtype=bool) if domain is None else np.asarray(domain,dtype=bool)
    if valid.shape!=shape: raise ValueError('domain shape mismatch')
    if prewater_mask is not None:
        pre=np.asarray(prewater_mask,dtype=bool)
        if pre.shape!=shape: raise ValueError('prewater shape mismatch')
        cost[pre & valid]=-np.inf
    if np.any(np.isnan(cost[valid])): raise ValueError('NaN cost on valid support')
    result=np.full(shape,np.inf); heap=[]
    for i,j in np.argwhere(src&valid):
        i=int(i); j=int(j); result[i,j]=-np.inf; heapq.heappush(heap,(-np.inf,i,j))
    h,w=shape
    while heap:
        val,i,j=heapq.heappop(heap)
        if val!=result[i,j]: continue
        for di in (-1,0,1):
            for dj in (-1,0,1):
                if not (di or dj): continue
                ii,jj=i+di,j+dj
                if not(0<=ii<h and 0<=jj<w) or not valid[ii,jj]: continue
                t=max(val,cost[ii,jj])
                if t<result[ii,jj]:
                    result[ii,jj]=t; heapq.heappush(heap,(t,ii,jj))
    return result

def paired_change_frequency(z_fields, normal_surfaces, flood_surfaces,
                            source_mask, domain=None, prewater_mask=None):
    z=np.asarray(z_fields); w0=np.asarray(normal_surfaces); w1=np.asarray(flood_surfaces)
    if z.shape!=w0.shape or z.shape!=w1.shape or z.ndim!=3:
        raise ValueError('paired arrays must have shape (realizations, height, width)')
    if np.any(w1 < w0 - 1e-8): raise ValueError('A5 nesting violated in fitted surfaces')
    r0=[];r1=[]
    for n in range(z.shape[0]):
        d0=minimax_deficit(source_mask,z[n]-w0[n],domain,prewater_mask)
        d1=minimax_deficit(source_mask,z[n]-w1[n],domain,prewater_mask)
        r0.append(d0<=0);r1.append(d1<=0)
    r0=np.asarray(r0);r1=np.asarray(r1)
    if np.any(r0 & ~r1): raise AssertionError('paired reachable states not nested')
    change=np.mean(r1 & ~r0,axis=0)
    diff=r1.mean(axis=0)-r0.mean(axis=0)
    if not np.allclose(change,diff,rtol=0,atol=1e-12):raise AssertionError('pair frequency identity failed')
    return {'p0_reach':r0.mean(axis=0),'p1_reach':r1.mean(axis=0),'p_change':change}
