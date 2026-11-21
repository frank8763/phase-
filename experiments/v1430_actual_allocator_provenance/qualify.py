"""Actual source association on explicit software arrays, zero compute/model."""
import ast
import copy
import fcntl
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy','coupled_model','prediction'}:raise AssertionError('ALLOCATOR_SOURCE_NO_MODELS:'+name)

def main():
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'QUALIFICATION.json').exists();os.chdir(R);sys.meta_path.insert(0,NoModel())
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py'}:raise AssertionError('ALLOCATOR_SOURCE_MODEL_CONSTRUCTOR_STEP_COMPUTE_FORBIDDEN')
 sys.setprofile(forbid);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply();guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
 parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text());assert parent['active_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==5
 import numpy as np
 source=exact('v1430_production_allocator_source',C/'allocation.py');lifecycle=exact('v1430_actual_lifecycle_binding',C/'lifecycle.py');supervisor=exact('v1430_once_supervisor_binding',C/'supervisor.py')
 assert Path(lifecycle.peer_module.EventPeer.command.__code__.co_filename).resolve()==R/'experiments/v1426_peer_graceful_closure/model_peer.py'
 # This file path is in the actual run function, not a generic sys.modules alias.
 text=(C/'lifecycle.py').read_text();assert "allocation=exact('v1423_independent_allocator_audit',C/'allocation.py')"in text
 assert "R/'experiments/v1429_native_scalar_event_audit/audit.py'"in(C/'supervisor.py').read_text()
 io=exact('v1430_atomic_io',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  q=np.zeros(11);q[0]=-4.;q[1]=-2.;q[3]=1.;state=dict(time=0.,qpos=q.tolist(),qvel=np.zeros(10).tolist(),ctrl=[0.]*4,mocap_pos=[],mocap_quat=[])
  setup=dict(actuator_ids=[0,1,2,3],steering_qpos_addresses=[7,9],steering_qvel_addresses=[6,8]);initial=dict(native_tick=0,sim_time=0.,body=[-4.,-2.,0.,0.,0.],body_lateral=0.,steering=dict(position=[0.,0.],velocity=[0.,0.]),controller_memory=dict(last_ctrl=[0.]*4,integral=0.),coupled_episode=False,steering_motion_active=False,parked_target=None)
  actual=[dict(copy.deepcopy(state),time=.01*(i+1))for i in range(3)];rows=[];modes=source.mode_module.ModeMemory(canonical_native=0,coupled_episode=False,steering_motion_active=False)
  for i in range(3):
   before=state if i==0 else actual[i-1];target=.05 if i==1 else None
   rows.append(dict(before_native=i,applied=True,source_full_state_sha256=source.digest(before),body=initial['body'],encoders=[0.]*4,last_ctrl=[0.]*4,integral=0.,control_owner='ORIGINAL_RPP'if i==0 else'DISCLOSED_SHARED_EXECUTION_BRIDGE',request=[0.,0.,False],parked_target=target,mode_history=modes.snapshot(i)))
   modes.applied(before_native=i,v=0.,w=0.,parked_target=target,steering_motion_active_after=target is not None)
  baseline=source.preflight(actual,rows,state,initial,setup);assert baseline['passed']and baseline['source_rows']==3
  negatives=[]
  def reject(label,fn):
   try:fn()
   except (AssertionError,ValueError,KeyError):negatives.append(label);return
   raise AssertionError('ALLOCATOR_SOURCE_MUTATION_ACCEPTED:'+label)
  changed=copy.deepcopy(rows);changed[1]['body'][0]+=.01;reject('body_wrong_actual_state',lambda:source.preflight(actual,changed,state,initial,setup))
  changed=copy.deepcopy(rows);changed[2]['encoders'][0]=.1;reject('encoder_wrong_actual_state',lambda:source.preflight(actual,changed,state,initial,setup))
  changed=copy.deepcopy(actual);changed[1]['qpos'][1]+=.01;reject('actual_fullstate_changed',lambda:source.preflight(changed,rows,state,initial,setup))
  changed=copy.deepcopy(rows);changed[1]['last_ctrl'][0]=.01;reject('last_control_not_actual',lambda:source.preflight(actual,changed,state,initial,setup))
  changed=copy.deepcopy(initial);changed['controller_memory']['last_ctrl'][0]=.01;reject('initial_control_memory_not_actual',lambda:source.preflight(actual,rows,state,changed,setup))
  changed=copy.deepcopy(rows);changed[2]['mode_history']['coupled_episode']=False;reject('cross_mode_history_reset',lambda:source.preflight(actual,changed,state,initial,setup))
  reject('missing_actual_row',lambda:source.preflight(actual[:-1],rows,state,initial,setup))
  io.atomic(O/'SOFTWARE_SOURCE_ARRAYS.json',dict(initial_full_state=state,initial_packet=initial,actual_arrays=actual,source_rows=rows,software_only_not_physical=True))
  result=dict(passed=True,models=0,physical_native=0,analytical_integrations=0,actual_replay_native=0,allocator_constructions=0,allocator_recomputations=0,actual_cpu=[2],original_writeguard=True,constructor_step_compute_profile_guard=True,software_source_only=True,production_preflight_Nplus1_source_exercised=True,negative_cases=negatives,latest_EventPeer_and_V1429_event_audit_explicit_lifecycle_supervisor_bindings=True,actual_allocator_recomputation_unexecuted=True,actual_lifecycle_and_supervisor_unexecuted=True,complete_route_admission_absent=True,source_hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in C.iterdir()if p.is_file()})
  io.atomic(O/'QUALIFICATION.json',result);print(json.dumps(result))
if __name__=='__main__':main()
