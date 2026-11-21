"""Actual socket pump and real elapsed-time freshness probes; zero model work."""
import ast
import copy
import fcntl
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoPhysical(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy'}:raise AssertionError('RPC_QUALIFICATION_NO_PHYSICAL:'+name)

def main():
 assert sys.argv[1:]==['--entry-check']and os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'QUALIFICATION.json').exists()
 os.chdir(R);sys.meta_path.insert(0,NoPhysical());calls=[]
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py'}:calls.append(frame.f_code.co_name);raise AssertionError('RPC_ZERO_MODEL_CONSTRUCTOR_OR_STEP')
 sys.setprofile(forbid);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply();guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
 parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text());assert parent['active_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==5
 import numpy as np
 source=exact('v1424_actual_frozen_pump',R/'experiments/v1423_integrated_route_audit/pump.py');native=exact('v1424_actual_frozen_native',R/'experiments/v1423_integrated_route_audit/native_step.py');io=exact('v1424_atomic_io',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')
 out=O/'socket';out.mkdir();log=(out/'peer.console').open('x');peer=None;pump=None;records=[];budgets=[];tests=[]
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  n=SimpleNamespace(vehicle=SimpleNamespace(count=0),applied=0,run_id='v1424_SOFTWARE_RPC_NOT_PLANT',sent={},bridge_started=False)
  owner=SimpleNamespace(native=n,output=out,bridge=None,last_published_native=None);sequence=[0]
  def envelope():
   now=time.monotonic();tick=n.vehicle.count;body=[0.,0.,0.,0.,0.];wire=dict(schema=1,run_id=n.run_id,sequence=sequence[0],sampled_at=now,body=body,ranges_m=[3.]*32,native_tick=tick,sim_time=tick*.01,sensor_frame=dict(native_tick=tick,time=tick*.01,xy=[0.,0.],yaw=0.,sampled_at=now));sequence[0]+=1;n.sent[wire['sequence']]=wire;owner.last_published_native=tick
   return dict(kind='ROUTE_ACTUAL_FRAME',wire=wire,feedback={},evidence_state_sha256='0'*64)
  owner.envelope=envelope
  def check(stage,count):
   budgets.append((stage,count))
   if stage=='ACTUAL_NATIVE':raise RuntimeError('QUALIFIED_NO_MODEL_OR_ACTUAL_STEP_BUDGET_STOP')
  try:
   pump=source.Pump(owner,check_budget=check,append=records.append,model_peer=None)
   peer=subprocess.Popen(['taskset','-c','3','/usr/bin/python3.12','-B',str(C/'socket_peer.py'),str(out)],stdout=log,stderr=subprocess.STDOUT)
   end=time.monotonic()+5
   while not(out/'PEER_READY.json').exists():assert peer.poll()is None and time.monotonic()<end;time.sleep(.005)
   def request(index,kind,tick=0,tamper=False):io.atomic(out/'PEER_REQUEST.json',dict(index=index,kind=kind,native_tick=tick,tamper=tamper))
   def until(predicate):
    end=time.monotonic()+3
    while not predicate():assert peer.poll()is None and time.monotonic()<end;pump.iteration()
   request(0,'arm');until(lambda:pump.armed);tests.append('real_socket_arm')
   n.vehicle.count=n.applied=5;pump.publish();request(1,'command',0);until(lambda:len(pump.command_gate.retired)==1)
   assert pump.command_gate.retired[-1]['reason']=='SUPERSEDED_ACTUAL_STATE'and not any(x[0]=='ACTUAL_NATIVE'for x in budgets);tests.append('real_socket_superseded_source_retired_without_step')
   request(2,'command',5)
   try:until(lambda:False)
   except RuntimeError as exc:assert str(exc)=='QUALIFIED_NO_MODEL_OR_ACTUAL_STEP_BUDGET_STOP'
   else:raise AssertionError('VALID_COMMAND_DID_NOT_REACH_REAL_PRESTEP_BUDGET')
   assert pump.command_gate.accepted[-1]['observation_native_tick']==5 and n.vehicle.count==5;tests.append('real_socket_current_command_reaches_budget_without_step')
   request(3,'command',5,True)
   try:until(lambda:False)
   except AssertionError as exc:assert str(exc)=='BINDING_TICK_CHANGED'
   else:raise AssertionError('REAL_SOCKET_TAMPER_ACCEPTED')
   tests.append('real_socket_tampered_origin_refused')
  finally:
   io.atomic(out/'PEER_STOP.json',dict(stop=True))
   if peer is not None:
    try:peer.wait(timeout=3)
    except subprocess.TimeoutExpired:peer.terminate();peer.wait(timeout=2)
   if pump is not None:pump.close()
   log.close();io.atomic(out/'PUMP_RECEIPTS.json',dict(records=records,budget_callbacks=budgets,software_fixture_not_actual=True,models=0,physical_native=0))
  assert peer.returncode==0 and json.loads((out/'PEER_RESULT.json').read_text())['closed']
  branch=exact('v1424_original_saved_branch_reader',R/'experiments/v1407_lossless_branch_stream/stream.py');folder=R/'runs/v1417_complete_timed_witness/model/branches';index=json.loads((folder/'INDEX.json').read_text());reader=branch.BranchReader(folder,index,np);states,ctrl=reader.read(index['branches'][0]);reader.finish()
  ages=[]
  for case in ['expired_after_certificate','reserve_mutated_current_state']:
   v=SimpleNamespace(count=0,d=SimpleNamespace(time=0.,qpos=np.zeros(7),qvel=np.zeros(6),ctrl=np.zeros(4),mocap_pos=np.zeros((0,3)),mocap_quat=np.zeros((0,4))),adapter=SimpleNamespace(last=np.zeros(4),integral=0.))
   ns=native.NativeStep.__new__(native.NativeStep);ns.vehicle=v;ns.applied=0;ns.in_step=False;ns.before_native_budget=lambda *args:None
   modes=dict(canonical_origin_native=0,covered_native=0,coupled_episode=False,steering_motion_active=False,parked_target=None);ns.mode_memory=SimpleNamespace(snapshot=lambda tick:copy.deepcopy(modes));now=time.monotonic();wire=dict(schema=1,run_id='v1424_SOFTWARE_EXPIRY',sequence=0,sampled_at=now,body=[0.,0.,0.,0.,0.],ranges_m=[3.]*32,native_tick=0,sim_time=0.,sensor_frame=dict(native_tick=0,time=0.,xy=[0.,0.],yaw=0.,sampled_at=now));ns.sent={0:wire};ns.run_id=wire['run_id']
   packet=dict(body=wire['body'],body_lateral=0.,native_tick=0,sim_time=0.,steering=dict(position=[0.,0.],velocity=[0.,0.]),controller_memory=dict(last_ctrl=[0.,0.,0.,0.],integral=0.),**{k:modes[k]for k in ['coupled_episode','steering_motion_active','parked_target']});ns.packet=lambda _:copy.deepcopy(packet)
   identity=hashlib.sha256(json.dumps(packet,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
   def reserve(p,m):
    if case=='expired_after_certificate':time.sleep(.215)
    else:v.d.qpos[0]=.001
    return dict(before_native=0,complete_native=200,passed=True,source_packet_sha256=identity,causal_tube_lower_m=.22,software_injected_shape_only_not_certificate=True),states,ctrl
   ns.reserve=reserve;delivery=dict(source_kind='ACTUAL_FRAME',run_id=ns.run_id,origin=dict(kind='LOCAL_SHARED_ACTUAL_FEEDBACK',generated_monotonic=now),observation_sequence=0,observation_native_tick=0,observation_sampled_at=now)
   started=time.monotonic()
   try:ns.apply(0.,0.,phase='QUALIFICATION_ONLY',control_owner='DISCLOSED_SHARED_EXECUTION_BRIDGE',delivery=delivery)
   except AssertionError as exc:
    expected='ACTUAL_COMMAND_EXPIRED_DURING_CERTIFICATE'if case=='expired_after_certificate'else'PRIVATE_CERTIFICATE_MUTATED_ACTUAL_OWNER';assert str(exc)==expected
    ages.append(dict(case=case,error=repr(exc),elapsed_s=time.monotonic()-started,physical_native=0,analytical_native=0,copied_arrays_not_certificate=True))
   else:raise AssertionError('POST_CERTIFICATE_BOUNDARY_FAILED:'+case)
   assert v.count==0 and not ns.in_step
  assert not calls
  io.atomic(O/'QUALIFICATION.json',dict(passed=True,models=0,analytical_native=0,physical_native=0,replay_native=0,actual_cpu=[2],socket_peer_cpu=[3],real_datagram_production_pump=True,software_fixtures_not_actual_sensors_or_plant=True,production_socket_cases=tests,post_certificate_cases=ages,actual_route_ROS_controller_not_started=True,model_ROS_peer_lifecycle_unexecuted=True,full_route_admission=False,source_hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in C.glob('*')if p.is_file()}))
  print(json.dumps(dict(passed=True,models=0,physical_native=0,production_socket_cases=tests,post_certificate_cases=ages)))
if __name__=='__main__':main()
