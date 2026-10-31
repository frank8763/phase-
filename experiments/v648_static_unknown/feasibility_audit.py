"""Evaluation-only necessary-condition audit. Never imported by a controller."""
import json,math
from collections import deque
from pathlib import Path
import numpy as np

def audit(protocol,resolution=.025):
    lo,hi=-5.,5.;axis=np.arange(lo,hi+resolution/2,resolution)
    xx,yy=np.meshgrid(axis,axis,indexing='ij');p=np.column_stack((xx.ravel(),yy.ravel()))
    bounds=np.asarray(protocol['footprint_bounds']);inner=float(min(-bounds[0],-bounds[1],bounds[2],bounds[3]))
    clearance=np.minimum(p.min(axis=1)-lo,hi-p.max(axis=1))-inner
    for x,y,hx,hy in protocol['known_rectangles']:
        clearance=np.minimum(clearance,np.linalg.norm(np.maximum(np.abs(p-[x,y])-[hx,hy],0),axis=1)-inner)
    if 'physical_unknown_obstacles'not in protocol:
        return {'status':'UNKNOWN_OBSTACLE_INVENTORY_INCOMPLETE','reason':'legacy protocol omitted unknown9; no feasibility conclusion valid without complete physical inventory'}
    circles=list(protocol['known_circles'])+[[*u['xy'],u['radius']]for u in protocol['physical_unknown_obstacles']]
    for x,y,r in circles:clearance=np.minimum(clearance,np.linalg.norm(p-[x,y],axis=1)-r-inner)
    # Optimistic cells: an entire cell is rejected only when its maximum possible Lipschitz clearance is below the floor.
    free=(clearance>=.15-resolution/math.sqrt(2)).reshape(xx.shape)
    start=np.rint((np.asarray(protocol['start_qpos'][:2])-lo)/resolution).astype(int)
    if not free[tuple(start)]:return {'optimistic_disk_connected':False,'reason':'initial_inscribed_disk_not_clear','inscribed_radius_m':inner}
    seen=np.zeros_like(free,dtype=bool);seen[tuple(start)]=True;q=deque([tuple(start)])
    while q:
        x,y=q.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            a,b=x+dx,y+dy
            if 0<=a<len(axis) and 0<=b<len(axis) and free[a,b] and not seen[a,b]:seen[a,b]=True;q.append((a,b))
    goals=(np.linalg.norm(p-np.asarray(protocol['goal_xy']),axis=1)<=.45+resolution/math.sqrt(2)).reshape(free.shape)
    return {'optimistic_disk_connected':bool(np.any(seen&goals)),'inscribed_radius_m':inner,'resolution_m':resolution,'hard_floor_m':.15,'visited_cells':int(seen.sum()),'scope':'evaluation-only necessary condition; positive connectivity does not certify SE2/dynamic feasibility','uses_hidden_geometry':True,'controller_input':False}

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('protocol');args=parser.parse_args()
    protocol=Path(args.protocol);result=audit(json.loads(protocol.read_text()));print(json.dumps(result,indent=2))
    protocol.with_name('EVALUATION_FEASIBILITY.json').write_text(json.dumps(result,indent=2))
