"""Real native CLI: entry mode0models, normal mode requires complete admission."""
import argparse
import ast
import copy
import fcntl
import time
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoPhysical(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy'}:raise AssertionError('NATIVE_ENTRY_MODELS_FORBIDDEN:'+name)

def main():
 p=argparse.ArgumentParser();p.add_argument('task');p.add_argument('--entry-check',action='store_true');a=p.parse_args();assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
 if a.entry_check:
  sys.meta_path.insert(0,NoPhysical())
  def forbid(frame,event,arg):
   if event=='call'and frame.f_code.co_name in {'__init__','step'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py'}:raise AssertionError('NATIVE_ENTRY_ZERO_MODEL_CONSTRUCTOR_OR_STEP')
  sys.setprofile(forbid)
 os.chdir(R);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply();task=json.loads(Path(a.task).read_text());assert task in json.loads((C/'TASKS.json').read_text())
 out=O/'native_entry'if a.entry_check else Path(task['output']);assert out.is_relative_to(O)and out.is_dir()
 guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=out);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
 lifecycle=exact('v1427_actual_latest_lifecycle',C/'admitted_lifecycle.py');budget=exact('v1427_frozen_route_limits',C/'budget.py')
 if a.entry_check:
  lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert not(out/'ENTRY_QUALIFICATION.json').exists(),'ENTRY_ALREADY_CLOSED'
  assert Path(lifecycle.peer_module.EventPeer.command.__code__.co_filename).resolve()==R/'experiments/v1426_peer_graceful_closure/model_peer.py'
  try:budget.complete_admission()
  except RuntimeError as exc:assert str(exc)=='NO_COMPLETE_ROUTE_ADMISSION_MODELS_AND_VEHICLES_FORBIDDEN'
  else:raise AssertionError('UNQUALIFIED_ROUTE_ADMITTED')
  limits=budget.read(C/'LIMITS.json');budget.limits_check(limits);storage=budget.storage_preflight(limits)
  negatives=[]
  def rejected(label,fn):
   try:fn()
   except (AssertionError,RuntimeError,TimeoutError):negatives.append(label);return
   raise AssertionError('NEGATIVE_UNEXPECTEDLY_ACCEPTED:'+label)
  changed=copy.deepcopy(limits);changed['maximum_actual_native']+=1;rejected('changed_limits',lambda:budget.limits_check(changed))
  parent=budget.read(R/'runs/v1382_weekend_campaign/LEDGER.json');now=time.time();mono=time.monotonic();window=dict(boot_id=parent['boot_id'],started_unix=now,started_monotonic=mono,absolute_deadline_unix=now+5400,hard_stop_monotonic=mono+5400)
  budget.clocks(window,parent,reserve_s=600)
  bad=dict(window,boot_id='wrong');rejected('wrong_boot',lambda:budget.clocks(bad,parent,reserve_s=600))
  bad=dict(window,absolute_deadline_unix=now+500,hard_stop_monotonic=mono+500);rejected('finalization_reserve_exhausted',lambda:budget.clocks(bad,parent,reserve_s=600))
  supervisor=exact('v1427_once_supervisor_entry',C/'supervisor.py');rejected('once_supervisor_refuses_missing_admission',lambda:supervisor.launch('main'))
  errors=[]
  def close_error():raise OSError('SOFTWARE_CLOSE_ERROR')
  supervisor.cleanup_attempt(errors,'SOFTWARE_CLOSE',close_error);assert errors==[dict(stage='SOFTWARE_CLOSE',error="OSError('SOFTWARE_CLOSE_ERROR')")]
  assert not(O/'main/LAUNCH_CLAIM.json').exists()and not(O/'ROUND_WINDOW.json').exists()
  lifecycle.io.atomic(out/'ENTRY_QUALIFICATION.json',dict(negative_cases=negatives,secondary_closure_failure_captured=True,all_runs_storage_preflight=storage,production_supervisor_imported_not_launched=True,passed=True,models=0,analytical_native=0,physical_native=0,actual_cpu=[2],original_writeguard=True,constructor_step_profile_guard=True,latest_EventPeer_exact_binding=True,complete_admission_gate_refused=True,physical_admission=False));print((out/'ENTRY_QUALIFICATION.json').read_text());return 0
 qualification=budget.complete_admission();approval=json.loads((O/'APPROVAL.json').read_text());window=json.loads((O/'ROUND_WINDOW.json').read_text());budget.clocks(window,json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text()),reserve_s=600)
 result=lifecycle.run(task,approval,window);return 0 if result.get('functional_passed')and not result.get('first_error')and not result.get('save_errors')else 1
if __name__=='__main__':raise SystemExit(main())
