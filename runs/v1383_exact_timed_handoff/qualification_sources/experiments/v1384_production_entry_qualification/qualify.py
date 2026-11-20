"""Saved-state/controller/geometry/serializer/complete CLI qualification."""
import ast
import importlib.abc
import importlib.util
import math
import os
import subprocess
import sys
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parents[2]/'experiments/v1383_exact_timed_handoff'))
from component_context import *
class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','physical','factory','rclpy'}:raise AssertionError('NO_PHYSICAL_QUALIFICATION '+name)
def producer():
    sys.meta_path.insert(0,NoPhysical());from audit import audit
    import numpy as np
    value=read(R/'runs/v858_nav2_verified/v1378/steering_response/FINAL_INDEPENDENT_AUDIT.json');value['fixture']=dict(ok=np.bool_(True),bad=np.bool_(False),ulp=np.nextafter(np.float64(1),np.float64(2)))
    p=O/'PRODUCER_JSON_FIXTURE.json';dump(p,value);assert read(p)==value and read(p)['fixture']['bad'] is False
    print(json.dumps(dict(passed=True,whole_actual_audit_roundtrip=True,models=0)))
def guard():
    s=importlib.util.spec_from_file_location('timed_original_output_guard',R/'experiments/v1372_coherent_sampling_fault/qualify_output.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.RAW=RAW;m.child()
def main():
    sys.meta_path.insert(0,NoPhysical());import numpy as np
    from controller import Capture
    from gear_handoff import GearHandoff
    from geometry_contract import Geometry,membership,rear
    task=read(C/'TASKS.json')[0];task_check(task);plan=read(R/task['response_reference_file']);prior=Path(task['prior_raw']);rows=read(prior/'APPLIED_JOURNAL.json');final=read(prior/'FINAL_PACKET.json');setup=read(prior/'physics/SETUP.json')
    assert len(rows)==32600 and final['body']==task['origin_body'] and final['controller_memory']['last_ctrl']==task['origin_memory']
    checks={'exact_saved32600_and_original32200':True};gate=GearHandoff()
    for row in rows:
        v,w,p=gate.select(*row['upstream_request'][:2],native_tick=row['before_native'],body=row['body'],last_ctrl=row['last_ctrl'],encoders=row['encoders']);assert row['request']==[v,w,False] and p==row['gear_handoff']
    assert gate.gear==1;checks['full_saved_gear_metadata_exact']=True
    selector=Capture(task);zero_start=None;request=None
    for i,row in enumerate(plan['predicted_schedule']):
        tick=32600+i;s=plan['predicted_states'][i];body=[s[0],s[1],s[2],s[3],s[5]];memory=plan['predicted_memory'][i];enc=[0.,0.,0.,0.]
        if i%5==0 and zero_start is None:
            v,w,state=selector.select(body,tick,enc,memory[:4]);request=[v,w]
            if state['phase']=='RESPONSE_COMPLETE':zero_start=tick
        if zero_start is not None:request=[0.,0.]
        v,w,p=gate.select(*request,native_tick=tick,body=body,last_ctrl=memory[:4],encoders=enc)
        assert request==row['request'] and [v,w]==row['admitted'];selector.observe_gear(tick,p)
    assert len(plan['predicted_schedule'])==935 and zero_start is not None and 32600+935-zero_start==200 and selector.release_tick==32800
    checks['actual_callback_release_request_clock_and200tail_equivalent']=True
    geometry=Geometry(setup['known'],read(R/task['causal_model_file']));lower=geometry.tube(plan['predicted_states'],32600);assert lower>=.22 and abs(lower-read(R/'runs/v1379_timed_response_preparation/BRAKING_WITNESS.json')['nominal_tube_lower_m'])<=1e-8
    checks['full_response_geometry_matches_braking_qualification']=True
    # Complete corner support extrema checked against dense independent points.
    normals=np.c_[np.cos(np.arange(64)*math.tau/64),np.sin(np.arange(64)*math.tau/64)];maximum_violation=0.
    for yaw in [plan['predicted_states'][i][2] for i in range(0,936,31)]:
        for x,y in [(-.14,-.375),(-.14,.375),(.74,-.375),(.74,.375)]:
            X=x*math.cos(yaw)-y*math.sin(yaw);Y=x*math.sin(yaw)+y*math.cos(yaw);A=X*normals[:,0]+Y*normals[:,1];B=-Y*normals[:,0]+X*normals[:,1];bound=np.where(abs(np.arctan2(B,A))<=.1,np.hypot(A,B),A*math.cos(.1)+abs(B)*math.sin(.1))
            for angle in np.linspace(-.1,.1,201):
                sampled=A*math.cos(angle)+B*math.sin(angle);maximum_violation=max(maximum_violation,float((sampled-bound).max()))
    assert maximum_violation<=1e-10;checks['continuous_full_footprint_corner_support_bound']=True
    rejected=[]
    for label,body,tick in [('position',list(final['body']),32600),('yaw',list(final['body']),32600),('time',list(final['body']),33000)]:
        if label=='position':body[0]+=.1
        if label=='yaw':body[2]+=.3
        try:membership(body,tick,plan['predicted_states'])
        except AssertionError:rejected.append(label)
        else:raise AssertionError('BAD_RESPONSE_ACCEPTED '+label)
    try:authorize(task,{})
    except (AssertionError,FileNotFoundError):rejected.append('disabled_model_authority')
    else:raise AssertionError('UNAUTHORIZED_MODEL_ACCEPTED')
    checks['bad_response_and_no_authority_refused']=True
    from campaign import native_environment
    s=importlib.util.spec_from_file_location('timed_complete_isolation',R/'tools/isolate.py');isolation=importlib.util.module_from_spec(s);s.loader.exec_module(isolation)
    entries=[]
    for label,command in [('backend',isolation.command(C/'backend_check.py',writable=True)),('native',[sys.executable,'-B',str(C/'native.py'),str(C/'ENTRY.json'),'--entry-check']),('producer',isolation.command(C/'qualify.py',writable=True)+['--producer']),('guard',[sys.executable,'-B',str(C/'qualify.py'),'--guard'])]:
        p=subprocess.run(['taskset','-c','2',*command],cwd=R,env=native_environment(),capture_output=True,text=True,timeout=60);(O/(label+'.console')).write_text(p.stdout+p.stderr);assert p.returncode==0,label+' '+p.stderr[-2000:];proof=json.loads(p.stdout.strip().splitlines()[-1]);assert proof['passed'];entries.append(dict(label=label,proof=proof))
        if label=='native':
            assert len(proof['production_callable_sources'])==9
            assert all(path.startswith(str(C.relative_to(R))+'/') for path in proof['production_callable_sources'].values())
            checks['exact_production_callable_sources']=True
    link=RAW/'qualification/readonly_source_link'
    if link.is_symlink():link.unlink()
    assert sources();dump(O/'QUALIFICATION.json',dict(passed=True,checks=checks,negative_cases=rejected,entries=entries,full_tube_lower_m=lower,maximum_support_bound_violation_m=maximum_violation,models=0,analytical_native=0,physical_native=0,tested_source_hashes={str(p.relative_to(R)):sha(p) for p in [*C.glob('*.py'),*Path(__file__).resolve().parent.glob('*')] if p.is_file()}));print(json.dumps(dict(passed=True,checks=len(checks),entries=len(entries),models=0,physical_native=0)))
if __name__=='__main__':
    if '--producer' in sys.argv:producer()
    elif '--guard' in sys.argv:guard()
    else:main()
