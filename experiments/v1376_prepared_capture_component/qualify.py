"""Saved-input/controller/real-entry/JSON/output qualification with zero models."""
import argparse
import importlib.abc
import importlib.util
import os
import subprocess
import sys
from component_context import *

class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','physical','factory','rclpy'}:raise AssertionError('QUALIFICATION_MODEL_IMPORT '+name)

def producer_check():
    sys.meta_path.insert(0,NoModel())
    import numpy as np
    from audit import audit
    # Exact previous production proof plus false booleans and a one-ULP float,
    # through the same atomic serializer used for full current audit results.
    prior=read(R/'runs/v1373_sampling_audit_serialization/SUPPLEMENTAL_INDEPENDENT_AUDIT.json')
    value=dict(prior,fixture_false=np.bool_(False),fixture_true=np.bool_(True),fixture_nextafter=np.nextafter(np.float64(1.),np.float64(2.)))
    path=O/'PRODUCER_SERIALIZATION_FIXTURE.json';dump(path,value);restored=read(path)
    assert restored==value and restored['fixture_false'] is False and restored['fixture_nextafter']>1.
    print(json.dumps(dict(passed=True,real_audit_module_imported=True,full_previous_proof_roundtrip_exact=True,false_true_and_one_ulp_preserved=True,python=sys.version,numpy=np.__version__,models=0,physical_native=0)))

