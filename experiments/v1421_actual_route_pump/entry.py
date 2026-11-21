"""Preparation-only real native CLI; all model construction profile-forbidden."""
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
class NoPhysical(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy'}:raise AssertionError('ACTUAL_PUMP_ENTRY_NO_PHYSICAL:'+name)

def main():
 assert sys.argv[1:]==['--entry-check']and os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
 assert not(O/'ENTRY_QUALIFICATION.json').exists();os.chdir(R);sys.meta_path.insert(0,NoPhysical());calls=[]
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py'}:
   calls.append(frame.f_code.co_name);raise AssertionError('ACTUAL_PUMP_ZERO_MODEL_CONSTRUCTOR_OR_STEP')
 sys.setprofile(forbid);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply()
 guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
 parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text());assert parent['active_round']is None and not parent['models_now_authorized']
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  spec=importlib.util.spec_from_file_location('v1421_actual_native_lifecycle',C/'lifecycle.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  task=next(x for x in json.loads((R/'experiments/v1370_overnight_controller_matrix/TASKS.json').read_text())if x['task_id']=='rpp_default_horizon_m1_s01_main')
  try:m.admit(task,{},{} )
  except m.NotAdmitted as exc:
   assert str(exc)=='ACTUAL_ROUTE_FULL_QUALIFICATION_AND_BUDGET_MISSING';m.io.atomic(O/'PRELAUNCH_REFUSAL.json',dict(passed=True,expected_refusal=repr(exc),models=0,physical_native=0))
  else:raise AssertionError('PREPARATION_ADMITTED_PHYSICAL_ROUTE')
  assert not calls
  functions=[m.run,m.physical_binding,m.pump_module.Pump.iteration,m.pump_module.Pump.prefix_step,m.owner_module.CanonicalOwner.on_cusp,m.owner_module.CanonicalOwner.after_bridge_zero,m.peer_module.EventPeer.command]
  assert all(Path(fn.__code__.co_filename).resolve().is_relative_to(C)for fn in functions)
  source={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in C.glob('*')if p.is_file()}
  result=dict(passed=True,models=0,analytical_native=0,physical_native=0,actual_cpu=[2],original_writeguard=True,constructor_step_profile_guard=True,real_lifecycle_pump_peer_owner_imports=True,normal_route_prelaunch_refused_before_physical_binding=True,actual_pump_runtime_unexecuted=True,model_peer_runtime_unexecuted=True,full_route_admission=False,source_hashes=source)
  m.io.atomic(O/'ENTRY_QUALIFICATION.json',result);print(json.dumps(result))
if __name__=='__main__':main()
