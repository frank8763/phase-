"""Predeclared open-command native control qualification, single 11-second execution."""
import fcntl,json,os,sys,time,traceback
from pathlib import Path
import numpy as np
from physics_backend import Vehicle,R,C
from instrumentation import dump
OUT=R/'runs/v856_nav2_foundation';END=1794052800.
def main():
    out=OUT/'vehicle_qualification01';assert not out.exists(),'QUALIFICATION_ALREADY_CLAIMED'
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);os.sched_setaffinity(0,{sorted(os.sched_getaffinity(0))[3]})
    vehicle=None;result=dict(passed=False,actual_native=0,replay_native=0,private_native=0,environment_initializations_attempted=1)
    try:
        vehicle=Vehicle(out,'WEST_EAST',10010001,False);start=time.monotonic();maximum_lag=0.;observations=[]
        for k in range(1100):
            if time.time()>=END-20:raise TimeoutError('ROOT_DEADLINE')
            elapsed=k*.01
            v,w=(.2,0.)if 1<=elapsed<4 else(.15,.05)if 6<=elapsed<9 else(0.,0.)
            target=start+k*.01;time.sleep(max(0.,target-time.monotonic()));lag=time.monotonic()-target;maximum_lag=max(maximum_lag,lag)
            if lag>.1:raise RuntimeError('PHYSICS_WALL_LAG_OVER_100MS')
            vehicle.step(v,w);observations.append(vehicle.body())
        obs=np.asarray(observations);forward=float(np.mean(obs[250:390,3]));yawrate=float(np.mean(obs[750:890,4]));stopped=float(np.linalg.norm(vehicle.d.qvel[:2]));summary=vehicle.finish();result.update(summary,maximum_wall_lag_s=maximum_lag,steady_forward_m_s=forward,steady_turn_yaw_rad_s=yawrate,final_translation_speed_m_s=stopped)
        replay=vehicle.replay();result.update(replay_native=replay['replay_native'],replay=replay)
        result['checks']=dict(forward_tracks_fixed_02_command=.10<=forward<=.30,positive_yaw_response=.01<=yawrate<=.15,brake_settles_below_003=stopped<=.03,physical_safety=summary['bad_contacts']==0 and summary['minimum_actual_clearance_m']>=.15,full_native_replay=replay['passed'],wall_paced=maximum_lag<=.1)
        result['passed']=all(result['checks'].values())
    except BaseException as e:
        result.update(error=repr(e),traceback=traceback.format_exc())
        if vehicle:result.update(vehicle.finish())
    finally:
        if out.exists():dump(out/'RESULT.json',result)
        else:dump(OUT/'QUALIFICATION_ENTRY_ERROR.json',result)
        print(json.dumps(result),flush=True)
    return 0 if result['passed']else 1
if __name__=='__main__':sys.exit(main())
