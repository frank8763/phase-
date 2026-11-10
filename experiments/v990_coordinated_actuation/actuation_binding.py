"""Candidate memory switch/recording seam; no model initialization or stepping.

A future separately authorized component engine may call this after restoring the
original history. This module itself grants no physical authority.
"""
import copy
import gzip
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import numpy as np

R=Path(__file__).resolve().parents[2]
SOURCE=Path(__file__).with_name('vehicle_control.py')
OLD=R/'experiments/v958_hold_steering_contract/vehicle_control.py'
spec=importlib.util.spec_from_file_location('v990_selected_allocation',SOURCE)
control=importlib.util.module_from_spec(spec);spec.loader.exec_module(control)


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def forces(vehicle):
    # Values only; querying these arrays does not call a physics API.
    return {n:np.asarray(getattr(vehicle.d,n)).tolist()for n in
        ['actuator_force','qfrc_actuator','qfrc_constraint']if hasattr(vehicle.d,n)}


def bind_restored(vehicle,task,out,mj):
    out=Path(out);old=vehicle.adapter
    assert task['origin_native_tick']in [6083,7814]and task['stage']=='component','WRONG_COMPONENT_ORIGIN'
    assert vehicle.count==task['origin_native_tick']and abs(vehicle.d.time-task['origin_sim_time'])<=1e-9,'SWITCH_NOT_AT_ORIGINAL_ORIGIN'
    assert Path(inspect.getsourcefile(old.compute)).resolve()==OLD,'HISTORICAL_ADAPTER_NOT_V958'
    stopped=np.asarray(vehicle.body()[3:5],float)
    assert np.max(abs(stopped))<=.03 and np.linalg.norm(np.asarray(vehicle.d.qvel)[:2])<=.03,'SWITCH_REQUIRES_ACTUAL_STOP'
    enc=np.asarray(vehicle.steering_sample(),float)
    assert enc.shape==(4,)and np.max(abs(enc[2:]))<=.03,'SWITCH_REQUIRES_STEERING_SETTLED'
    states={n:np.asarray(getattr(vehicle.d,n)).copy()for n in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']}
    stamp=float(vehicle.d.time);count=vehicle.count;model=vehicle.m
    new=control.Adapter(vehicle.m,mj,vehicle.dt,encoders=old.encoders)
    assert type(new.commands)is type(old.commands)and new.commands.ids==old.commands.ids,'COMMAND_MAP_CHANGED'
    proof=control.transfer_restored_state(old,new)
    assert all(np.array_equal(a,np.asarray(getattr(vehicle.d,n)))for n,a in states.items()),'PHYSICAL_STATE_CHANGED_BY_SWITCH'
    assert vehicle.m is model and vehicle.count==count and vehicle.d.time==stamp,'CLOCK_MODEL_OR_COUNT_CHANGED_BY_SWITCH'
    vehicle.adapter=new;rows=[];step=vehicle.step;finish=vehicle.finish
    def checked_step(v,w,stale=False):
        tick=vehicle.count;body=list(vehicle.body());enc=np.asarray(vehicle.steering_sample(),float).tolist()
        before_forces=forces(vehicle);error=None
        try:return step(v,w,stale)
        except BaseException as e:error=repr(e);raise
        finally:
            advanced=vehicle.count-tick
            if advanced==1:
                rows.append(dict(native_tick=vehicle.count,v=float(v),w=float(w),stale=bool(stale),
                    pre_native_body=body,pre_native_steering=enc,pre_native_forces=before_forces,
                    post_native_body=list(vehicle.body()),post_native_steering=np.asarray(vehicle.steering_sample(),float).tolist(),
                    post_native_forces=forces(vehicle),proof=copy.deepcopy(new.last_allocation_proof),
                    actual_ctrl=np.asarray(vehicle.d.ctrl)[new.commands.ids].tolist(),step_error=error))
            elif advanced!=0:raise AssertionError('NONCANONICAL_STEP_COUNT')
    def checked_finish():
        with gzip.open(out/'ALLOCATION.json.gz','wt')as f:json.dump(rows,f,allow_nan=False)
        return finish()
    vehicle.step=checked_step;vehicle.finish=checked_finish
    proof.update(passed=True,native_tick=count,sim_time=stamp,old_control_source=str(OLD.relative_to(R)),
        old_control_sha256=sha(OLD),new_control_source=str(SOURCE.relative_to(R)),new_control_sha256=sha(SOURCE),
        physical_state_unchanged=True,active_revision='V990_JOINT_CURVATURE_COMMON_SPEED_ALLOCATION',
        switch_after_exact_historical_restore=True,models_initialized_by_binding=0)
    (out/'ACTIVE_ADAPTER_BINDING.json').write_text(json.dumps(proof,indent=2)+'\n')
    p=out/'SETUP.json';setup=json.loads(p.read_text())
    setup.update(active_adapter_revision=proof['active_revision'],active_adapter_source_sha256=sha(SOURCE),
                 adapter_switch_native_tick=count,historical_adapter_revision=setup['adapter_revision'])
    p.write_text(json.dumps(setup,indent=2)+'\n')
    return proof
