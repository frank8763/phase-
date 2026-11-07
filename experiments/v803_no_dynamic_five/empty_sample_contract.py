"""Outer interval contraction using only certified unhit ray-march samples.
No center/point hypotheses are removed from uncertainty unless the whole cell
is strictly inside one impossible-center disk. Ambiguous cells are retained.
"""
import numpy as np
RADIUS=.10
SLACK=1e-4
GRID=32

def empty_points(rays,bounds):
    lo,hi=np.asarray(bounds)[:,0],np.asarray(bounds)[:,1];points=[]
    for ray in np.asarray(rays,float).reshape(-1,7):
        ds=np.arange(0,3.000001,.08);ds=ds[ds<ray[4]-ray[5]-SLACK]
        origin=np.asarray(ray[:2],np.float32);direction=np.asarray(ray[2:4],np.float32)
        sampled=(origin[None,:]+ds.astype(np.float32)[:,None]*direction).astype(float)
        near=np.all(sampled>=lo-RADIUS,axis=1)&np.all(sampled<=hi+RADIUS,axis=1)
        points.extend(sampled[near])
    return np.unique(np.asarray(points).reshape(-1,2),axis=0)

def contract_box(bounds,rays):
    bounds=np.asarray(bounds,float);lo,hi=bounds[:,0],bounds[:,1]
    points=empty_points(rays,bounds)
    if not len(points):return bounds.copy(),{'empty_points':0,'removed_cells':0,'retained_cells':GRID*GRID,'area_before_m2':float(np.prod(hi-lo)),'area_after_m2':float(np.prod(hi-lo))}
    edges=[np.linspace(lo[i],hi[i],GRID+1)for i in range(2)]
    indices=np.stack(np.meshgrid(np.arange(GRID),np.arange(GRID),indexing='ij'),axis=-1).reshape(-1,2)
    lower=np.stack([edges[i][indices[:,i]]for i in range(2)],axis=1)
    upper=np.stack([edges[i][indices[:,i]+1]for i in range(2)],axis=1)
    impossible=np.zeros(len(indices),bool)
    for chunk in range(0,len(points),64):
        q=points[chunk:chunk+64]
        # Exact interval supremum distance to q over every closed cell.
        farthest=np.maximum(abs(lower[:,None,:]-q),abs(upper[:,None,:]-q))
        impossible|=np.any(np.sum(farthest*farthest,axis=-1)<(RADIUS-SLACK)**2,axis=1)
    assert not np.all(impossible),'EMPTY_SAMPLE_OUTER_SET_INCONSISTENT'
    result=np.stack([lower[~impossible].min(axis=0),upper[~impossible].max(axis=0)],axis=1)
    result[:,0]=np.maximum(lo,result[:,0]-5e-7);result[:,1]=np.minimum(hi,result[:,1]+5e-7)
    return result,{'empty_points':len(points),'removed_cells':int(impossible.sum()),'retained_cells':int((~impossible).sum()),'area_before_m2':float(np.prod(hi-lo)),'area_after_m2':float(np.prod(result[:,1]-result[:,0])),'cells_per_axis':GRID,'continuous_cells_retained':True,'maximal_interior_distance_slack_m':SLACK}
