"""Complete recorded-audit ordinary path on explicit static software arrays.

No original closed physical/numerical run is audited or replayed. Artificial
205-row records can never establish navigation/scientific PASS.
"""
import ast
import copy
import fcntl
import gzip
import hashlib
import importlib.abc
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy','coupled_model','prediction'}:raise AssertionError('ARRAY_QUALIFICATION_NO_MODEL:'+name)

def main():
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'ARRAY_QUALIFICATION.json').exists()
 os.chdir(R);sys.meta_path.insert(0,NoModel())
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py'}:raise AssertionError('ARRAY_QUALIFICATION_MODEL_CALL')
 sys.setprofile(forbid)
 guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
 parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text());assert parent['active_round']is None and not parent['models_now_authorized']and parent['scientific_revisions']==5
 import numpy as np
 audit=exact('v1427_real_recorded_audit',C/'audit.py');io=exact('v1427_atomic_io',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  out=O/'software205';out.mkdir();(out/'physics').mkdir();n=205
  q=np.zeros(11);q[0]=-4.;q[1]=-2.;q[3]=1.;vel=np.zeros(10);control=np.zeros(4);pos=np.zeros((1,3));quat=np.array([[1.,0.,0.,0.]])
  initial=dict(time=np.array([0.]),qpos=q,qvel=vel,ctrl=control,mocap_pos=pos,mocap_quat=quat)
  trace=dict(time=.01*np.arange(1,n+1),qpos=np.tile(q,(n,1)),qvel=np.tile(vel,(n,1)),ctrl=np.tile(control,(n,1)),mocap_pos=np.tile(pos,(n,1,1)),mocap_quat=np.tile(quat,(n,1,1)),clearance=np.ones(n),self_margin=np.ones(n))
  def save_np(path,data):
   with path.open('wb')as stream:np.savez_compressed(stream,**data)
  save_np(out/'INITIAL_FULL_STATE.npz',initial);save_np(out/'physics/NATIVE_TRACE.npz',trace)
  setup=dict(actuator_ids=[0,1,2,3],limits=[[-.52,.52],[-.52,.52],[-10.,10.],[-10.,10.]],slew_per_second=[1.,1.,1.,1.],steering_qpos_addresses=[7,9],steering_qvel_addresses=[6,8],actor=dict(amplitude_m=.25,omega_rad_s=.32,radius_m=.1,axis_xy=[1.,0.],maximum_speed_m_s=.08,anchor_xy=[0.,0.],phase_rad=0.))
  io.atomic(out/'physics/SETUP.json',setup);io.atomic(out/'INITIAL_PACKET.json',dict(controller_memory=dict(last_ctrl=[0.,0.,0.,0.],integral=0.)))
  with gzip.open(out/'physics/CONTACTS.json.gz','wt')as stream:json.dump([[]for _ in range(n+1)],stream)
  with gzip.open(out/'physics/SENSORS.json.gz','wt')as stream:json.dump([dict(native_tick=0),dict(native_tick=n)],stream)
  body=[-4.,-2.,0.,0.,0.];gear=audit.gear_module.GearHandoff();root=[];now=100.;run_id='v1427_SOFTWARE_ARRAYS_NOT_PLANT';wire=dict(schema=1,run_id=run_id,sequence=0,sampled_at=now,body=body,ranges_m=[3.]*32,native_tick=0,sim_time=0.,sensor_frame=dict(native_tick=0,time=0.,xy=body[:2],yaw=0.,sampled_at=now))
  root.append(dict(kind='PUBLISHED_ACTUAL_ENVELOPE',envelope=dict(wire=wire,feedback=dict(native_tick=0),evidence_state_sha256=audit.recorded.digest(audit.fullstate(initial,trace,0)))))
  command=dict(kind='command',run_id=run_id,sequence=0,issued_at=now,v=0.,w=0.,command_source='CAUSAL_BRAKE_HOLD',origin=dict(kind='LOCAL_ZERO',generated_monotonic=now),observation_sequence=0,observation_native_tick=0,observation_sampled_at=now)
  root.append(dict(kind='RECEIVED_ACTUAL_ROUTE',before_native=0,packet=command,received_monotonic=now))
  delivery=dict(source_kind='ACTUAL_FRAME',run_id=run_id,origin=command['origin'],observation_sequence=0,observation_native_tick=0,observation_sampled_at=now)
  for i in range(n):
   vr,wr,proof=gear.select(0.,0.,native_tick=i,body=body,last_ctrl=[0.]*4,encoders=[0.]*4)
   row=dict(before_native=i,applied=False,request=[vr,wr,False],upstream_request=[0.,0.,False],gear_handoff=proof,body=body,encoders=[0.]*4,last_ctrl=[0.]*4,integral=0.,parked_target=None,control_owner='DISCLOSED_SHARED_EXECUTION_BRIDGE'if i<5 else'APPLIED_STOP_TAIL',delivery=delivery if i<5 else None,expiry_gate=dict(applied_monotonic=now)if i<5 else None,source_full_state_sha256=audit.recorded.digest(audit.fullstate(initial,trace,i)))
   root.extend([dict(kind='BEFORE_ORIGINAL_PREFIX_NATIVE',row=row),dict(kind='AFTER_ORIGINAL_PREFIX_NATIVE',row=dict(row,applied=True))])
  def save_root(data):(out/'ACTUAL_OWNER_JOURNAL.jsonl').write_text(''.join(json.dumps(row,separators=(',',':'))+'\n'for row in data))
  save_root(root)
  result=dict(new_actual_native=n,actual_inflight_unknown=False,source_unchanged=True,software_fixture_not_actual=True,functional_passed=False,first_error=None,save_errors=[],replay=dict(passed=True,replay_native=n,maximum_qpos_qvel_ctrl_mocap_error=0.,contact_mismatched_ticks=0,software_placeholder_not_replay=True),independent_allocation=dict(passed=True,recorded_rows=n,maximum_memory_control_error=0.,software_placeholder_not_allocator_compute=True),physical=dict(first_actor_detection=None,actual_travel_after_detection_m=0.))
  io.atomic(out/'RESULT.json',result);io.atomic(out/'ROS_RESULT.json',dict(passed=False,closed=True,evidence_write_errors=[],software_placeholder_not_ROS=True));io.atomic(out/'FORECAST_RECORDS.json',[dict(horizon_s=1.5,sim_time=0.,center=[0.,0.],radius_m=1.)])
  task=dict(output=str(out),run_id=run_id,goal_xy=[4.,-2.],start_xy=[-4.,-2.],start_yaw=0.)
  baseline=audit.audit(task);assert baseline['passed']is False
  passed=['actual_N_actions_Nplus1_states','finite_all_states','native_clock','physical_clearance','self_margin','source_unchanged','control_caps_and_slew','complete_contacts_no_bad','independent_body_encoders_fullstate_source','independent_gear_mode','actual_rpc_identity_and_retirement','continuous_control_owner_accounting','complete200_applied_zero_tail','forecast_coverage','sensor_initial_final_native','terminal_rest_and_zero_drive']
  assert all(baseline['checks'][key]for key in passed)
  assert baseline['checks']['real_actual_evidence_not_software_fixture']is False and baseline['checks']['whole_original_goal']is False and baseline['checks']['event_certificates_and_fixed_reference']is False
  io.atomic(O/'SOFTWARE_BASELINE_AUDIT.json',dict(baseline,software_arrays_only_not_actual_audit=True))
  negatives=[]
  def reject(name,fn):
   try:proof=fn()
   except (AssertionError,ValueError):negatives.append(name);return
   assert proof.get('passed')is False,'AUDIT_MUTATION_PASSED:'+name;negatives.append(name)
  changed={k:v.copy()for k,v in trace.items()};changed['qpos'][1,0]+=.001;save_np(out/'physics/NATIVE_TRACE.npz',changed);reject('changed_applied_fullstate',lambda:audit.audit(task));save_np(out/'physics/NATIVE_TRACE.npz',trace)
  changed={k:v.copy()for k,v in trace.items()};changed['time'][2]+=.001;save_np(out/'physics/NATIVE_TRACE.npz',changed);reject('native_clock_changed',lambda:audit.audit(task));save_np(out/'physics/NATIVE_TRACE.npz',trace)
  # Real pair source compares disk arrays. The second view is a software copy,
  # never a second actual trial or independent numerical sample.
  other=O/'software_pair_view';other.mkdir();(other/'physics').mkdir();save_np(other/'INITIAL_FULL_STATE.npz',initial);save_np(other/'physics/NATIVE_TRACE.npz',trace)
  pair=audit.pair(out,other);assert pair['passed']
  changed={k:v.copy()for k,v in trace.items()};changed['qpos'][1,0]=np.nan;save_np(other/'physics/NATIVE_TRACE.npz',changed);reject('pair_NaN_refused',lambda:audit.pair(out,other))
  changed={k:v.copy()for k,v in trace.items()};changed['ctrl'][1,0]=1e-7;save_np(other/'physics/NATIVE_TRACE.npz',changed);reject('pair_control_1e7_refused',lambda:audit.pair(out,other))
  changed={k:v.copy()for k,v in trace.items()};changed['time'][1]+=.001;save_np(other/'physics/NATIVE_TRACE.npz',changed);reject('pair_native_clock_refused',lambda:audit.pair(out,other));save_np(other/'physics/NATIVE_TRACE.npz',trace)
  proof=dict(passed=True,models=0,analytical_native=0,physical_native=0,replay_native=0,actual_cpu=[2],software_arrays_only_not_actual_navigation=True,ordinary_recorded_audit_full_function_exercised=True,ordinary_checks_passed=passed,full_actual_audit_unexecuted=True,event_reserve_certificate_reference_path_unexecuted=True,allocator_recomputation_unexecuted=True,software_pair_equal_arrays_not_independent_repeat=True,negative_cases=negatives,source_hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in C.glob('*')if p.is_file()},physical_admission=False)
  io.atomic(O/'ARRAY_QUALIFICATION.json',proof);print(json.dumps(proof))
if __name__=='__main__':main()
