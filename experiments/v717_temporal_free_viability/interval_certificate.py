"""Conservative four-dimensional branch-and-bound over pre-detection motion states."""
import math
from types import SimpleNamespace
import numpy as np
SPEED=.12
ACCEL=.04
RADIUS=.10
FLOOR=.155
HORIZON=3.28

def maximum_displacement(time,velocity):
    t=np.asarray(time,float);v=np.asarray(velocity,float)
    switch=np.clip((SPEED-v)/ACCEL,0.,t)
    return v*switch+.5*ACCEL*switch**2+SPEED*(t-switch)

def minimum_displacement(time,velocity):return -maximum_displacement(time,-np.asarray(velocity,float))

def past_box(lo,hi,dt):
    return lo[:,:2]-maximum_displacement(dt,hi[:,2:]),hi[:,:2]-minimum_displacement(dt,lo[:,2:])

def future_boxes(lo,hi,times):
    t=np.asarray(times)[None,:,None]
    return lo[:,None,:2]+minimum_displacement(t,lo[:,None,2:]),hi[:,None,:2]+maximum_displacement(t,hi[:,None,2:])

def certify(poses,times,now,certificates,paired_clearance,limit=16384):
    poses=np.asarray(poses);times=np.asarray(times);assert len(poses)==329 and abs(times[-1]-HORIZON)<1e-12
    assert all(c.time<=now+1e-10 for c in certificates)
    c,s=np.cos(poses[:,2]),np.sin(poses[:,2]);extent=np.c_[abs(c)*.44+abs(s)*.375,abs(s)*.44+abs(c)*.375]
    margin=RADIUS+FLOOR+SPEED*HORIZON
    lower=np.r_[np.min(poses[:,:2]-extent,axis=0)-margin,[-SPEED,-SPEED]]
    upper=np.r_[np.max(poses[:,:2]+extent,axis=0)+margin,[SPEED,SPEED]]
    queue=[(0,lower,upper)];serial=1;processed=0;nodes=[];unsafe=[]
    field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2))
    while queue and processed<limit:
        size=min(256,len(queue),limit-processed);batch=queue[:size];queue=queue[size:]
        ids=[b[0]for b in batch];lo=np.array([b[1]for b in batch]);hi=np.array([b[2]for b in batch]);processed+=size
        fl,fh=future_boxes(lo,hi,times);centres=(fl+fh)/2;half=(fh-fl)/2
        ego=np.broadcast_to(poses,(size,*poses.shape)).reshape(-1,3)
        distances=paired_clearance(field,ego,centres.reshape(-1,2),half.reshape(-1,2)).reshape(size,-1)
        minimum=distances.min(axis=1);safe=minimum>=FLOOR
        reject=np.full(size,-1,int);reject_margin=np.full(size,np.nan)
        # Reverse chronology often rejects recent dangerous states first.
        for index in range(len(certificates)-1,-1,-1):
            pending=np.flatnonzero((reject<0)&~safe)
            if not len(pending):break
            cert=certificates[index];pl,ph=past_box(lo[pending],hi[pending],now-cert.time);mid=(pl+ph)/2
            bound=cert.point_lower(mid,np.full(len(mid),cert.time))-np.linalg.norm((ph-pl)/2,axis=1)
            invalid=bound>1e-8;chosen=pending[invalid];reject[chosen]=index;reject_margin[chosen]=bound[invalid]
        for j in range(size):
            row=dict(id=ids[j],lower=lo[j].tolist(),upper=hi[j].tolist(),future_minimum_clearance_lower_bound_m=float(minimum[j]))
            if safe[j]:row['classification']='SAFE_OVER_FULL_NATIVE_HORIZON'
            elif reject[j]>=0:row.update(classification='HISTORY_INCOMPATIBLE',history_index=int(reject[j]),historical_exclusion_lower_margin_m=float(reject_margin[j]))
            else:
                widths=(hi[j]-lo[j])*[1.,1.,HORIZON,HORIZON];axis=int(np.argmax(widths));mid=(hi[j,axis]+lo[j,axis])/2
                if widths[axis]<1e-5:
                    row['classification']='UNRESOLVED';unsafe.append(row)
                else:
                    a=hi[j].copy();a[axis]=mid;b=lo[j].copy();b[axis]=mid
                    row.update(classification='SPLIT',axis=axis,children=[serial,serial+1]);queue.extend([(serial,lo[j].copy(),a),(serial+1,b,hi[j].copy())]);serial+=2
            nodes.append(row)
    passed=not queue and not unsafe
    return dict(status='FULL_INTERVAL_CERTIFICATE'if passed else'INTERVAL_CERTIFICATE_UNRESOLVED',passed=passed,root_lower=lower.tolist(),root_upper=upper.tolist(),nodes=nodes,processed_nodes=processed,pending_nodes=len(queue),unresolved_leaf_count=len(unsafe),node_budget=limit,
                proof_scope='All current states in the root classified by conservative future bounds or past observation inconsistency; outside root cannot threaten this fixed finite pose trajectory.',new_integrations=0)
