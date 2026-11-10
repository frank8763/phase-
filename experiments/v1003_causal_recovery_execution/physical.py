"""True t0 and exact6083 history, then exact frozen V993 controller binding."""
import importlib.util,json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v1003_causal_recovery_execution'
p=R/'experiments/v974_daytime_binding_gate/physical.py'
s=importlib.util.spec_from_file_location('v1003_original_physical_factory',p);base=importlib.util.module_from_spec(s);s.loader.exec_module(base)

def create_vehicle(out,task,guard,progress,on_vehicle):
    v=base.create_vehicle(out,task);on_vehicle(v);guard();v.scan();maximum=0.
    commands=json.loads((O/'prior_v974/physics/BODY_COMMANDS.json').read_text())
    with np.load(O/'prior_v974/physics/NATIVE_TRACE.npz')as expected:
        for i,row in enumerate(commands[:task['origin_native_tick']]):
            guard();v._in_history_step=True;v.step(row[1],row[2],row[5]);v._in_history_step=False
            for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
                a=np.asarray(getattr(v.d,key));b=expected[key][i]
                if a.size:maximum=max(maximum,float(abs(a-b).max()))
            assert maximum<=1e-8,'HISTORICAL_PREFIX_STATE_CONTROL_MISMATCH'
            if i%5==0:v.scan()
            if(i+1)%512==0:progress(v,'RESTORING_HISTORY')
    assert v.count==task['origin_native_tick']and abs(v.d.time-task['origin_sim_time'])<=1e-9
    Path(out,'PREFIX_RESTORE.json').write_text(json.dumps(dict(passed=True,historical_native=v.count,maximum_full_state_control_error=maximum,no_root_or_time_rewrite=True),indent=2)+'\n')
    import mujoco as mj
    from actuation_binding import bind_restored
    proof=bind_restored(v,task,out,mj);v.probe_initial_curvature=proof['stopped_origin_curvature'];progress(v,'HISTORY_RESTORED_AND_SWITCHED')
    return v
replay=base.replay
