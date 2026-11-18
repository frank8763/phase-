"""One scalar fit on fixed new data; no state propagation or model loading."""
from pathlib import Path
import sys
import fcntl
import time
import math

C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1159_bounded_steering_load'
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply()
sys.path.insert(0,str(R/'experiments/v1158_excited_steering_model'))
import data_tools as dt
np=dt.np;q=dt.old


def main():
    assert not(C/'PARAMETERS.json').exists()and not O.exists(),'ONE_SCALAR_FIT_ONLY'
    O.mkdir(parents=True);start=time.monotonic()
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert q.sha(R/'REVIEW_PENDING')==q.GUARD
    d=dt.response_data();idx=np.arange(2200,6400);state=d['states'];a,b=map(float,q.PARAMETERS['steering_discrete'])
    target=np.array([q.projection.virtual(x)for x in d['controls'][idx,:2]])
    excited=np.c_[state[idx,7],target-state[idx,6],np.maximum(state[idx,3],0.)**2*np.sign(target)]
    mask=np.linalg.norm(excited,axis=1)>1e-6;idx=idx[mask];target=target[mask]
    feature=-b*np.maximum(state[idx,3],0.)**2*np.tanh(state[idx,6]/.015)
    residual=state[idx+1,7]-a*state[idx,7]-b*(target-state[idx,6])
    assert feature@feature>1e-8,'NO_LOAD_EXCITATION'
    optimum=float(feature@residual/(feature@feature))
    p=dict(coefficients=[a,b,optimum],smooth_width_rad=.015,
        method='one scalar bounded least squares; out-of-bound optimum rejected, not clipped',fit_path=d['path'],
        fixed_fit_interval=[2200,6400],fit_native_before=idx.tolist(),fit_samples=len(idx),
        rmse=float(np.sqrt(np.mean((residual-optimum*feature)**2))),
        original_transient_coefficients_unchanged=True,one_scalar_fit=True,
        data_not_independent_confirmation=True,models=0,physical_native=0,training_updates=0)
    q.dump(C/'PARAMETERS.json',p)
    model=q.projection.load('v1159_scalar_candidate',C/'model.py')
    try:
        *_,pole=model.validate(p);passed=True;reason=None
    except AssertionError as e:pole=None;passed=False;reason=str(e)
    result=dict(closed=True,passed=passed,reason=reason,load_scalar=optimum,stable_fixed_speed_branch_pole=pole,
                fit_samples=len(idx),fit_rmse=p['rmse'],models=0,physical_native=0,analytical_native=0,wall_s=time.monotonic()-start)
    q.dump(O/'FIT_RESULT.json',result);print(q.json.dumps(result));return 0 if passed else 1


if __name__=='__main__':sys.exit(main())
