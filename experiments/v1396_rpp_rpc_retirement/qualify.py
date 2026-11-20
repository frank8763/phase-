"""Saved prefix, fixed response, actual peer, production CLI/JSON/guard gates."""
import ast
import importlib.abc
import importlib.util
import os
import subprocess
import sys
from component_context import *
class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','factory','physical','rclpy'}:raise AssertionError('ZERO_MODEL_QUALIFICATION '+name)
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def producer():
    sys.meta_path.insert(0,NoPhysical());from audit import audit
    import numpy as np
    value=read(Path(read(C/'ENTRY.json')['prior_raw'])/'FINAL_INDEPENDENT_AUDIT.json');value['fixture']=dict(ok=np.bool_(True),bad=np.bool_(False),ulp=np.nextafter(np.float64(1),np.float64(2)))
    p=O/'PRODUCER_JSON_FIXTURE.json';dump(p,value);assert read(p)==value and read(p)['fixture']['bad'] is False
    print(json.dumps(dict(passed=True,full_actual_producer_JSON_roundtrip=True,models=0)))
def guard():
    source=R/'experiments/v1372_coherent_sampling_fault/qualify_output.py';m=load('original_qualified_raw_guard',source);m.RAW=RAW;m.child()
def main():
    sys.meta_path.insert(0,NoPhysical());import numpy as np
    from gear_handoff import GearHandoff
    from geometry_contract import Geometry,membership,errors
    task=read(C/'ENTRY.json');task_check(task);prior=Path(task['prior_raw']);rows=read(prior/'APPLIED_JOURNAL.json');packet=read(prior/'FINAL_PACKET.json');assert len(rows)==10775==packet['native_tick'] and packet['body']==task['origin_body'] and packet['controller_memory']['last_ctrl']==task['origin_memory']
    assert read(prior/'FINAL_INDEPENDENT_AUDIT.json')['passed'];gate=GearHandoff()
    for row in rows:
        v,w,proof=gate.select(*row['upstream_request'][:2],native_tick=row['before_native'],body=row['body'],last_ctrl=row['last_ctrl'],encoders=row['encoders']);assert [v,w,False]==row['request'] and proof==row['gear_handoff']
    assert gate.gear==1 and any(row['parked_target'] is not None for row in rows)
    with np.load(R/task['response_reference_file']) as z:states=z['states'].copy();controls=z['ctrl'].copy()
    assert len(states)==len(controls)+1==2576 and np.max(abs(states[0,:4]-np.array(packet['body'][:4])))<=1e-8
    journal=read(R/'runs/v1393_full9390_preparation/PREDICTED_JOURNAL.json');assert len(journal)==2575 and all(x['zero_tail'] and x['admitted']==[0.,0.] for x in journal[-200:])
    geometry=Geometry(read(prior/'physics/SETUP.json')['known'],task['causal_all_future_ball']);lower=geometry.tube(states);assert lower>=.22 and abs(lower-.2320689792491846)<=1e-8
    previous=0
    for i,s in enumerate(states):
        proof=membership([s[0],s[1],s[2],s[3],s[5]],10775+i,states,previous);previous=proof['reference_index'];assert proof['rear_error_m']<=1e-8 and proof['time_error_s']==0.
    bad=[]
    for name,body,tick in [('position',[packet['body'][0]+.1,*packet['body'][1:]],10775),('yaw',[*packet['body'][:2],packet['body'][2]+.3,*packet['body'][3:]],10775),('time',packet['body'],11200)]:
        try:membership(body,tick,states)
        except AssertionError:bad.append(name)
        else:raise AssertionError('BAD_FIXED_RESPONSE_ACCEPTED '+name)
    assert read(O/'peer_qualification/QUALIFICATION.json')['passed'] and read(O/'peer_qualification/QUALIFICATION.json')['not_new_sensor_acquisition']
    from campaign import native_environment
    isolation=load('original_isolated_backend',R/'tools/isolate.py');entries=[]
    for label,command in [('backend',isolation.command(C/'backend_check.py',writable=True)),('native',[sys.executable,'-B',str(C/'native.py'),str(C/'ENTRY.json'),'--entry-check']),('producer',isolation.command(C/'qualify.py',writable=True)+['--producer']),('guard',[sys.executable,'-B',str(C/'qualify.py'),'--guard'])]:
        p=subprocess.run(['taskset','-c','2',*command],cwd=R,env=native_environment(),capture_output=True,text=True,timeout=60);(O/(label+'.console')).write_text(p.stdout+p.stderr);assert p.returncode==0,label+' '+p.stderr[-2200:];proof=json.loads(p.stdout.strip().splitlines()[-1]);assert proof['passed'];entries.append(dict(label=label,proof=proof))
    link=RAW/'qualification/readonly_source_link'
    if link.is_symlink():link.unlink()
    assert sources();proof=dict(passed=True,models=0,analytical_native=0,physical_native=0,saved_prefix_gear_rows=len(rows),parked_source_metadata_preserved=True,original_fixed_response_native=2575,complete200_reference_zero_tail=True,full_reference_membership_points=len(states),full_response_tube_lower_m=lower,negative_cases=bad,actual_peer_saved_frame_interface_qualified=True,saved_frame_playback_not_new_acquisition=True,entries=entries,tested_source_hashes={str(p.relative_to(R)):sha(p) for p in C.iterdir() if p.is_file() and p.name!='SOURCE_FREEZE.json'})
    dump(O/'QUALIFICATION.json',proof);print(json.dumps(dict(passed=True,saved_gear_rows=len(rows),response_points=len(states),complete_entries=len(entries),models=0)))
if __name__=='__main__':
    if '--producer' in sys.argv:producer()
    elif '--guard' in sys.argv:guard()
    else:main()
