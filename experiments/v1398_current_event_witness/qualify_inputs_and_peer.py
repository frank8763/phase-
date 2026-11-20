"""Once-only complete-origin boundary plus real modeled-plugin interface.

Synthetic owner state and translated saved coefficients are explicit fixtures.
No vehicle/model is constructed and no physical/model step is executed.
"""
import copy
import fcntl
import hashlib
import importlib.abc
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import traceback
from types import SimpleNamespace

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','coupled_model','factory','physical','rclpy'}:
            raise AssertionError('NO_MODEL_INPUT_PEER_QUALIFICATION:'+name)
sys.meta_path.insert(0,NoModel())
from origin_binding import bind,event,field,exact
from mode_memory import ModeMemory
acquisition=exact('v1398_prior_readonly_acquisition',R/'experiments/v1397_event_handoff_integration/native_event_frame.py')
io=exact('v1398_producer_json',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')
peer=exact('v1398_production_modeled_peer',C/'modeled_peer.py')


def main():
    os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));os.chdir(R)
    O.mkdir(exist_ok=True);claim=O/'INPUT_PEER_QUALIFICATION_CLAIM.json'
    assert not claim.exists(), 'CURRENT_INPUT_PEER_QUALIFICATION_ALREADY_CLAIMED'
    with (R/'runs/v648_static_unknown/execution.lock').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text());assert parent['active_round'] is None and not parent['models_now_authorized']
    assert time.time()<1795395600
    io.atomic(claim,dict(started_unix=time.time(),models=0,one_production_peer_attempt=True,synthetic_fixture_not_actual_state=True))
    out=O/'peer_qualification';out.mkdir(exist_ok=False);job=None;sock=None;log=None
    result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,
                fixture_not_new_measured_state=True,physical_admission=False,complete_model_backend_qualified=False)
    try:
        negatives=[]
        def reject(name,call):
            try:call()
            except (AssertionError,ValueError,RuntimeError,KeyError):negatives.append(name)
            else:raise AssertionError('INPUT_NEGATIVE_ACCEPTED:'+name)
        mode=ModeMemory(canonical_native=0,coupled_episode=False,steering_motion_active=False)
        mode.applied(before_native=0,v=0.,w=0.,parked_target=-.2,steering_motion_active_after=True)
        assert mode.snapshot(1)['coupled_episode'] and mode.snapshot(1)['steering_motion_active']
        mode.applied(before_native=1,v=0.,w=0.,parked_target=None,steering_motion_active_after=False)
        assert mode.snapshot(2)['coupled_episode'] and not mode.snapshot(2)['steering_motion_active']
        mode.applied(before_native=2,v=.1,w=0.,parked_target=None,steering_motion_active_after=False)
        assert not mode.snapshot(3)['coupled_episode']
        reject('missing_canonical_mode_history',lambda:ModeMemory(canonical_native=2,coupled_episode=False,steering_motion_active=False))
        reject('mode_history_gap',lambda:mode.applied(before_native=4,v=0.,w=0.,parked_target=None,steering_motion_active_after=False))
        reject('parked_drive',lambda:mode.applied(before_native=3,v=.1,w=0.,parked_target=-.2,steering_motion_active_after=True))
        reject('active_without_parked_mode',lambda:mode.applied(before_native=3,v=0.,w=0.,parked_target=None,steering_motion_active_after=True))
        saved=json.loads((R/'runs/v1393_full9390_preparation/FIXED_INPUTS.json').read_text())
        body=copy.deepcopy(saved['observed_packet']['body'])
        class Vector(list):
            def tolist(self):return list(self)
        class Vehicle:
            count=300
            d=SimpleNamespace(time=3.,qpos=Vector(body[:3]),qvel=Vector([0.,0.,0.]),ctrl=Vector([0.,0.,0.,0.]),mocap_pos=Vector([]),mocap_quat=Vector([]))
            adapter=SimpleNamespace(last=Vector([0.,0.,0.,0.]),integral=0.,parked_target=None,_steering_motion_active=False)
            def body(self):return body[:]
            def steering_sample(self):return Vector([0.,0.,0.,0.])
            def scan(self):return dict(native_tick=self.count,time=self.d.time,xy=body[:2],yaw=body[2],ranges=[3.]*32)
        vehicle=Vehicle();gear=SimpleNamespace(gear=1,brake_start=None,last_tick=299)
        history=ModeMemory(canonical_native=0,coupled_episode=False,steering_motion_active=False)
        for i in range(300):history.applied(before_native=i,v=0.,w=0.,parked_target=None,steering_motion_active_after=False)
        clock=lambda:100.
        measured=acquisition.acquire(vehicle,event.frames.SampleCache(clock=clock),gear,run_id='v1398-software-fixture',sequence=0,now=clock)
        source=json.loads((R/'runs/v858_nav2_verified/v1370/rpp_default_horizon_m1_s01_main/CAUSAL_PREDICTION_MODEL.json').read_text())
        # Deliberate timestamp translation is fixture-only, never production.
        source['periodic']['source_tick']=200;source['periodic']['last']=2.;source['last_observed_time']=2.
        forecast=field.all_future(source,current_native=300,current_sim_time=3.)
        segment=copy.deepcopy(saved['original_target_segment'])
        rear=[body[0]-.3*__import__('math').cos(body[2]),body[1]-.3*__import__('math').sin(body[2]),body[2]]
        math=__import__('math');first=segment['poses'][0]
        geometry=dict(start_distance_m=math.dist(rear[:2],first[:2]),start_heading_rad=abs(math.atan2(math.sin(rear[2]-first[2]),math.cos(rear[2]-first[2]))),minimum_clearance_m=.21)
        request=event.make_request(measured,segment,geometry,forecast,run_id='v1398-software-fixture',event_index=0,brake_start=0,now=100.)
        current=bind(vehicle,request,history,source,gear=gear,now=100.)
        assert current['origin']['body_lateral']==0. and current['origin']['coupled_episode'] is False
        assert current['origin']['native_tick']==300 and current['gear_memory']['last_tick']==299
        wrong=copy.deepcopy(source);wrong['periodic']['vertices'][0][0][0]+=.001
        reject('changed_coefficient_same_tick',lambda:bind(vehicle,request,history,wrong,gear=gear,now=100.))
        reject('old_full_state_frame',lambda:bind(vehicle,request,history,source,gear=gear,now=100.201))
        original_root=vehicle.d.qpos[0];vehicle.d.qpos[0]=original_root+.001
        reject('changed_root_state',lambda:bind(vehicle,request,history,source,gear=gear,now=100.))
        vehicle.d.qpos[0]=original_root
        changed_gear=SimpleNamespace(gear=-1,brake_start=None,last_tick=299)
        reject('changed_owner_gear',lambda:bind(vehicle,request,history,source,gear=changed_gear,now=100.))
        vehicle.adapter._steering_motion_active=True
        reject('changed_owner_mode',lambda:bind(vehicle,request,history,source,gear=gear,now=100.))
        vehicle.adapter._steering_motion_active=False
        run_id='v1398-modeled-peer-interface-only';sequence=0;sent={}
        io.atomic(out/'CURRENT_INPUT.json',current)
        def packet():
            nonlocal sequence
            value=dict(kind='MODELED_BODY_CAUSAL_MAP_NOT_SENSOR',run_id=run_id,sequence=sequence,native_tick=300,body=body[:],sent_monotonic=time.monotonic(),input_sha256=current['input_sha256'])
            sent[sequence]=value;sequence+=1;return value
        first=packet();peer.validate_request(first,run_id,-1,input_sha256=current['input_sha256'],origin_native=300)
        for name,change in [('unbound_input',dict(input_sha256='0'*64)),('actual_frame_in_modeled_peer',dict(kind='ACTUAL_FRAME')),('before_event_origin',dict(native_tick=299))]:
            reject(name,lambda change=change:peer.validate_request(dict(first,**change),run_id,-1,input_sha256=current['input_sha256'],origin_native=300))
        helper=exact('v1398_qualified_ros_environment',R/'experiments/v1396_rpp_rpc_retirement/peer_environment.py');ros,environment=helper.environment(out)
        entry=ros.command(['taskset','-c','3','/usr/bin/python3.12','-B',str(C/'modeled_peer.py'),str(out),run_id,'--entry-check'])
        p=subprocess.run(entry,cwd=R,env=environment,capture_output=True,text=True,timeout=30);(out/'entry.console').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr[-1200:]
        sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);address=str((out/'owner.sock').relative_to(R));sock.bind(address);sock.settimeout(.02)
        log=(out/'peer.console').open('x');job=subprocess.Popen(ros.command(['taskset','-c','3','/usr/bin/python3.12','-B',str(C/'modeled_peer.py'),str(out),run_id]),cwd=R,env=environment,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        target=str((out/'peer.sock').relative_to(R));until=time.monotonic()+10
        while not Path(target).exists():assert job.poll() is None and time.monotonic()<until;time.sleep(.02)
        replies=[];until=time.monotonic()+55;next_send=0.
        while len(replies)<2:
            assert job.poll() is None and time.monotonic()<until,'CURRENT_EVENT_REAL_PLUGIN_CALLBACK_TIMEOUT'
            if time.monotonic()>=next_send:sock.sendto(json.dumps(packet(),allow_nan=False).encode(),target);next_send=time.monotonic()+.05
            try:reply=json.loads(sock.recv(65536))
            except socket.timeout:continue
            assert reply['kind']=='ORIGINAL_RPP_MODELED_COMMAND' and reply['sequence'] in sent
            assert reply['input_sha256']==current['input_sha256'] and reply['native_tick']==300 and reply['body']==body and reply['not_measured_response']
            assert reply['command_ros_ns']>=reply['first_tf_ros_ns'] and 0<=time.monotonic()-reply['origin']['generated_monotonic']<=.2
            replies.append(reply)
        sock.sendto(json.dumps(dict(kind='STOP',run_id=run_id)).encode(),target);job.wait(timeout=10)
        proof=json.loads((out/'PEER_RESULT.json').read_text());assert job.returncode==0 and proof['passed'] and proof['synthetic_scan_messages']==0 and proof['controller_exited']
        result.update(passed=True,mode_transition_cases=3,negative_cases=negatives,full_origin_readonly_binding=True,real_original_plugin_callback=True,modeled_native_origin_without_saved_tick=300,no_synthetic_scan_publisher=True,replies=replies,peer_result=proof)
    except BaseException as exc:
        result.update(error=repr(exc),traceback=traceback.format_exc())
    finally:
        if job is not None and job.poll() is None:
            os.killpg(job.pid,signal.SIGTERM)
            try:job.wait(timeout=8)
            except subprocess.TimeoutExpired:os.killpg(job.pid,signal.SIGKILL);job.wait(timeout=3)
        if sock is not None:sock.close();(out/'owner.sock').unlink(missing_ok=True)
        if log is not None:log.close()
        result.update(closed=True,closed_unix=time.time());io.atomic(O/'INPUT_PEER_QUALIFICATION.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['traceback','replies','peer_result']}))
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
