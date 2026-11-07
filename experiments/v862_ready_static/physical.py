"""Lazy physical dependency boundary. Nothing here constructs a model on import."""
import json,os,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def create_vehicle(out,task):
    sys.path.insert(0,str(R/'experiments/v858_nav2_verified'))
    import vehicle
    original=vehicle.initialize
    def scoped_factory(*args,**kwargs):
        previous=Path.cwd()
        try:
            os.chdir('/home/linghu/catkin_ws/src/mk-mini')
            return original(*args,**kwargs)
        finally:os.chdir(previous)
    vehicle.initialize=scoped_factory
    try:
        instance=vehicle.Vehicle(out,task['case_id'],task['seed'],False)
        assert instance.actor is None,'STATIC_TASK_HAS_ACTOR'
        return instance
    finally:vehicle.initialize=original
def replay(instance,deadline,out):
    """Same executed-control replay contract, with the newly authorized deadline."""
    import numpy as np
    import mujoco as mj
    d=mj.MjData(instance.m);mj.mj_setState(instance.m,d,instance.initial,instance.spec)
    mj.mj_forward(instance.m,d);maximum=0.;mismatches=0;count=0
    for i,row in enumerate(instance.rows):
        if time.time()>=deadline-5:raise TimeoutError('AUTHORIZED_REPLAY_DEADLINE')
        d.ctrl[:]=row['ctrl'];instance.native(instance.m,d);count+=1
        mj.mj_kinematics(instance.m,d);mj.mj_collision(instance.m,d)
        for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
            value=getattr(d,key)
            if not np.isfinite(value).all():raise RuntimeError('NONFINITE_REPLAY_STATE '+key)
            if value.size:maximum=max(maximum,float(np.max(abs(value-row[key]))))
        classified=[instance.catalog.classify(c,i+1,(i+1)//8,float(d.time))for c in d.contact]
        actual=[(r['geom1_id'],r['geom2_id'],r['contact_type'],r['contact_distance'])for r in classified]
        expected=instance.contacts[i+1]
        if len(actual)!=len(expected)or any(a[:3]!=b[:3]or abs(a[3]-b[3])>1e-8 for a,b in zip(actual,expected)):mismatches+=1
        if count%100==0:(out/'REPLAY_PROGRESS.json').write_text(json.dumps(dict(executed_replay_native=count))+'\n')
    result=dict(replay_native=count,maximum_qpos_qvel_ctrl_mocap_error=maximum,
                contact_mismatched_ticks=mismatches,passed=maximum<=1e-8 and mismatches==0)
    (out/'REPLAY.json').write_text(json.dumps(result,indent=2)+'\n');return result
