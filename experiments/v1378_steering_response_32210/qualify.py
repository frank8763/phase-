"""Single saved-state steering response preparation, zero physical models."""
import importlib.abc
import importlib.util
import subprocess
import sys
from component_context import *
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','physical','factory','rclpy'}:raise AssertionError('QUALIFICATION_MODEL_IMPORT '+name)

def producer():
    sys.meta_path.insert(0,NoModel())
    import numpy as np
    from audit import audit
    proof=read(R/'runs/v858_nav2_verified/v1376/capture_main/FINAL_INDEPENDENT_AUDIT.json')
    value=dict(proof,false_fixture=np.bool_(False),true_fixture=np.bool_(True),ulp_fixture=np.nextafter(np.float64(1.),np.float64(2.)))
    p=O/'PRODUCER_SERIALIZATION_FIXTURE.json';dump(p,value);assert read(p)==value and read(p)['false_fixture'] is False
    print(json.dumps(dict(passed=True,actual_audit_module_imported=True,complete_prior_proof_JSON_exact=True,python=sys.version,numpy=np.__version__,models=0,physical_native=0)))
def guard():
    s=importlib.util.spec_from_file_location('v1378_original_write_guard',R/'experiments/v1372_coherent_sampling_fault/qualify_output.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.RAW=RAW;m.child()
def main():
    sys.meta_path.insert(0,NoModel())
    import math,numpy as np
    from types import SimpleNamespace
    from controller import Capture
    from envelope_geometry import bounds
    task=read(C/'TASKS.json')[0];task_check(task);row=read(Path(task['prior_raw'])/'APPLIED_JOURNAL.json')[32210];assert row['body']==task['origin_body'] and row['last_ctrl']==task['origin_memory'];checks={'exact_source_state_and_memory':True}
    body=row['body'];last=row['last_ctrl'];enc=row['encoders'];c=Capture(task)
    v,w,p=c.select(body,32210,enc,last);assert v==w==0 and p['phase']=='PREPARE_REVERSE' and p['parked_target'] is not None
    k=-.5;front=[math.atan(.6*k/(1-.27*k)),math.atan(.6*k/(1+.27*k))];correct=[*front,0.,0.];u=[*front,0.,0.]
    c.select(body,32215,correct,u);v,w,p=c.select(body,32220,[*front,.04,0.],u);assert p['ready_since'] is None
    c.select(body,32225,correct,u);moving=body[:];moving[3]=.004;_,_,p=c.select(moving,32230,correct,u);assert p['ready_since'] is None
    c.select(body,32235,correct,u);_,_,p=c.select(body,32240,correct,[*front,.001,.001]);assert p['ready_since'] is None
    c.select(body,32245,correct,u);_,_,p=c.select(body,32260,correct,u);assert p['phase']=='PREPARE_REVERSE'
    v,w,p=c.select(body,32265,correct,u);assert v==w==0 and p['phase']=='RESPONSE_COMPLETE' and p['parked_target'] is None;checks['actual_response_selector_hold_and_bad_feedback_rejections']=True
    from native import binding
    _,Adapter,_,_=binding();setup=read(Path(task['prior_raw'])/'physics/SETUP.json');limits=np.asarray(setup['limits']);owner=object.__new__(Adapter)
    owner.wheelbase=.6;owner.track=.54;owner.max_curvature=1/1.32;owner.center_limit=math.atan(.6/1.32);owner.dt=.01;owner.virtual_rate=.6;owner.last=np.asarray(last);owner.integral=row['integral'];owner.parked_target=math.atan(-.3);owner._steering_motion_active=False
    owner.commands=SimpleNamespace(lower=limits[:,0],upper=limits[:,1],rate=np.asarray(setup['slew_per_second'])*.08,legal=lambda a:bool(np.isfinite(a).all() and (a>=limits[:,0]-1e-10).all() and (a<=limits[:,1]+1e-10).all()))
    owner.encoders=lambda:np.asarray(enc)
    try:owner.compute(0.,0.,.004,0.,False)
    except AssertionError:pass
    else:raise AssertionError('MOVING_ENTRY_ACCEPTED')
    for _ in range(400):
        old=owner.last.copy();a=owner.compute(0.,0.,body[3],body[4],False);assert max(abs(x) for x in a[2:])==0 and np.max(abs(a-old)-np.asarray(setup['slew_per_second'])*.01)<=1e-10
    assert np.max(abs(owner.last[:2]-front))<=1e-8;checks['actual_original_allocator400_metadata_calls_and_zero_rear']=True
    lower=1e6
    for yaw in np.linspace(-.1,.1,201):
        b=body[:];b[2]+=yaw;value,_,_=bounds(task,b,setup['known']);lower=min(lower,value)
    lower-=.02+math.hypot(.44,.375)*.001/2;assert lower>=.22 and abs(lower-read(R/'runs/v1377_timed_handoff_witness/ORIGINAL_COUPLED_ENVELOPE_GEOMETRY.json')['complete_envelope_lower_m'])<=1e-8;checks['full_original_declared_envelope_geometric_readback']=True
    try:authorize(task,{})
    except AssertionError as e:assert 'MODELS_DISABLED' in str(e)
    else:raise AssertionError('UNAUTHORIZED_MODEL_ENTRY')
    checks['models_denied_in_preparation']=True
    s=importlib.util.spec_from_file_location('v1378_own_campaign_helpers',C/'campaign.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    s=importlib.util.spec_from_file_location('v1378_isolation',R/'tools/isolate.py');isolation=importlib.util.module_from_spec(s);s.loader.exec_module(isolation)
    entries=[]
    for name,command in [('backend',isolation.command(C/'backend_check.py',writable=True)),('native',[sys.executable,'-B',str(C/'native.py'),str(C/'ENTRY.json'),'--entry-check']),('producer_json',isolation.command(C/'qualify.py',writable=True)+['--producer']),('output_guard',[sys.executable,'-B',str(C/'qualify.py'),'--guard'])]:
        p=subprocess.run(command,cwd=R,env=m.native_environment(),capture_output=True,text=True,timeout=45);(O/(name+'.console')).write_text(p.stdout+p.stderr);assert p.returncode==0,name+' '+p.stderr[-1200:]
        proof=json.loads(p.stdout.strip().splitlines()[-1]);assert proof['passed'];entries.append(dict(name=name,proof=proof))
    link=RAW/'qualification/readonly_source_link'
    if link.is_symlink():link.unlink()
    assert sources();dump(O/'QUALIFICATION.json',dict(passed=True,checks=checks,entries=entries,declared_envelope_lower_m=lower,current_actual_response_not_yet_qualified=True,models=0,physical_native=0,private_native=0,replay_native=0,tested_source_hashes={str(p.relative_to(R)):sha(p) for p in C.glob('*.py')}))
    print(json.dumps(dict(passed=True,checks=len(checks),entries=len(entries),declared_envelope_lower_m=lower,models=0)))
if __name__=='__main__':
    if '--producer' in sys.argv:producer()
    elif '--guard' in sys.argv:guard()
    else:main()
