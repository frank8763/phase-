"""Only the changed whole-module guard compiler path; no old suite replay."""
import ast
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import types
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy'}:raise AssertionError('GUARD_IDENTITY_NO_MODELS:'+name)

def main():
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'ENTRY_QUALIFICATION.json').exists()
 os.chdir(R);sys.meta_path.insert(0,NoModels())
 def profile(frame,event,arg):
  if event=='call'and Path(frame.f_code.co_filename).is_relative_to(R)and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py','vehicle_control.py'}:raise AssertionError('GUARD_IDENTITY_MODEL_OR_COMPUTE_FORBIDDEN')
 sys.setprofile(profile);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply();exact('v1447_current_entry_CLI',C/'entry.py').install_guard(O)
 init=exact('v1447_current_initializer',C/'initializer.py');contract=init.contract;guards=exact('v1447_actual_whole_module_guard',C/'guard_binding.py')
 prior_path=R/'runs/v1445_immutable_initializer_writeguard/ENTRY_QUALIFICATION.json';prior=contract.read(prior_path);assert prior['passed']and prior['models']==0
 for path,digest in prior['source_hashes'].items():assert contract.sha(R/path)==digest
 same=[]
 for name in ['zero_steps.py','quota.py','entry.py','task_cache.py','initializer.py']:
  old=(R/'experiments/v1445_immutable_initializer_writeguard'/name).read_text().replace('v1445_immutable_initializer_writeguard',C.name).replace('v1445_','v1447_')
  assert ast.dump(ast.parse(old),include_attributes=False)==ast.dump(ast.parse((C/name).read_text()),include_attributes=False),'SOURCE_CHANGED_CANNOT_REUSE:'+name
  same.append(name)
 parent_path=R/'runs/v1382_weekend_campaign/LEDGER.json';parent_before=parent_path.read_bytes();p=json.loads(parent_before);assert p['active_round']is None and not p['models_now_authorized']
 negatives=[]
 def reject(label,fn,message):
  try:fn()
  except (AssertionError,RuntimeError,PermissionError)as exc:
   assert message in str(exc),(label,repr(exc));negatives.append(dict(case=label,error=repr(exc)));return
  raise AssertionError('FULL_MODULE_IDENTITY_NEGATIVE_ACCEPTED:'+label)
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);out=O/'identity_entry';out.mkdir()
  original=guards.ORIGINAL;module=compile(original.read_text(),str(original),'exec',dont_inherit=True)
  code=next(v for v in module.co_consts if isinstance(v,types.CodeType)and v.co_name=='write_guard')
  namespace=dict(Path=Path,os=os,OUT=out);guard=types.FunctionType(code,namespace,'write_guard')
  assert code.co_flags&16777216 and any(isinstance(v,types.CodeType)for v in code.co_consts)
  bound=guards.bind_function(guard,O);assert bound.__code__ is guard.__code__
  # The original failure is demonstrated using the extracted compiler result,
  # without rerunning any closed initializer or previous qualification.
  node=next(v for v in ast.parse(original.read_text()).body if isinstance(v,ast.FunctionDef)and v.name=='write_guard');subset=compile(ast.Module(body=[node],type_ignores=[]),str(original),'exec',dont_inherit=True)
  extracted=next(v for v in subset.co_consts if isinstance(v,types.CodeType)and v.co_name=='write_guard')
  assert extracted.co_code==code.co_code and extracted.co_names==code.co_names and extracted.co_consts!=code.co_consts
  reject('old_extracted_code_missing_future_flag',lambda:guards.bind_function(types.FunctionType(extracted,namespace,'write_guard'),O),'ORIGINAL_WRITE_GUARD_CODE_CHANGED')
  changed=code.replace(co_consts=code.co_consts+('UNAUTHORIZED_EXTRA_CONST',));reject('changed_constant_refused',lambda:guards.bind_function(types.FunctionType(changed,namespace,'write_guard'),O),'ORIGINAL_WRITE_GUARD_CODE_CHANGED')
  changed=code.replace(co_flags=code.co_flags^16777216);reject('changed_future_flag_refused',lambda:guards.bind_function(types.FunctionType(changed,namespace,'write_guard'),O),'ORIGINAL_WRITE_GUARD_CODE_CHANGED')
  changed=code.replace(co_filename=str(C/'guard_binding.py'));reject('wrong_source_refused',lambda:guards.bind_function(types.FunctionType(changed,namespace,'write_guard'),O),'ORIGINAL_WRITE_GUARD_SOURCE_CHANGED')
  with guards.bind_original_guard(O)as receipt:sys.addaudithook(guard)
  namespace['OUT']=R/'runs/v858_nav2_verified'
  init.io.atomic(out/'IMMUTABLE_CURRENT_OUTPUT.json',dict(software_only=True,future_flags=code.co_flags,mutable_OUT_changed=True,original_code_unchanged=True))
  assert receipt['installed_original_guard_count']==1 and bound.__globals__['OUT']==O
  reject('bound_original_other_run_write_refused',lambda:bound('open',(str(R/'runs/v858_nav2_verified/x'),'w',os.O_WRONLY)),'Write outside isolated experiment')
  reject('bound_original_Stage_read_refused',lambda:bound('open',(str(O/'training/e2e_test/x'),'r',0)),'Stage source excluded')
  reject('initializer_no_admission_refused',lambda:init.run({}, {}, {}),'INITIALIZER_ENTRY_PREREQUISITES_MISSING_MODELS_FORBIDDEN')
  assert parent_path.read_bytes()==parent_before
  result=dict(passed=True,models=0,physical_native=0,analytical_integrations=0,allocator_recomputations=0,actual_replay_native=0,actual_cpu=[2],original_writeguard=True,original_full_module_compiled_without_exec=True,exact_full_guard_code_future_flags_verified=code.co_flags,old_extracted_compiler_red_case_preserved=True,actual_immutable_original_hook_registered=True,negative_cases=negatives,entry_gates=prior['entry_gates'],changed_runtime_source_checks_passed=True,reused_initializer_entry_qualification_SHA=prior['reused_initializer_entry_qualification_SHA'],reused_OSMesa_and_immutable_scope_qualification_SHA=contract.sha(prior_path),unchanged_normalized_source_files=same,actual_native_C_save_executed=False,actual_canonical_initializer_called=False,initializer_runtime_qualified=False,physical_route_admission=False,all_runs_peak=contract.storage_preflight(),source_hashes={str(path.relative_to(R)):contract.sha(path)for path in C.iterdir()if path.is_file()})
  init.io.atomic(O/'ENTRY_QUALIFICATION.json',result);print(json.dumps(result));return 0

if __name__=='__main__':raise SystemExit(main())
