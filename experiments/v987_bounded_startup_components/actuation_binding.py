"""Switch only controller memory at the exact restored origin; no model calls."""
import copy,gzip,hashlib,importlib.util,inspect,json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2]
SOURCE=R/'experiments/v984_decoupled_yaw_servo/vehicle_control.py'
OLD=R/'experiments/v958_hold_steering_contract/vehicle_control.py'
spec=importlib.util.spec_from_file_location('v987_frozen_rear_yaw',SOURCE)
control=importlib.util.module_from_spec(spec);spec.loader.exec_module(control)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def bind_restored(vehicle,task,out,mj):
    out=Path(out);origin=task['origin_native_tick'];old=vehicle.adapter
    assert vehicle.count==origin and abs(vehicle.d.time-task['origin_sim_time'])<=1e-9,'ADAPTER_SWITCH_NOT_AT_EXACT_ORIGIN'
    assert Path(inspect.getsourcefile(old.compute)).resolve()==OLD,'HISTORICAL_ADAPTER_NOT_V958'
    before={n:np.asarray(getattr(vehicle.d,n)).copy()for n in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
    clock=float(vehicle.d.time);count=vehicle.count;model=vehicle.m
    new=control.Adapter(vehicle.m,mj,vehicle.dt,encoders=old.encoders)
    assert type(new.commands)is type(old.commands)and new.commands.ids==old.commands.ids,'ACTUATOR_MAP_TYPE_OR_IDS_CHANGED'
    proof=control.transfer_restored_state(old,new)
    assert all(np.array_equal(a,np.asarray(getattr(vehicle.d,n)))for n,a in before.items())
    assert vehicle.m is model and vehicle.count==count and vehicle.d.time==clock,'SWITCH_ADVANCED_OR_CHANGED_MODEL'
    vehicle.adapter=new
    rows=[];step=vehicle.step;finish=vehicle.finish
    def checked_step(v,w,stale=False):
        tick=vehicle.count;step(v,w,stale)
        assert vehicle.count==tick+1,'NONCANONICAL_STEP_COUNT'
        p=copy.deepcopy(vehicle.adapter.last_yaw_proof)
        rows.append(dict(native_tick=vehicle.count,v=float(v),w=float(w),stale=bool(stale),proof=p,
                         actual_ctrl=vehicle.d.ctrl[new.commands.ids].tolist()))
    def checked_finish():
        # Save actuation evidence even when native safety/serialization fails.
        with gzip.open(out/'YAW_FEEDBACK.json.gz','wt')as f:json.dump(rows,f,allow_nan=False)
        return finish()
    vehicle.step=checked_step;vehicle.finish=checked_finish
    proof.update(passed=True,native_tick=count,sim_time=clock,old_control_source=str(OLD.relative_to(R)),
        old_control_sha256=sha(OLD),new_control_source=str(SOURCE.relative_to(R)),new_control_sha256=sha(SOURCE),
        switch_after_exact_historical_restore=True,physical_state_unchanged=True,active_revision='V984_REAR_ONLY_BODY_YAW',
        command_map_source=str(Path(inspect.getsourcefile(type(new.commands))).resolve().relative_to(R)))
    (out/'ACTIVE_ADAPTER_BINDING.json').write_text(json.dumps(proof,indent=2)+'\n')
    setup_path=out/'SETUP.json';setup=json.loads(setup_path.read_text())
    setup.update(active_adapter_revision=proof['active_revision'],active_adapter_source_sha256=sha(SOURCE),adapter_switch_native_tick=count,
                 historical_adapter_revision=setup['adapter_revision'])
    setup_path.write_text(json.dumps(setup,indent=2)+'\n')
    return proof
