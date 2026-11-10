"""Reconstruct exact actuator history and candidate inputs; no model calls."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
from independent import check as independent_check
from fixture import make,old

R=Path(__file__).resolve().parents[2]
SOURCE=Path(__file__).with_name('vehicle_control.py')
spec=importlib.util.spec_from_file_location('v990_independent_selected_class',SOURCE)
control=importlib.util.module_from_spec(spec);spec.loader.exec_module(control)


def same(a,b):
    if isinstance(a,dict):return isinstance(b,dict)and a.keys()==b.keys()and all(same(a[k],b[k])for k in a)
    if isinstance(a,list):return isinstance(b,list)and len(a)==len(b)and all(same(x,y)for x,y in zip(a,b))
    if isinstance(a,bool)or a is None or isinstance(a,str):return a==b
    return isinstance(b,(int,float))and np.isfinite(a)and np.isfinite(b)and abs(a-b)<=1e-10


def body(q,v):
    yaw=np.arctan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
    return [float(q[0]),float(q[1]),float(yaw),float(v[0]*np.cos(yaw)+v[1]*np.sin(yaw)),float(v[5])]


def check(out,task):
    p=Path(out)/'physics';origin=task['origin_native_tick']
    setup=json.loads((p/'SETUP.json').read_text());binding=json.loads((p/'ACTIVE_ADAPTER_BINDING.json').read_text())
    assert binding['passed']and binding['native_tick']==origin and binding['physical_state_unchanged']
    assert binding['new_control_sha256']==hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'CONTROL_SOURCE_CHANGED'
    assert setup['adapter_switch_native_tick']==origin and setup['active_adapter_source_sha256']==binding['new_control_sha256']
    commands=json.loads((p/'BODY_COMMANDS.json').read_text())
    records=json.loads(gzip.decompress((p/'ALLOCATION.json.gz').read_bytes()))
    with np.load(p/'NATIVE_TRACE.npz')as f:q=f['qpos'];v=f['qvel'];ctrl=f['ctrl'][:,setup['actuator_ids']]
    assert len(q)==len(v)==len(ctrl)==len(commands)and len(q)>origin
    assert len(records)==len(q)-origin,'MISSING_ALLOCATION_ROWS'
    history=make(old.Adapter,setup);active=make(control.Adapter,setup);error=0.;rear_residual=0.
    for i,row in enumerate(commands):
        if i==origin:
            transfer=control.transfer_restored_state(history,active)
            assert transfer['original_last_control']==binding['original_last_control']
            assert transfer['original_longitudinal_integral']==binding['original_longitudinal_integral']
        adapter=history if i<origin else active;previous=adapter.last.copy()
        selected=adapter.compute(*row[1:6]);error=max(error,float(abs(selected-ctrl[i]).max()))
        if i<origin:continue
        rec=records[i-origin]
        assert rec['native_tick']==i+1 and rec['stale']==bool(row[5])and [rec['v'],rec['w']]==row[1:3],'ALLOCATION_RECEIPT_INPUT_CHANGED'
        actual_pre=body(q[i-1],v[i-1]);actual_post=body(q[i],v[i])
        assert np.max(abs(np.array(rec['pre_native_body'])-actual_pre))<=1e-8,'FORGED_PRE_BODY'
        assert np.max(abs(np.array(rec['post_native_body'])-actual_post))<=1e-8,'FORGED_POST_BODY'
        assert np.max(abs(np.array(row[3:5])-np.array(actual_pre[3:5])))<=1e-8,'FEEDBACK_NOT_ACTUAL_PRE_STATE'
        for label,index in [('pre_native_steering',i-1),('post_native_steering',i)]:
            expected=np.r_[q[index,setup['steering_qpos_addresses']],v[index,setup['steering_qvel_addresses']]]
            assert np.max(abs(np.array(rec[label])-expected))<=1e-8,'FORGED_ENCODER'
        assert same(rec['proof'],active.last_allocation_proof),'ALLOCATION_PROOF_NOT_RECONSTRUCTIBLE'
        assert np.max(abs(np.array(rec['actual_ctrl'])-ctrl[i]))<=1e-8,'RECORDED_CTRL_NOT_DISPATCHED'
        independent=independent_check(previous,ctrl[i],setup['limits'],setup['slew_per_second'])
        rear_residual=max(rear_residual,independent['rear_compatibility_residual_rad_s'])
    assert error<=1e-8,'MIXED_FINAL_ACTUATION_MAP_MISMATCH'
    return dict(passed=True,models=0,integrations=0,historical_control_rows=origin,new_control_rows=len(records),
        maximum_control_reconstruction_error=error,maximum_independent_rear_residual_rad_s=rear_residual,
        physical_tracking_qualified_by_this_check=False,
        force_arrays_are_logged_for_diagnosis_not_independently_replayed=True)
