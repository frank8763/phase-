"""Real installed FeasibleRPP + original bridge on a nonphysical bicycle peer.

Empty synthetic scans exercise static admission only. Saved causal full-cycle
geometry is separately qualified. These are not fresh physical observations.
"""
import copy
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
O=R/'runs/v977_state_consistent_recovery'
INDEX=int(sys.argv[1])
ATTEMPT=int(sys.argv[2]) if len(sys.argv)>2 else 1

class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory'}:
            raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel())
sys.path.insert(0,str(C))
import ros_worker
engine=ros_worker.engine
fixture=O/f'case{INDEX}_attempt{ATTEMPT}'
fixture.mkdir(exist_ok=False)
(fixture/'physics').mkdir()
saved=json.loads((R/'runs/v976_saved_recovery_diagnosis/RECOVERY_INPUTS.json').read_text())
plan=json.loads((O/'ZERO_MODEL_QUALIFICATION.json').read_text())['rows'][INDEX]['plan']
initial=saved['rows'][INDEX]['search_packet']
config=json.loads((C/'A_forward.yaml').read_text())
params=fixture/'PARAMS.json'
params.write_text(json.dumps(config,indent=2)+'\n')
task=copy.deepcopy(json.loads((R/'experiments/v974_daytime_binding_gate/TASKS.json').read_text())[0])
task.update(output=str(fixture),socket_dir=str(fixture.relative_to(R)),run_id=f'v977-software-{INDEX}',nav2_params=str(params),stage='component',component='RPP_CLOSED_LOOP_HANDOFF',wall_limit_s=40)
engine.authorized=lambda *args:time.time()+100
engine.require_candidate_ready=lambda:None
engine.verify_sources=lambda *args:None
events=[];states=[];errors=[];component_rows=[]
done=threading.Event()
peer=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
address=fixture/'physics.sock'
peer.bind(str(address.relative_to(R)));peer.settimeout(.001)

def serve():
    phase='WAITING';pose=np.asarray(initial['body'][:3],float);tick=0;v=w=0.;last=0.;target=time.monotonic();last_sent=0.
    held=initial['steering']['position']
    try:
        while not done.is_set():
            for _ in range(16):
                try:message=json.loads(peer.recv(65536));events.append(message)
                except socket.timeout:break
                if message['kind']=='arm':phase='RUNNING';target=time.monotonic()
                elif message['kind']=='command':v,w=message['v'],message['w'];last=message['issued_at']
                elif message['kind']=='stop':return
            now=time.monotonic()
            if phase=='RUNNING' and now>=target:
                if now-last>.2:v=w=0.
                a=pose[2];b=a+w*.01
                if abs(w)<1e-10:pose[:2]+=v*.01*np.array([math.cos(a),math.sin(a)])
                else:pose[:2]+=[v/w*(math.sin(b)-math.sin(a)),-v/w*(math.cos(b)-math.cos(a))]
                pose[2]=b;tick+=1;target+=.01
            if abs(v)>=.005:
                k=w/v;held=[math.atan(.6*k/(1-.27*k)),math.atan(.6*k/(1+.27*k))]
            packet=dict(kind='observation',run_id=task['run_id'],phase=phase,native_tick=tick,sim_time=tick*.01,
                sent_at=now,body_measured_at=now,scan_measured_at=now,initial_snapshot=phase=='WAITING',body=[*pose,v,w],
                steering=dict(native_tick=tick,measured_at=now,position=list(held),velocity=[0.,0.]),
                scan=dict(native_tick=tick,time=tick*.01,xy=pose[:2].tolist(),yaw=float(pose[2]),ranges=[3.]*32))
            if now-last_sent>=(.02 if phase=='WAITING'else .01):
                try:peer.sendto(json.dumps(packet).encode(),str((fixture/'ros.sock').relative_to(R)))
                except(FileNotFoundError,ConnectionRefusedError,socket.timeout):pass
                states.append(packet);last_sent=now
            time.sleep(.001)
    except BaseException as error:errors.append(repr(error))

