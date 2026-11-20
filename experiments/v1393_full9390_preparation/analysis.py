"""Bounded original-RPP analytical response and every-native braking witness."""
import argparse
import ast
import copy
import fcntl
import hashlib
import importlib.abc
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import socket
import sys
import time
import traceback

R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
class NoPhysical(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0] in {'mujoco','vehicle','torch','factory','physical','rclpy'}:raise AssertionError('NO_PHYSICAL_ANALYSIS '+name)
sys.meta_path.insert(0,NoPhysical())
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
io=load('analytical_json_boundary',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')
Geometry=load('analytical_full_footprint',C/'geometry.py').Geometry
GearHandoff=load('analytical_original_gear',R/'experiments/v1346_measured_gear_handoff/gear_handoff.py').GearHandoff

def guard():
    source=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';tree=ast.parse(source.read_text());node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='write_guard')
    namespace=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),namespace);sys.addaudithook(namespace['write_guard'])

def binding():
    sys.path.insert(0,str(R/'experiments/v1114_coupled_steering_mode'))
    from logic import Predictor,initial,kernel,Adapter
    assert Path(Predictor.step.__code__.co_filename).resolve()==R/'experiments/v1114_coupled_steering_mode/coupled_model.py'
    assert Path(Adapter.compute.__code__.co_filename).resolve()==R/'experiments/v1114_coupled_steering_mode/coupled_control.py'
    assert Path(GearHandoff.select.__code__.co_filename).resolve()==R/'experiments/v1346_measured_gear_handoff/gear_handoff.py'
    assert sorted(os.sched_getaffinity(0))==[2]
    return Predictor,initial,kernel,Adapter

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--entry-check',action='store_true');parser.add_argument('--serialize-check',action='store_true');parser.add_argument('--guard-check',action='store_true');args=parser.parse_args();os.chdir(R)
    Predictor,initial,kernel,Adapter=binding();import numpy as np
    guard()
    if args.serialize_check:
        proof=read(O/'peer_qualification02/PEER_RESULT.json');proof['fixture']=dict(bad=np.bool_(False),ok=np.bool_(True),ulp=np.nextafter(np.float64(1),np.float64(2)))
        path=O/'ANALYTICAL_PRODUCER_JSON.json';io.atomic(path,proof);assert read(path)==proof and read(path)['fixture']['bad'] is False
    if args.guard_check:
        path=O/'qualification_write.tmp';path.write_text('fixture');assert path.read_text()=='fixture';path.unlink()
        for path in [R/'experiments/UNEXPECTED_WRITE.tmp',R/'runs/v1379_timed_response_preparation/UNEXPECTED_WRITE.tmp']:
            try:path.write_text('forbidden')
            except PermissionError:pass
            else:raise AssertionError('ANALYSIS_WRITE_ESCAPE_ACCEPTED')
    if args.entry_check or args.serialize_check or args.guard_check:
        print(json.dumps(dict(passed=True,physical_models=0,analytical_native=0,actual_cpu=sorted(os.sched_getaffinity(0)),full_model_imports_without_construction=True,producer_json_roundtrip=args.serialize_check,production_write_guard=args.guard_check)));return 0
    assert not (O/'ANALYSIS_RESULT.json').exists() and not (R/'REVIEW_PENDING').exists()
    window=read(O/'ROUND_WINDOW.json');authority=read(O/'ANALYSIS_APPROVAL.json');parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json')
    assert authority['mode']=='ANALYTICAL_ONLY' and authority['maximum_steps']==650000 and parent['active_round']=='v1393_analysis01'
    assert window['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip() and window['absolute_deadline_unix']<=1795395600
    frozen=read(O/'ANALYSIS_SOURCE_FREEZE.json')['files'];assert all(sha(R/name)==h for name,h in frozen.items())
    fixed=read(O/'FIXED_INPUTS.json');raw=R/fixed['source_raw'];setup=read(raw/'physics/SETUP.json');origin=fixed['observed_packet'];geometry=Geometry(setup['known'],fixed['causal_all_future_ball']);goal=fixed['original_target_segment']['poses'][-1]
    started=time.monotonic();end=min(started+1800,window['hard_stop_monotonic']-30);steps=0;inflight=False;states=[];controls=[];memory=[];journal=[];brakes=[];brake_states=[];brake_controls=[];sock=None
    result=dict(passed=False,closed=False,physical_models=0,canonical_vehicle_initializations=0,physical_native=0,physical_replay_native=0,private_mujoco_native=0,analytical_native=0,physical_admission=False,actual_moving_response_qualified=False,forecast_map_is_not_measured_future=True)
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('ANALYSIS_ROOT_STOP')));signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(TimeoutError('ANALYSIS_SUPERVISOR_STOP')));signal.alarm(max(1,int(end-time.monotonic())))
    def advance(p,v,w):
        nonlocal steps,inflight
        assert steps<650000 and time.monotonic()<end and time.time()<min(window['absolute_deadline_unix'],1795395600)-20,'ANALYSIS_BUDGET_OR_ROOT_STOP'
        inflight=True;s,u=p.step(v,w,False);steps+=1;inflight=False;return s,u
    def body(s):return [float(s[0]),float(s[1]),float(s[2]),float(s[3]),float(s[5])]
    def enc(s):
        k=math.tan(s[6])/.6;dk=(1+math.tan(s[6])**2)/.6*s[7];q=[];dq=[]
        for sign in [1.,-1.]:
            den=1-sign*.27*k;a=.6*k/den;q.append(math.atan(a));dq.append(.6*dk/(den*den*(1+a*a)))
        return q+dq
    with (R/'runs/v648_static_unknown/execution.lock').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            p=Predictor(setup,initial(origin),kernel.PARAMETERS);p.adapter.__class__=Adapter;p.adapter.parked_target=None;p.adapter._steering_motion_active=origin['steering_motion_active'];result['analytical_predictor_constructions']=1
            assert np.max(abs(np.asarray(body(p.state))-origin['body']))<=1e-10
            assert np.max(abs(p.adapter.last-origin['controller_memory']['last_ctrl']))<=1e-10
            gate=GearHandoff();gate.gear=1;gate.last_tick=10774;states.append(p.state.copy());zero_start=None;reply=None;sequence=0
            peer_out=O/'analysis_peer';sock=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM);address=str((O/'analysis_owner.sock').relative_to(R));sock.bind(address);sock.settimeout(.1);target=str((peer_out/'peer.sock').relative_to(R));run_id='v1393-analysis01'
            for index in range(3000):
                tick=10775+index
                if index%5==0 and zero_start is None:
                    request=dict(kind='MODELED_BODY_CAUSAL_MAP_NOT_SENSOR',run_id=run_id,sequence=sequence,native_tick=tick,body=body(p.state),sent_monotonic=time.monotonic());sock.sendto(json.dumps(request,allow_nan=False).encode(),target);until=time.monotonic()+(55 if sequence==0 else 3)
                    while True:
                        assert time.monotonic()<until and time.monotonic()<end,'RPP_MODELED_CALLBACK_TIMEOUT'
                        try:reply=json.loads(sock.recv(65536));break
                        except socket.timeout:pass
                    assert reply['run_id']==run_id and reply['sequence']==sequence,'FOREIGN_RPP_MODEL_REPLY';sequence+=1
                    if reply['kind']=='RPP_ACTION_DONE':
                        assert reply['status']==4 and reply['error_code']==0,'RPP_MODELED_ACTION_REFUSED';zero_start=index;requested=[0.,0.]
                    else:
                        assert reply['kind']=='ORIGINAL_RPP_MODELED_COMMAND' and reply['body']==request['body'] and reply['not_measured_response'];requested=[reply['v'],reply['w']]
                if zero_start is not None:requested=[0.,0.]
                branch=copy.deepcopy(p);branch_states=[branch.state.copy()];branch_controls=[]
                for _ in range(200):s,u=advance(branch,0.,0.);branch_states.append(s.copy());branch_controls.append(u.copy())
                a=np.asarray(branch_states);lower=geometry.tube(a);rest=bool(abs(a[-1,[3,4,5]]).max()<=.003 and abs(a[-1,7])<=.03 and abs(branch.adapter.last[2:]).max()<=1e-10);caps=bool((abs(a[:,3:6])<=np.array([.13,.03,.16])+1e-8).all())
                item=dict(before_native=tick,source_state=p.state.tolist(),source_memory=[*p.adapter.last.tolist(),float(p.adapter.integral)],complete_stop_native=200,causal_tube_lower_m=lower,rest=rest,body_caps=caps);brakes.append(item);brake_states.append(a);brake_controls.append(np.asarray(branch_controls))
                if lower<.22-1e-8 or not rest or not caps:result.update(first_rejected_braking=item,stop_reason='MODELED_COMPLETE_BRAKING_REFUSED');break
                if zero_start is None:assert 0<=time.monotonic()-reply['origin']['generated_monotonic']<=.2,'MODELED_COMMAND_EXPIRED_DURING_CERTIFICATE'
                memory.append([*p.adapter.last.tolist(),float(p.adapter.integral)]);v,w,proof=gate.select(*requested,native_tick=tick,body=body(p.state),last_ctrl=p.adapter.last,encoders=enc(p.state))
                s,u=advance(p,v,w);states.append(s.copy());controls.append(u.copy());journal.append(dict(before_native=tick,requested=requested,admitted=[v,w],gear=proof,rpp_sequence=None if zero_start is not None else reply['sequence'],zero_tail=zero_start is not None))
                if geometry.tube(states[-2:])<.22-1e-8:result.update(stop_reason='MODELED_NOMINAL_TUBE_REFUSED',first_rejected_native=tick+1);break
                if index%100==0:io.atomic(O/'PARTIAL.json',dict(nominal_native=len(journal),analytical_native=steps,body=body(p.state),physical_native=0))
                if zero_start is not None and index-zero_start+1==200:
                    rear=[s[0]-.3*math.cos(s[2]),s[1]-.3*math.sin(s[2]),s[2]];position=math.dist(rear[:2],goal[:2]);heading=abs(math.atan2(math.sin(rear[2]-goal[2]),math.cos(rear[2]-goal[2])))
                    checks=dict(endpoint_position=position<=.12,endpoint_heading=heading<=.20,complete200_zero_tail=all(x['zero_tail'] and x['admitted']==[0.,0.] for x in journal[-200:]),all_native_braking_covered=len(brakes)==len(journal),nominal_tube=geometry.tube(states)>=.22-1e-8,body_rest=max(abs(x) for x in body(s)[3:])<=.003)
                    result.update(passed=all(checks.values()),checks=checks,position_error_m=position,heading_error_rad=heading,stop_reason='MODELED_FULL_SEGMENT_COMPLETE');break
            else:result['stop_reason']='MODELED_NATIVE_LIMIT_3000'
        except BaseException as exc:result.update(error=repr(exc),traceback=traceback.format_exc(),stop_reason='ANALYSIS_ENTRY_SOURCE_OR_MODEL_EXCEPTION')
        finally:
            signal.alarm(0);signal.signal(signal.SIGTERM,lambda *_:None)
            if sock is not None:
                try:sock.sendto(json.dumps(dict(kind='STOP',run_id='v1393-analysis01')).encode(),target)
                except OSError:pass
                sock.close();(O/'analysis_owner.sock').unlink(missing_ok=True)
            io.atomic(O/'PREDICTED_JOURNAL.json',journal);io.atomic(O/'PREDICTED_MEMORY.json',memory);io.atomic(O/'BRAKING_WITNESS.json',brakes)
            if states:np.savez_compressed(O/'PREDICTED_RESPONSE.npz',states=np.asarray(states),ctrl=np.asarray(controls))
            if brake_states:np.savez_compressed(O/'BRAKING_ALTERNATIVES.npz',states=np.asarray(brake_states),ctrl=np.asarray(brake_controls))
            result.update(closed=True,analytical_native=steps,analytical_step_inflight_unknown=inflight,nominal_native=len(journal),complete_braking_branches=len(brakes),wall_s=time.monotonic()-started,source_unchanged=all(sha(R/name)==h for name,h in frozen.items()))
            io.atomic(O/'ANALYSIS_RESULT.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['traceback','first_rejected_braking']}));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
