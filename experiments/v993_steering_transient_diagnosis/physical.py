"""Original t0/history exactly, then the preregistered fixed-stimulus adapter."""
import importlib.util,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v993_steering_transient_diagnosis'
def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=load('v993_original_factory',R/'experiments/v974_daytime_binding_gate/physical.py')

def create_vehicle(out,task,guard,progress,on_vehicle=lambda v:None):
    vehicle=base.create_vehicle(out,task);on_vehicle(vehicle);guard();vehicle.scan()
    commands=json.loads((O/'prior_v974/physics/BODY_COMMANDS.json').read_text());maximum=0.
    with np.load(O/'prior_v974/physics/NATIVE_TRACE.npz')as expected:
        for i,row in enumerate(commands[:task['origin_native_tick']]):
            guard();vehicle._in_history_step=True;vehicle.step(row[1],row[2],row[5]);vehicle._in_history_step=False
            for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
                a=np.asarray(getattr(vehicle.d,key));b=expected[key][i]
                if a.size:maximum=max(maximum,float(abs(a-b).max()))
            assert maximum<=1e-8,'HISTORICAL_PREFIX_STATE_CONTROL_MISMATCH'
            if i%5==0:vehicle.scan()
            if(i+1)%512==0:progress(vehicle,'RESTORING_HISTORY')
    assert vehicle.count==task['origin_native_tick']and abs(vehicle.d.time-task['origin_sim_time'])<=1e-9
    p=Path(out);(p/'PREFIX_RESTORE.json').write_text(json.dumps(dict(passed=True,historical_native=vehicle.count,
        maximum_full_state_control_error=maximum,no_root_or_time_rewrite=True),indent=2)+'\n')
    import mujoco as mj
    from actuation_binding import bind_restored
    proof=bind_restored(vehicle,task,p,mj);progress(vehicle,'HISTORY_RESTORED_AND_SWITCHED')
    vehicle.probe_initial_curvature=proof['stopped_origin_curvature']
    return vehicle
replay=base.replay
