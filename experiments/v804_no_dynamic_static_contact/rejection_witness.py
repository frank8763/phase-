"""Rejection-only witness: no contract may be accepted from sampled poses."""
import numpy as np

EPSILON=1e-8
PROBES=(327,255,191,127,63,31,15,7,0)

def evaluate(field,poses,dt=.01):
    poses=np.asarray(poses,float).reshape(-1,3)
    assert len(poses)==328 and dt==.01
    checked=[]
    for indices in [(327,),PROBES[1:]]:
        ids=np.asarray(indices,dtype=int)
        values=field.causal_values_at_times(poses[ids],(ids+1)*dt)
        assert values.shape==(len(ids),)and np.isfinite(values).all()
        checked.extend(dict(native_tick=int(i+1),causal_value_m=float(v))for i,v in zip(ids,values))
        bad=np.flatnonzero(values<.155-EPSILON)
        if len(bad):
            j=int(bad[0]);return dict(rejected=True,full_values=None,
                witness_native_tick=int(ids[j]+1),witness_value_m=float(values[j]),
                checked_native_samples=checked,full_minimum_not_evaluated=True)
    # Acceptance and ranking require the unchanged original complete calculation.
    full=field.trajectory_values(poses,dt)
    return dict(rejected=bool(full.min()<.155),full_values=full,
        witness_native_tick=None,witness_value_m=None,checked_native_samples=checked,
        full_minimum_not_evaluated=False)
