"""Real installed FeasibleRPP + original bridge on a nonphysical bicycle peer.

Empty synthetic scans exercise static admission only. Saved causal full-cycle
geometry is separately qualified. These are not fresh physical observations.
"""
import copy
import gzip
import subprocess
import importlib.abc
import json
import math
import socket
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace
import numpy as np

R=Path(__file__).resolve().parents[2]
C=Path(__file__).parent
O=R/'runs/v985_rear_yaw_components'
INDEX=int(sys.argv[1])
ATTEMPT=int(sys.argv[2]) if len(sys.argv)>2 else 1

class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel())
sys.path.insert(0,str(C))
from independent_tracking import check as precise_tracking
import ros_worker
engine=ros_worker.engine
fixture=O/f'case{INDEX}_attempt{ATTEMPT}'
fixture.mkdir(exist_ok=False)
(fixture/'physics').mkdir()
saved=json.loads((R/'runs/v976_saved_recovery_diagnosis/RECOVERY_INPUTS.json').read_text())
plan=json.loads((R/'records/nav2_v977_20261110/ZERO_MODEL_QUALIFICATION.json').read_text())['rows'][INDEX]['plan']
initial=saved['rows'][INDEX]['search_packet']
config=json.loads((C/'A_forward.yaml').read_text())
params=fixture/'PARAMS.json'
params.write_text(json.dumps(config,indent=2)+'\n')
task=copy.deepcopy(json.loads((C/'TASKS.json').read_text())[INDEX])
task.update(output=str(fixture),socket_dir=str(fixture.relative_to(R)),run_id=f'v977-software-{INDEX}',nav2_params=str(params),stage='component',component='RPP_CLOSED_LOOP_HANDOFF',wall_limit_s=40,software_only_fixture=True)
(fixture/'TASK.json').write_text(json.dumps(task,indent=2)+'\n')
engine.authorized=lambda *args:time.time()+100
engine.require_candidate_ready=lambda:None
engine.verify_sources=lambda *args:None
events=[];errors=[];component_rows=[]
with (fixture/'peer.console').open('x')as peer_log:
    producer=subprocess.Popen([sys.executable,'-B',str(C/'software_peer.py'),str(fixture/'TASK.json')],cwd=R,stdout=peer_log,stderr=subprocess.STDOUT)
    ready_until=time.monotonic()+3
    while not(fixture/'PEER_READY').exists():
        assert producer.poll()is None and time.monotonic()<ready_until,'SOFTWARE_PEER_NOT_READY'
        time.sleep(.005)
    try:result=engine.run(task,{},'EXPLICIT_MODEL_FREE_SEPARATE_INTERPRETER_PEER')
    finally:
        try:producer.wait(timeout=3)
        except subprocess.TimeoutExpired:producer.terminate();producer.wait(timeout=2)
peer_result=json.loads((fixture/'PEER_RESULT.json').read_text());errors=peer_result['errors']
with np.load(fixture/'PEER_TRACE.npz')as peer_data:actual=peer_data['body'].copy()
events=json.loads(gzip.decompress((fixture/'PEER_EVENTS.json.gz').read_bytes()))
component_rows=json.loads((fixture/'CLOSED_HANDOFF.json').read_text())['stages'] if (fixture/'CLOSED_HANDOFF.json').exists() else []
if (fixture/'COMPONENT_REFERENCE.json').exists():plan=json.loads((fixture/'COMPONENT_REFERENCE.json').read_text())['proposal']
reference=np.asarray(plan['path'])
maximum_position=maximum_heading=0.
for start in range(0,len(actual),128):
    block=actual[start:start+128];distance=np.linalg.norm(block[:,None,:2]-reference[None,:,:2],axis=2);ix=np.argmin(distance,axis=1)
    maximum_position=max(maximum_position,float(distance[np.arange(len(block)),ix].max()))
    e=block[:,2]-reference[ix,2];maximum_heading=max(maximum_heading,float(abs(np.arctan2(np.sin(e),np.cos(e))).max()))
commands=[x for x in events if x['kind']=='command']
endpoint=float(np.linalg.norm(actual[-1,:2]-reference[-1,:2])) if len(actual)else math.inf
progress=float(np.linalg.norm(actual[0,:2]-plan['original_goal'])-np.linalg.norm(actual[-1,:2]-plan['original_goal']))if len(actual)else 0.
precise=precise_tracking(plan,actual)if len(actual)else dict(passed=False,maximum_position_upper_m=None,maximum_heading_upper_rad=None,error='NO_PEER_MOTION_SEE_ORIGINAL_ROS_RESULT')
checks=dict(real_installed_recovery_RPP_action=result.get('action_status')==4 and len(component_rows)==1,
    original_map_startup_proof=result.get('global_master_readiness',{}).get('passed')is True,
    unchanged_complete_position_envelope=precise['passed']and precise['maximum_position_upper_m']<=.04,
    unchanged_complete_heading_envelope=precise['passed']and precise['maximum_heading_upper_rad']<=.035,
    tighter_endpoint_reached=endpoint<=.02+1e-3,unchanged_actual_progress_gate=progress>=.4,
    no_reverse=bool(commands)and all(x['v']>=0 for x in commands),
    one_ordered_command_channel=all(b['sequence']>a['sequence']for a,b in zip(commands,commands[1:])),
    all_issued_commands_have_original_static_admission=all(x['tube']['passed']and[x['v'],x['w']]==[x['tube']['v'],x['tube']['w']]for x in commands),
    no_native_model_or_peer_failure=not errors,nonempty_peer_motion=len(actual)>=100)
report=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,synthetic_peer=True,
    static_admission_only_in_this_fixture=True,causal_dynamic_geometry_qualified_separately=True,
    physical_tracking_qualified=False,separate_process_peer=peer_result,index=INDEX,maximum_position_error_m=maximum_position,
    maximum_heading_error_rad=maximum_heading,independent_dense_tracking=precise,
    endpoint_distance_m=endpoint,actual_peer_goal_improvement_m=progress,commands=len(commands),
    component=component_rows,result=result,peer_errors=errors,
    shutdown=json.loads((fixture/'DISPATCH_SHUTDOWN.json').read_text()))
(O/f'SOFTWARE_CASE{INDEX}_attempt{ATTEMPT}.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k not in {'result','component'}}),flush=True)
assert report['passed'],'SAVED_STATE_CONTROLLER_SOFTWARE_QUALIFICATION_FAILED'