def guard_child():
    spec=importlib.util.spec_from_file_location('phase_capture_exact_output_guard',R/'experiments/v1372_coherent_sampling_fault/qualify_output.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.RAW=RAW;m.child()

def main():
    sys.meta_path.insert(0,NoModel())
    from controller import Capture,errors
    import numpy as np
    task=read(C/'TASKS.json')[0];task_check(task);checks={};prior=read(Path(task['prior_raw'])/'APPLIED_JOURNAL.json')[9390]
    assert task['origin_body']==prior['body'] and task['origin_memory']==prior['last_ctrl'];checks['exact_saved_state_input']=True
    # Cursor below is metadata only; verify travel/200-tick/measured-rest phase
    # contract, not an assertion about actual vehicle response.
    controller=Capture(task);body=task['origin_body'][:];enc=prior['encoders'];last=prior['last_ctrl'];v,w,p=controller.select(body,9390,enc,last);assert v==-.1 and w==-.05
    moved=body[:];moved[0]-=.26;v,w,p=controller.select(moved,9395,enc,last);assert p['phase']=='BRAKE_REVERSE' and v==w==0.
    v,w,p=controller.select(moved,9590,enc,last);assert p['phase']=='BRAKE_REVERSE'
    moving=moved[:];moving[3]=.004;v,w,p=controller.select(moving,9595,enc,last);assert p['phase']=='BRAKE_REVERSE' and v==w==0.
    v,w,p=controller.select(moved,9600,enc,last);assert p['phase']=='PREPARE_FORWARD' and v==w==0. and p['parked_target'] is not None
    k=task['forward_curvature'];front=[np.arctan(.6*k/(1-.27*k)),np.arctan(.6*k/(1+.27*k))]
    settling=[*front,.04,0.];v,w,p=controller.select(moved,9605,settling,[*front,0.,0.]);assert p['phase']=='PREPARE_FORWARD'
    correct=[*front,0.,0.];v,w,p=controller.select(moving,9610,correct,[*front,0.,0.]);assert p['phase']=='PREPARE_FORWARD'
    v,w,p=controller.select(moved,9615,correct,[*front,.001,.001]);assert p['phase']=='PREPARE_FORWARD'
    v,w,p=controller.select(moved,9620,correct,[*front,0.,0.]);assert p['phase']=='FORWARD_ARC' and v==.1 and w==-.05 and p['parked_target'] is None
    moved[0]+=.16;v,w,p=controller.select(moved,9625,correct,[*front,0.,0.]);assert p['phase']=='CAPTURE_COMPLETE' and v==w==0.
    checks['actual_controller_metadata_phase_and_rest_contract']=True
    # Execute the unchanged real coupled-steering allocator on saved controller
    # metadata only. object.__new__ is not a vehicle/MjModel initialization.
    from native import binding
    _,Adapter,_,_=binding()
    from types import SimpleNamespace
    setup=read(Path(task['prior_raw'])/'physics/SETUP.json');limits=np.asarray(setup['limits'])
    actual=read(R/'runs/v858_nav2_verified/v1375/capture_main/APPLIED_JOURNAL.json')[9875]
    owner=object.__new__(Adapter);owner.wheelbase=.6;owner.track=.54;owner.max_curvature=1/1.32;owner.center_limit=__import__('math').atan(.6/1.32);owner.dt=.01;owner.virtual_rate=.6
    owner.last=np.asarray(actual['last_ctrl']);owner.integral=actual['integral'];owner.parked_target=__import__('math').atan(-.3);owner._steering_motion_active=False
    owner.commands=SimpleNamespace(lower=limits[:,0],upper=limits[:,1],rate=np.asarray(setup['slew_per_second'])*.08,
        legal=lambda u:bool(np.isfinite(u).all() and (u>=limits[:,0]-1e-10).all() and (u<=limits[:,1]+1e-10).all()))
    owner.encoders=lambda:np.asarray(actual['encoders'])
    try:owner.compute(0.,0.,.004,0.,False)
    except AssertionError:pass
    else:raise AssertionError('UNSAFE_MEASURED_STEERING_ENTRY_ACCEPTED')
    for _ in range(400):
        previous=owner.last.copy();u=owner.compute(0.,0.,0.,0.,False)
        assert max(abs(x) for x in u[2:])==0 and np.max(abs(u-previous)-np.asarray(setup['slew_per_second'])*.01)<=1e-10
    assert np.max(abs(owner.last[:2]-front))<=1e-8
    try:owner.compute(0.,0.,.011,0.,False)
    except AssertionError:pass
    else:raise AssertionError('COUPLED_MOTION_BOUND_ACCEPTED')
    checks['real_original_coupled_allocator400_metadata_calls_and_unsafe_entry_rejections']=True
    sys.path.insert(0,str(R/'experiments/v1374_day_handoff_validation'))
    from probe import interval_ball,field,geometry
    nominal=read(O/'NOMINAL_PREPARED_CAPTURE.json');path=np.asarray(nominal['trajectory']);ball=interval_ball(nominal['causal_vertices'],93.9,93.9+__import__('math').tau/.32)
    assert [*ball[0].tolist(),ball[1]]==task['causal_all_future_ball']
    known=read(Path(task['prior_raw'])/'physics/SETUP.json')['known'];minimum=float(geometry.pose_values(field(known,ball),path[:,:3]).min())
    assert minimum>=.22 and nominal['position_error_m']<=.12 and nominal['heading_error_rad']<=.20
    assert nominal['periodic_source_tick']<=9390;checks['complete_nominal_capture_with_full_period_causal_disk']=True
    try:authorize(task,{})
    except AssertionError as e:assert 'MODELS_DISABLED' in str(e)
    else:raise AssertionError('PREPARATION_MODEL_AUTHORITY_ACCEPTED')
    checks['models_denied_during_preparation']=True
    # The saved probe deliberately imports old frozen modules. Resolve this
    # batch's runtime by exact path rather than the now-shared name campaign.
    runtime_spec=importlib.util.spec_from_file_location('phase_capture_qualified_campaign',C/'campaign.py')
    runtime=importlib.util.module_from_spec(runtime_spec);runtime_spec.loader.exec_module(runtime)
    native_environment,peer_environment=runtime.native_environment,runtime.peer_environment
    spec=importlib.util.spec_from_file_location('phase_capture_isolation',R/'tools/isolate.py');isolation=importlib.util.module_from_spec(spec);spec.loader.exec_module(isolation)
    ros,env=peer_environment();entries=[]
    commands=[('backend',isolation.command(C/'backend_check.py',writable=True),native_environment()),
        ('native',[sys.executable,'-B',str(C/'native.py'),str(C/'ENTRY.json'),'--entry-check'],native_environment()),
        ('producer_audit_json',isolation.command(C/'qualify.py',writable=True)+['--producer-check'],native_environment()),
        ('legacy_output_guard',[sys.executable,'-B',str(C/'qualify.py'),'--guard-child'],native_environment())]
    for name,cmd,environment in commands:
        p=subprocess.run(cmd,cwd=R,env=environment,capture_output=True,text=True,timeout=45);(O/(name+'.console')).write_text(p.stdout+p.stderr)
        assert p.returncode==0,name+' '+p.stderr[-1000:];proof=json.loads(p.stdout.strip().splitlines()[-1]);assert proof['passed'];entries.append(dict(name=name,proof=proof))
    link=RAW/'qualification/readonly_source_link'
    if link.is_symlink():link.unlink()
    assert sources();dump(O/'QUALIFICATION.json',dict(passed=True,checks=checks,entries=entries,nominal_full_period_minimum_m=minimum,
        actual_response_qualified=False,models=0,physical_native=0,private_native=0,replay_native=0,
        tested_source_hashes={str(p.relative_to(R)):sha(p) for p in C.glob('*.py')}))
    print(json.dumps(dict(passed=True,checks=len(checks),real_entries=len(entries),nominal_full_period_minimum_m=minimum,models=0)))

if __name__=='__main__':
    if '--producer-check' in sys.argv:producer_check()
    elif '--guard-child' in sys.argv:guard_child()
    else:main()
