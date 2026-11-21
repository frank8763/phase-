"""New zero-model production import/binding check; no physical launch mode."""
import ast
import fcntl
import hashlib
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
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy'}:raise AssertionError('CUSP_ENTRY_PHYSICAL_IMPORT_FORBIDDEN:'+name)

def main():
 assert sys.argv[1:]==['--entry-check']and os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
 assert not(O/'ENTRY_QUALIFICATION.json').exists()
 os.chdir(R);sys.meta_path.insert(0,NoPhysical())
 calls=[]
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py'}:
   calls.append(frame.f_code.co_name);raise AssertionError('ZERO_MODEL_ENTRY_CONSTRUCTOR_OR_STEP')
 sys.setprofile(forbid)
 sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply()
 guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
 parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text());assert parent['active_round']is None and not parent['models_now_authorized']
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  old=R/'experiments/v1415_unified_causal_witness/audit.py';tree=ast.parse(old.read_text());function=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='audit');expr=next(x.value.args[1]for x in function.body if isinstance(x,ast.Assign)and any(isinstance(a,ast.Name)and a.id=='source'for a in x.targets))
  missing=eval(compile(ast.Expression(expr),str(old),'eval'),{'R':R});assert not missing.exists()
  try:exact('v1419_old_dependency_literal_red',missing)
  except FileNotFoundError:red=True
  else:raise AssertionError('MISSING_DEPENDENCY_RED_NOT_REPRODUCED')
  transaction=exact('v1419_actual_cusp_transaction',C/'transaction.py')
  source=transaction.auditor.backend_binding();source.binding()
  assert Path(source.__file__).resolve()==R/'experiments/v1415_unified_causal_witness/generator.py'
  assert transaction.auditor.backend_binding.__code__.co_filename==str(C/'audit.py')
  assert Path(transaction.owner.OwnerRequest.__init__.__code__.co_filename).resolve()==R/'experiments/v1415_unified_causal_witness/event_owner.py'
  assert not calls
  io=exact('v1419_atomic_evidence',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');import numpy as np
  io.atomic(O/'JSON_ROUNDTRIP.json',dict(passed=np.bool_(True),nested=[np.float64(.22),np.int64(200)]))
  assert json.loads((O/'JSON_ROUNDTRIP.json').read_text())==dict(passed=True,nested=[.22,200])
  files={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in C.glob('*')if p.is_file()}
  result=dict(passed=True,models=0,analytical_native=0,physical_native=0,old_dependency_literal_red_FileNotFoundError=red,new_production_backend_binding_green=True,actual_cpu=[2],original_writeguard=True,constructor_step_profile_guard=True,transaction_source_imported=True,full_numerical_audit_unexecuted=True,physical_admission=False,source_hashes=files)
  io.atomic(O/'ENTRY_QUALIFICATION.json',result);print(json.dumps(result))
if __name__=='__main__':main()
