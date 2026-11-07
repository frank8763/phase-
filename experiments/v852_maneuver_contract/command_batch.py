"""Exact batch construction/deduplication of existing canonical controls.

Only CPU array arithmetic, no model or physics; full native prediction and all
safety tests must follow. This is not a GPU/native throughput qualification.
"""
import numpy as np


def sequences(targets,last,lower,upper,rate,horizon=240,brake_after=80):
    targets=np.asarray(targets,float);last=np.asarray(last,float);lower=np.asarray(lower,float);upper=np.asarray(upper,float);rate=np.asarray(rate,float)
    assert targets.ndim==2 and targets.shape[1]==4 and len(targets)>0 and np.isfinite(targets).all()
    assert all(x.shape==(4,)and np.isfinite(x).all()for x in [last,lower,upper,rate])
    assert np.all(lower<upper)and np.all(rate>0)and np.all(last>=lower)and np.all(last<=upper)
    assert type(horizon)is int and horizon>0 and horizon%8==0
    assert brake_after is None or(type(brake_after)is int and 0<=brake_after<=horizon and brake_after%8==0)
    commands=np.repeat(last[None],len(targets),axis=0);rows=[]
    for tick in range(0,horizon,8):
        active=targets.copy()
        if brake_after is not None and tick>=brake_after:active[:,2:]=0.
        commands=np.clip(np.clip(active,lower,upper),commands-rate,commands+rate)
        rows.append(np.repeat(commands[:,None,:],8,axis=1))
    return np.concatenate(rows,axis=1)


def deduplicate_full_sequences(controls):
    controls=np.asarray(controls,float)
    assert controls.ndim==3 and controls.shape[2]==4 and np.isfinite(controls).all()
    seen={};unique=[];inverse=[];first=[]
    for i,row in enumerate(controls):
        key=np.ascontiguousarray(row).tobytes()
        if key not in seen:seen[key]=len(unique);unique.append(row.copy());first.append(i)
        inverse.append(seen[key])
    unique=np.asarray(unique);inverse=np.asarray(inverse,int)
    assert np.array_equal(unique[inverse],controls)
    return unique,inverse,np.asarray(first,int)