def component_run(node,until,deadline,spin,wait,require,check_servers):
    sys.path.insert(0,str(C))
    from transaction import TrackingGuard,fingerprint
    from binding import FollowPathBinding
    binding=FollowPathBinding(node)
    wait(node,binding.client.server_is_ready,min(until,time.monotonic()+2),'FOLLOW_SERVER_TIMEOUT')
    node.forward.reference(plan['path'])
    node.committed_recovery=TrackingGuard(plan)
    event=dict(action='SEND_FOLLOW_PATH_ONCE',controller_id='RecoveryFollowPath',goal_checker_id='recovery_goal_checker',path=plan['path'],path_sha256=fingerprint(plan['path']))
    accepted=binding.send(event)
    wait(node,accepted.done,min(until,time.monotonic()+2),'FOLLOW_ACCEPT_TIMEOUT')
    handle=accepted.result();require(handle.accepted,'FOLLOW_REJECTED')
    node.committed_recovery.mode='FOLLOW_RECOVERY'
    result=handle.get_result_async()
    while not result.done():
        spin(node,timeout_sec=.005);check_servers();require(node.guard_failure is None,'COMMAND_CONTRACT_FAILURE '+str(node.guard_failure));require(time.monotonic()<until,'SOFTWARE_COMPONENT_TIMEOUT')
    status=result.result().status
    node.committed_recovery.mode='STOPPED_REPLAN'
    settled=time.monotonic()+.6
    while time.monotonic()<settled:spin(node,timeout_sec=.005)
    component_rows.append(dict(controller_id=event['controller_id'],goal_checker=event['goal_checker_id'],status=status,normal_navigation_action_sent=False,follow_actions_sent=1,end_packet=node.latest,production_bridge_source=str(Path(engine.__file__).relative_to(R)),production_binding_source=str(Path(sys.modules['binding'].__file__).relative_to(R))))
    return SimpleNamespace(status=status,result=SimpleNamespace(error_code=0)),component_rows

sys.modules['closed_handoff']=SimpleNamespace(run=component_run)
thread=threading.Thread(target=serve);thread.start()
try:result=engine.run(task,{},'EXPLICIT_MODEL_FREE_V977_CONTROLLER_FIXTURE')
finally:done.set();thread.join(3);peer.close();address.unlink(missing_ok=True)
reference=np.asarray(plan['path']);actual=np.asarray([x['body'][:3]for x in states if x['phase']=='RUNNING']).reshape(-1,3)
np.savez_compressed(fixture/'PEER_TRACE.npz',body=actual,reference=reference,
                    native_tick=np.asarray([x['native_tick']for x in states if x['phase']=='RUNNING'],dtype=np.int64))
maximum_position=maximum_heading=0.
for start in range(0,len(actual),128):
    block=actual[start:start+128];distance=np.linalg.norm(block[:,None,:2]-reference[None,:,:2],axis=2);ix=np.argmin(distance,axis=1)
    maximum_position=max(maximum_position,float(distance[np.arange(len(block)),ix].max()))
    e=block[:,2]-reference[ix,2];maximum_heading=max(maximum_heading,float(abs(np.arctan2(np.sin(e),np.cos(e))).max()))
commands=[x for x in events if x['kind']=='command']
endpoint=float(np.linalg.norm(actual[-1,:2]-reference[-1,:2])) if len(actual)else math.inf
progress=float(np.linalg.norm(actual[0,:2]-plan['original_goal'])-np.linalg.norm(actual[-1,:2]-plan['original_goal']))if len(actual)else 0.
checks=dict(real_installed_recovery_RPP_action=result.get('action_status')==4 and len(component_rows)==1,
    original_map_startup_proof=result.get('global_master_readiness',{}).get('passed')is True,
    unchanged_complete_position_envelope=maximum_position<=.04,
    unchanged_complete_heading_envelope=maximum_heading+.758770385*.00625<=.035,
    tighter_endpoint_reached=endpoint<=.02+1e-3,unchanged_actual_progress_gate=progress>=.4,
    no_reverse=bool(commands)and all(x['v']>=0 for x in commands),
    one_ordered_command_channel=all(b['sequence']>a['sequence']for a,b in zip(commands,commands[1:])),
    all_issued_commands_have_original_static_admission=all(x['tube']['passed']and[x['v'],x['w']]==[x['tube']['v'],x['tube']['w']]for x in commands),
    no_native_model_or_peer_failure=not errors,nonempty_peer_motion=len(actual)>=100)
report=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,synthetic_peer=True,
    static_admission_only_in_this_fixture=True,causal_dynamic_geometry_qualified_separately=True,
    physical_tracking_qualified=False,index=INDEX,maximum_position_error_m=maximum_position,
    maximum_heading_error_rad=maximum_heading,conservative_reference_sampling_heading_allowance_rad=.758770385*.00625,
    endpoint_distance_m=endpoint,actual_peer_goal_improvement_m=progress,commands=len(commands),
    component=component_rows,result=result,peer_errors=errors,
    shutdown=json.loads((fixture/'DISPATCH_SHUTDOWN.json').read_text()))
(O/f'SOFTWARE_CASE{INDEX}_attempt{ATTEMPT}.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k not in {'result','component'}}),flush=True)
assert report['passed'],'SAVED_STATE_CONTROLLER_SOFTWARE_QUALIFICATION_FAILED'
