"""Continuous rectangle union and per-cell necessary velocity contractions."""
import numpy as np
from empty_sample_contract import empty_points
from motion_tracker import capsule_constraints,ACCEL,SPEED,RADIUS,paired_rectangle_clearance
GRID=16

def build_cells(bounds,rays,rect,circ,now,frames):
    bounds=np.asarray(bounds,float);lo,hi=bounds[:2,0],bounds[:2,1]
    edges=[np.linspace(lo[i],hi[i],GRID+1)for i in range(2)]
    ids=np.stack(np.meshgrid(np.arange(GRID),np.arange(GRID),indexing='ij'),axis=-1).reshape(-1,2)
    lower=np.stack([edges[i][ids[:,i]]for i in range(2)],axis=1);upper=np.stack([edges[i][ids[:,i]+1]for i in range(2)],axis=1)
    impossible=np.zeros(len(ids),bool);points=empty_points(rays,bounds[:2]);A,b,_=capsule_constraints(np.asarray(rays,float).reshape(-1,7),rect,circ)
    for q in points:
        far=np.maximum(abs(lower-q),abs(upper-q));impossible|=(far*far).sum(axis=1)<(.10-1e-4)**2
    for n,c in zip(A,b):
        nearest=np.where(n>=0,lower,upper);impossible|=(nearest*n).sum(axis=1)>c+5e-7
    kept=(~impossible).reshape(GRID,GRID);merged=[]
    # Runs partition the retained continuous cells without convexifying holes.
    for i,row in enumerate(kept):
        j=0
        while j<GRID:
            if not row[j]:j+=1;continue
            start=j
            while j+1<GRID and row[j+1]:j+=1
            merged.append([edges[0][i],edges[1][start],edges[0][i+1],edges[1][j+1]]);j+=1
    assert merged,'UNION_OUTER_SET_EMPTY'
    cells=[]
    for x0,y0,x1,y1 in merged:
        pl=np.asarray([x0,y0])-5e-7;pu=np.asarray([x1,y1])+5e-7;vl=bounds[2:,0].copy();vu=bounds[2:,1].copy()
        for t,old in frames:
            dt=now-t
            if dt<=1e-7:continue
            vl=np.maximum(vl,(pl-old[:2,1])/dt-.5*ACCEL*dt);vu=np.minimum(vu,(pu-old[:2,0])/dt+.5*ACCEL*dt)
        if np.any(vl>vu):continue
        cells.append([pl.tolist(),pu.tolist(),vl.tolist(),vu.tolist()])
    assert cells,'UNION_VELOCITY_SET_EMPTY'
    return cells,{'grid_cells':GRID*GRID,'retained_grid_cells':int(kept.sum()),'cover_rectangles':len(cells),'empty_points':len(points),'scope':'continuous retained-cell cover; conditional bounded-noise and motion-class outer set'}

def future_cells(cells,times):
    cells=np.asarray(cells,float);t=np.asarray(times,float).reshape(-1,1,1);pl,pu,vl,vu=[cells[:,i,:][None,:,:]for i in range(4)]
    return np.maximum(pl+t*vl-.5*ACCEL*t*t,pl-SPEED*t),np.minimum(pu+t*vu+.5*ACCEL*t*t,pu+SPEED*t)

def clearance(field,poses,cells,times):
    poses=np.asarray(poses,float).reshape(-1,3);lo,hi=future_cells(cells,times);n,k,_=lo.shape
    result=paired_rectangle_clearance(field,np.repeat(poses,k,axis=0),((lo+hi)/2).reshape(-1,2),((hi-lo)/2).reshape(-1,2)).reshape(n,k).min(axis=1)
    return result
