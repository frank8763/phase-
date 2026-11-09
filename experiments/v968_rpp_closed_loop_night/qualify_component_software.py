"""Full installed RPP two-action software seam, explicit nonphysical kinematic peer."""
import copy
import importlib.abc
import json
import math
import socket
import sys
import threading
import time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v968_rpp_closed_loop_night'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in{'mujoco','torch','vehicle','physical','factory'}:raise AssertionError('MODEL_IMPORT_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
import ros_worker
engine=ros_worker.engine
out=R/'runs/v968_component_software_fixture03';out.mkdir(exist_ok=False);(out/'physics').mkdir()
task=copy.deepcopy(json.loads((C/'TASKS.json').read_text())[0]);task.update(output=str(out),socket_dir=str(out.relative_to(R)),run_id='v968-component-software-fixture')
engine.authorized=lambda *args:time.time()+110
engine.require_candidate_ready=lambda:None
engine.verify_sources=lambda *args:None
peer=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);address=Path(task['socket_dir'])/'physics.sock';peer.bind(str(address));peer.settimeout(.001)
done=threading.Event();events=[];states=[];failure=[]
def serve():
    phase='WAITING';pose=np.array([-4.,-2.,0.]);tick=0;velocity=angular=0.;last=0.;target=time.monotonic();last_sent=0.
    try:
        while not done.is_set():
            for _ in range(16):
                try:packet=json.loads(peer.recv(65536));events.append(packet)
                except socket.timeout:break
                if packet['kind']=='arm':phase='RUNNING';target=time.monotonic()
                elif packet['kind']=='command':velocity=packet['v'];angular=packet['w'];last=packet['issued_at']
                elif packet['kind']=='stop':return
            now=time.monotonic()
            if phase=='RUNNING'and now>=target:
                if now-last>.2:velocity=angular=0.
                a=pose[2];b=a+angular*.01
                if abs(angular)<1e-10:pose[:2]+=velocity*.01*np.array([math.cos(a),math.sin(a)])
                else:pose[:2]+=[velocity/angular*(math.sin(b)-math.sin(a)),-velocity/angular*(math.cos(b)-math.cos(a))]
                pose[2]=b;tick+=1;target+=.01
            k=0. if abs(velocity)<.005 else angular/velocity
            enc=[math.atan(.6*k/(1-.27*k)),math.atan(.6*k/(1+.27*k))]
            # Hold last steering during synthetic stop as production adapter does.
            if abs(velocity)<.005:enc=states[-1]['steering']['position']if states else[0.,0.]
            packet=dict(kind='observation',run_id=task['run_id'],phase=phase,native_tick=tick,sim_time=tick*.01,
                sent_at=now,body_measured_at=now,scan_measured_at=now,initial_snapshot=phase=='WAITING',
                body=[*pose,velocity,angular],steering=dict(native_tick=tick,measured_at=now,position=enc,velocity=[0.,0.]),
                scan=dict(native_tick=tick,time=tick*.01,xy=pose[:2].tolist(),yaw=float(pose[2]),ranges=[3.]*32))
            if now-last_sent>=(.02 if phase=='WAITING'else .01):
                try:peer.sendto(json.dumps(packet).encode(),str(Path(task['socket_dir'])/'ros.sock'))
                except(FileNotFoundError,ConnectionRefusedError,socket.timeout):pass
                last_sent=now
            states.append(packet);time.sleep(.001)
    except BaseException as e:failure.append(repr(e))
thread=threading.Thread(target=serve);thread.start()
try:result=engine.run(task,{},'EXPLICIT_ZERO_MODEL_KINEMATIC_SOFTWARE_FIXTURE')
finally:done.set();thread.join(3);peer.close();address.unlink(missing_ok=True)
stages=json.loads((out/'CLOSED_HANDOFF.json').read_text())['stages']if(out/'CLOSED_HANDOFF.json').exists()else[]
commands=[e for e in events if e['kind']=='command']
checks=dict(actual_installed_RPP_both_actions=result.get('action_status')==4 and len(stages)==2,
    original_startup_map_proof=result.get('global_master_readiness',{}).get('passed')is True,
    actual_production_component_no_exception=result.get('passed')is True and not failure,
    actual_forward_requests=bool(commands)and any(e['v']>.05 for e in commands)and all(e['v']>=0 for e in commands),
    all_issued_commands_have_original_certificates=all(e['tube']['passed']and[e['v'],e['w']]==[e['tube']['v'],e['tube']['w']]for e in commands),
    held_steering_exercised=len(stages)==2 and max(map(abs,stages[0]['end_packet']['steering']['position']))>=.2)
report=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,synthetic_peer=True,physical_qualification=False,
    result=result,peer_errors=failure,commands=len(commands),scope='Real installed Nav2/RPP two-action and actual bridge-shaping/admission software; kinematic peer states are NOT physical evidence.')
(O/'FULL_COMPONENT_SOFTWARE_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=report['passed'],checks=checks,error=result.get('error'),commands=len(commands))));assert report['passed']
