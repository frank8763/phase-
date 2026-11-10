"""Reconstruct mixed historical/new motor controls from saved actual inputs."""
import gzip,hashlib,importlib.util,json,sys,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent
def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
source=R/'experiments/v984_decoupled_yaw_servo/vehicle_control.py';new=load('v985_audit_control',source)
old=load('v985_audit_old',R/'experiments/v958_hold_steering_contract/vehicle_control.py')
def make(cls,setup):
    a=cls.__new__(cls);limits=np.asarray(setup['limits'],float)
    a.commands=SimpleNamespace(lower=limits[:,0],upper=limits[:,1],rate=np.asarray(setup['slew_per_second'])*.08,
        legal=lambda u:bool(np.isfinite(u).all()and np.all(u>=limits[:,0]-1e-10)and np.all(u<=limits[:,1]+1e-10)))
    a.dt=.01;a.last=np.zeros(4);a.integral=0.;a.wheelbase=.6;a.track=.54;a.radius=.12;a.center_limit=.42722137342572125
    a.max_curvature=np.tan(a.center_limit)/a.wheelbase;a.mode='DRIVING';a.encoders=None;a.last_yaw_proof=None
    return a
def equal_proof(a,b):
    if isinstance(a,dict):return isinstance(b,dict)and a.keys()==b.keys()and all(equal_proof(a[k],b[k])for k in a)
    if isinstance(a,list):return isinstance(b,list)and len(a)==len(b)and all(equal_proof(x,y)for x,y in zip(a,b))
    if isinstance(a,bool)or a is None or isinstance(a,str):return a==b
    return isinstance(b,(int,float))and np.isfinite(a)and np.isfinite(b)and abs(a-b)<=1e-10
def compare_history(data,expected,commands,old_commands,origin):
    assert len(commands)>=origin and len(old_commands)>=origin
    errors={}
    for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
        a=np.asarray(data[key][:origin]);b=np.asarray(expected[key][:origin]);assert a.shape==b.shape and len(a)==origin
        errors[key]=float(abs(a-b).max())if a.size else 0.
    assert max(errors.values())<=1e-8,'INDEPENDENT_HISTORICAL_STATE_CONTROL_MISMATCH'
    assert all([a[1],a[2],a[5]]==[b[1],b[2],b[5]]for a,b in zip(commands[:origin],old_commands[:origin])),'HISTORICAL_BODY_REQUEST_CHANGED'
    return dict(passed=True,full_state_control_errors=errors,historical_native_rows=origin,integrations=0)
def check(out,task):
    out=Path(out);p=out/'physics';origin=task['origin_native_tick'];setup=json.loads((p/'SETUP.json').read_text())
    binding=json.loads((p/'ACTIVE_ADAPTER_BINDING.json').read_text());commands=json.loads((p/'BODY_COMMANDS.json').read_text())
    assert binding['passed']and binding['native_tick']==origin and binding['integrations']==0 and binding['physical_state_unchanged']
    assert binding['new_control_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()and setup['adapter_switch_native_tick']==origin
    with np.load(p/'NATIVE_TRACE.npz')as f:ctrl=f['ctrl'][:,setup['actuator_ids']];q=f['qpos'];vel=f['qvel']
    assert len(commands)==len(ctrl)>origin
    proofs=json.loads(gzip.decompress((p/'YAW_FEEDBACK.json.gz').read_bytes()));assert len(proofs)==len(ctrl)-origin
    history=make(old.Adapter,setup);active=make(new.Adapter,setup);error=0.;feedback=0
    for i,row in enumerate(commands):
        if i==origin:
            transfer=new.transfer_restored_state(history,active)
            assert transfer['original_last_control']==binding['original_last_control']and abs(transfer['original_longitudinal_integral']-binding['original_longitudinal_integral'])<=1e-12
        # The actual pre-native state is the preceding saved sample. No online
        # privileged actor information is used by this independent offline check.
        if i>=origin:
            a=q[i-1];yaw=np.arctan2(2*(a[3]*a[6]+a[4]*a[5]),1-2*(a[5]**2+a[6]**2))
            measured=[float(vel[i-1,0]*np.cos(yaw)+vel[i-1,1]*np.sin(yaw)),float(vel[i-1,5])]
            assert max(abs(np.asarray(row[3:5])-measured))<=1e-8,'RECORDED_FEEDBACK_NOT_ACTUAL_PRE_NATIVE_STATE'
        adapter=history if i<origin else active;u=adapter.compute(*row[1:6]);error=max(error,float(abs(u-ctrl[i]).max()))
        if i>=origin:
            recorded=proofs[i-origin];assert recorded['native_tick']==i+1 and recorded['stale']==bool(row[5])
            assert [recorded['v'],recorded['w']]==row[1:3]
            assert np.max(abs(np.asarray(recorded['actual_ctrl'])-ctrl[i]))<=1e-8
            assert equal_proof(recorded['proof'],adapter.last_yaw_proof),'FEEDBACK_PROOF_NOT_RECONSTRUCTIBLE'
            feedback+=int(adapter.last_yaw_proof['applied'])
    assert error<=1e-8,'MIXED_HISTORICAL_NEW_CONTROL_MAP_MISMATCH'
    return dict(passed=True,models=0,integrations=0,historical_control_rows=origin,new_control_rows=len(ctrl)-origin,
        feedback_rows=feedback,maximum_motor_control_reconstruction_error=error,physical_response_accepted_by_this_check=False)
def audit(out,task):
    try:
        prior=R/'runs/v985_rear_yaw_components/prior_v974'
        required=json.loads((C/'RESTORE_REQUIREMENTS.json').read_text())
        for name in ['physics/NATIVE_TRACE.npz','physics/BODY_COMMANDS.json']:
            path=prior/name;row=next(r for r in required['files']if r['path']==str(path.relative_to(R)))
            assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'],'HISTORICAL_INPUT_SHA_MISMATCH'
        p=Path(out)/'physics'
        commands=json.loads((p/'BODY_COMMANDS.json').read_text());old_commands=json.loads((prior/'physics/BODY_COMMANDS.json').read_text())
        with np.load(p/'NATIVE_TRACE.npz')as data,np.load(prior/'physics/NATIVE_TRACE.npz')as expected:
            history=compare_history(data,expected,commands,old_commands,task['origin_native_tick'])
        answer=check(out,task);answer['independent_full_historical_restore']=history
    except BaseException as e:answer=dict(passed=False,error=repr(e),traceback=traceback.format_exc(),models=0,integrations=0)
    (Path(out)/'ACTUATION_AUDIT.json').write_text(json.dumps(answer,indent=2)+'\n');return answer
