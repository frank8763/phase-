"""Exact control scope and atomic closure on explicitly mapped software files."""
import ast
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
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy','coupled_model','prediction'}:raise AssertionError('CONTROL_SCOPE_NO_MODEL:'+name)

def main():
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'CONTROL_QUALIFICATION.json').exists();os.chdir(R);sys.meta_path.insert(0,NoModel())
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py'}:raise AssertionError('CONTROL_ZERO_MODEL_CONSTRUCTOR_STEP_COMPUTE')
 sys.setprofile(forbid);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply();guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
 parent_path=R/'runs/v1382_weekend_campaign/LEDGER.json';parent_before=parent_path.read_bytes();parent=json.loads(parent_before);assert parent['active_round']is None and not parent['models_now_authorized']
 reference=(O/'REVIEW_PENDING.reference').read_bytes();assert hashlib.sha256(reference).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 boundary=exact('v1435_exact_control_boundary',C/'bounded_io.py');writers=exact('v1435_control_role_counter',C/'writer_budget.py');supervisor=exact('v1435_actual_supervisor_closure',C/'supervisor.py')
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  out=O/'control_task';out.mkdir();software=O/'software_control_files';software.mkdir()
  review=software/'REVIEW_PENDING';ledger=software/'LEDGER.json';stage=software/'LEDGER.json.tmp'
  # Physical files are software-only; quota labels map onto the exact real
  # control targets to exercise production role/target admission without writing
  # the active parent ledger or changing the real review sentinel.
  aliases={review:R/'REVIEW_PENDING',ledger:parent_path,stage:parent_path.with_suffix('.json.tmp')}
  writer=writers.WriterBudget(out,role='SUPERVISOR_LOG',maximum_bytes=1024**2,source_identity='c'*64);wrong=writers.WriterBudget(out,role='ACTUAL_ROS',maximum_bytes=1024**2,source_identity='c'*64)
  def charge(path,size):return writer.reserve(path,size)if path.is_relative_to(out)else writer.reserve_control(aliases[path],size)
  negatives=[]
  def reject(label,fn):
   try:fn()
   except (AssertionError,OSError,KeyError,ValueError):negatives.append(label);return
   raise AssertionError('CONTROL_SCOPE_NEGATIVE_ACCEPTED:'+label)
  with boundary.OutputBoundary(out,charge,control_paths=aliases,control_renames={(stage,ledger)}):
   review.write_bytes(reference);assert review.read_bytes()==reference
   supervisor.put(ledger,dict(software_only=True,active_round=None,models_now_authorized=False,status='CLOSED_SOFTWARE_TEST'))
   assert not stage.exists()and json.loads(ledger.read_text())['active_round']is None
   reject('non_supervisor_role_control_write',lambda:wrong.reserve_control(R/'REVIEW_PENDING',1))
   reject('unlisted_real_control_target',lambda:writer.reserve_control(R/'RESEARCH_STATUS.md',1))
   reject('unlisted_output_escape',lambda:(O/'FORBIDDEN_OUTSIDE_CONTROL').write_text('no'))
   stage.write_text('software stage only')
   reject('control_stage_wrong_rename_target',lambda:stage.replace(out/'wrong.json'))
   reject('control_final_wrong_rename_source',lambda:ledger.replace(review))
   stage.replace(ledger)
   primary=dict(error="ValueError('SOFTWARE_PRIMARY')",software_only=True);errors=[]
   def failure():raise OSError('SOFTWARE_SECONDARY_CLOSE')
   supervisor.cleanup_attempt(errors,'CLOSE_SOFTWARE_CHILD',failure)
   assert primary['error']=="ValueError('SOFTWARE_PRIMARY')"and errors[0]['stage']=='CLOSE_SOFTWARE_CHILD'
   review.write_bytes(reference);supervisor.put(ledger,dict(software_only=True,closed=True,passed=False,first_error=primary,secondary_closure_errors=errors,active_round=None,models_now_authorized=False))
   saved=json.loads(ledger.read_text());assert saved['first_error']==primary and saved['secondary_closure_errors']==errors and review.read_bytes()==reference
  assert parent_path.read_bytes()==parent_before,'LIVE_PARENT_LEDGER_CHANGED_DURING_SOFTWARE_CONTROL_TEST'
  result=dict(passed=True,models=0,analytical_integrations=0,allocator_recomputations=0,physical_native=0,actual_replay_native=0,actual_cpu=[2],original_writeguard=True,constructor_step_compute_profile_guard=True,explicit_software_control_file_mapping=True,real_parent_ledger_unchanged=True,original_review_bytes_SHA_verified_in_software_restore=True,production_atomic_put_and_cleanup_attempt_exercised=True,secondary_error_did_not_mask_first=True,negative_cases=negatives,actual_supervisor_work_unexecuted=True,complete_route_admission_absent=True,physical_admission=False,source_hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in C.iterdir()if p.is_file()})
  exact('v1435_atomic_result_io',R/'experiments/v1383_exact_timed_handoff/evidence_io.py').atomic(O/'CONTROL_QUALIFICATION.json',result);print(json.dumps(result))
if __name__=='__main__':main()
