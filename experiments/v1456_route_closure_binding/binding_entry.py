"""Only new state-first storage and exact new production-output bindings."""
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
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*_):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy'}:raise AssertionError('NEW_ROUTE_BINDING_MODELS_FORBIDDEN:'+name)

def qualify(task):
 assert not(O/'ENTRY_ONCE_CLAIM.json').exists()
 (O/'ENTRY_ONCE_CLAIM.json').write_text(json.dumps(dict(unix=time.time(),models=0,scope='NEW_STATE_FIRST_CLOSURE_AND_NATIVE_OUTPUT_BINDING'))+'\n')
 finder=NoModels();sys.meta_path.insert(0,finder);previous=sys.getprofile()
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_filename.startswith(str(R)+'/')and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py','vehicle_control.py'}:raise AssertionError('NEW_ROUTE_BINDING_MODEL_OR_COMPUTE_FORBIDDEN')
 sys.setprofile(forbid);life=exact('v1456_actual_new_lifecycle',C/'lifecycle.py');result=dict(passed=False,models=0,physical_native=0,allocator_recomputations=0,actual_replay_native=0,software_only=True);first=None;negatives=[]
 def rejected(name,fn):
  try:fn()
  except (AssertionError,RuntimeError,FileExistsError):negatives.append(name);return
  raise AssertionError('NEW_ROUTE_BINDING_NEGATIVE_ACCEPTED:'+name)
 try:
  import numpy as np
  parentpath=R/'runs/v1382_weekend_campaign/LEDGER.json';before=parentpath.read_bytes();parent=json.loads(before);assert parent['active_round']is None and not parent['models_now_authorized']
  with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   assert life.O==O and life.N==C and life.C==R/'experiments/v1449_route_initializer_binding'
   rejected('new_native_lifecycle_missing_complete_admission',lambda:life.run(task,{},{}))
   supervisor=exact('v1456_once_current_supervisor',C/'supervisor.py');budget=supervisor.budget
   assert supervisor.O==O and budget.O==O and supervisor.C==C
   rejected('new_once_supervisor_missing_complete_admission',lambda:supervisor.launch('main'))
   tasks=life.read(C/'TASKS.json');assert all(Path(t['output']).is_relative_to(O)and Path(t['run_root'])==O for t in tasks)
   original=next(t for t in life.read(R/'experiments/v1370_overnight_controller_matrix/TASKS.json')if t['task_id']=='rpp_default_horizon_m1_s01_main');remap={'task_id','run_id','output','run_root','native_limit','depends_on','role'}
   assert all({k:v for k,v in t.items()if k not in remap}=={k:v for k,v in original.items()if k not in remap}for t in tasks)
   assert Path(life.peer_module.EventPeer.command.__code__.co_filename)==R/'experiments/v1449_route_initializer_binding/model_peer.py'
   old,Adapter,factory,replay=life.physical_binding(O)
   assert Path(Adapter.compute.__code__.co_filename)==R/'experiments/v1114_coupled_steering_mode/coupled_control.py'
   assert Path(factory.create_vehicle.__code__.co_filename)==R/'experiments/v1067_causal_replan_brake_reserve/scene_binding.py'
   assert Path(replay.__code__.co_filename)==R/'experiments/v882_runtime_evidence_repair/physical.py'
   current=life.read(R/'runs/v1454_bounded_gzip_closure/CLOSED_REVIEW.json');assert current['passed']and current['actual_native']==current['independent_allocator_recomputations']==current['own_replay_native']==200
   writers=exact('v1456_bound_writer_proof',C/'writer_coverage.py').coverage();assert len(writers)==4
   limits=budget.read(C/'LIMITS.json');budget.limits_check(limits);storage=budget.storage_preflight(limits)
   qmodule=exact('v1456_frozen_quota',life.C/'quota.py');boundary=exact('v1456_frozen_boundary',C/'bounded_io.py');saver=exact('v1456_new_state_first_saver',C/'state_capture.py');audit=exact('v1456_scalar_clock_recorded_audit',C/'audit.py')
   software=O/'software_state_first';software.mkdir();quota=qmodule.EvidenceQuota(software,limits);quota.bind_external_names([]);quota.external_writers=[];quota.write_enforcement_active=True
   initial=dict(time=np.asarray(0.),qpos=np.arange(20,dtype=float),qvel=np.zeros(19),ctrl=np.zeros(11),mocap_pos=np.zeros((1,3)),mocap_quat=np.asarray([[1.,0.,0.,0.]]))
   rows=[{k:np.asarray(v).copy()for k,v in initial.items()}for _ in range(2)];rows[0]['time']=np.asarray(.01);rows[1]['time']=np.asarray(.02);rows[1]['qpos'][0]+=.01
   vehicle=SimpleNamespace(rows=rows,count=3,d=SimpleNamespace(ctrl=np.zeros(11)))
   with boundary.OutputBoundary(software,quota.charge_write):
    quota.prepare_grant(2*1024**2,phase='COMPLETE_ZERO_TAIL_OR_CLOSURE',valid_for_s=30,external_writers=[])
    for label,state,count in [('N0',[],0),('partial_N2_gap1',rows,3)]:
     folder=software/label;folder.mkdir();vehicle.rows=state;vehicle.count=count
     proof=saver.save_current_prefix(vehicle,initial,folder,quota,np)
     assert proof['recorded_actions']==len(state)and proof['recorded_Nplus1_states']==len(state)+1 and proof['unrecorded_actual_gap']==count-len(state)and proof['complete']==(count==len(state))
     with np.load(folder/'FULL_STATE_NPLUS1.npz',allow_pickle=False)as stream:
      assert all(np.array_equal(stream[k][0],value)for k,value in initial.items())and len(stream['applied_ctrl'])==len(state)
      if state:assert np.array_equal(stream['qpos'][1:],np.asarray([r['qpos']for r in state]))
     rejected('no_overwrite_'+label,lambda:saver.save_current_prefix(vehicle,initial,folder,quota,np))
    def badcase(label,*,newinitial=None,newrows=None,count=2):
     folder=software/label;folder.mkdir();v=SimpleNamespace(rows=rows if newrows is None else newrows,count=count,d=vehicle.d)
     return saver.save_current_prefix(v,initial if newinitial is None else newinitial,folder,quota,np)
    bad=dict(initial,time=np.asarray([0.]));rejected('initial_clock_wrong_rank',lambda:badcase('rank',newinitial=bad))
    badrows=copy.deepcopy(rows);badrows[0]['qpos']=np.zeros(19);rejected('actual_shape_changed',lambda:badcase('shape',newrows=badrows))
    badrows=copy.deepcopy(rows);badrows[0]['qvel'][0]=np.nan;rejected('nonfinite_actual',lambda:badcase('nan',newrows=badrows))
    rejected('recorded_exceeds_actual_count',lambda:badcase('count',count=1))
   quota.retire_grant();quota.write_enforcement_active=False
   # Scalar initial time must agree with the original digest contract in the
   # actual allocator and the new recorded route audit, no numerical model run.
   vehicle.rows=rows;trace={k:np.asarray([row[k]for row in rows])for k in initial}
   assert audit.fullstate(initial,trace,0)['time']==0. and audit.fullstate(initial,trace,2)['time']==.02
   rejected('recorded_initial_clock_wrong_rank',lambda:audit.fullstate(dict(initial,time=np.asarray([0.])),trace,0))
   assert parentpath.read_bytes()==before and not(O/'ROUND_WINDOW.json').exists()and not(O/'main').exists()and not(O/'repeat').exists()
   frozen={}
   for name in ['v1449_route_initializer_binding','v1454_bounded_gzip_closure']:
    files=life.read(R/'runs'/name/'SOURCE_FREEZE.json')['files'];assert all(life.sha(R/p)==h for p,h in files.items());frozen.update(files)
   frozen.update({str(p.relative_to(R)):life.sha(p)for p in C.iterdir()if p.is_file()})
   result.update(passed=True,actual_cpu=[2],original_writeguard=True,constructor_step_compute_profile_guard=True,negative_cases=negatives,new_native_supervisor_task_output_and_frozen_peer_bindings=True,state_first_N0_and_partial_gap_roundtrip=True,no_copy_counted_as_physics_or_replay=True,scalar_initial_clock_matches_actual_allocator_and_recorded_audit=True,old_actual_closure_proof_referenced_not_reexecuted=True,external_writer_source_coverage=writers,all_runs_storage_peak=storage,complete_route_admission_absent=True,physical_admission=False,source_hashes=frozen,current_event_crossmode_runtime_unexecuted=True)
 except BaseException as exc:
  import traceback
  first=dict(error=repr(exc),traceback=traceback.format_exc());result['first_error']=first
 finally:
  sys.setprofile(previous);sys.meta_path.remove(finder)
  life.io.atomic(O/'BINDING_QUALIFICATION.json',result);life.io.atomic(O/'ENTRY_CLOSED.json',dict(closed=True,passed=result['passed'],models=0,first_error=first))
  # A failed once qualification freezes the attempted source too; repair only
  # in a new version, never by overwriting this evidence or rerunning this CLI.
  if result['passed']:life.io.atomic(O/'SOURCE_FREEZE.json',dict(files=result['source_hashes'],models=0,physical_admission=False))
 return 0 if result['passed']else 1
