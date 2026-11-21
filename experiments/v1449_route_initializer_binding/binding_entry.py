"""Exact changed production source binding check; never initialize a vehicle."""
import ast
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy'}:raise AssertionError('ROUTE_BINDING_NO_MODEL:'+name)

def main():
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'BINDING_QUALIFICATION.json').exists()
 os.chdir(R);sys.meta_path.insert(0,NoModels())
 def forbid(frame,event,arg):
  if event=='call'and Path(frame.f_code.co_filename).is_relative_to(R)and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py','vehicle_control.py'}:raise AssertionError('ROUTE_BINDING_MODEL_OR_COMPUTE_FORBIDDEN')
 sys.setprofile(forbid);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply();guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
 life=exact('v1449_actual_route_lifecycle',C/'lifecycle.py');budget=exact('v1449_actual_current_limits',C/'budget.py');writers=exact('v1449_actual_source_coverage',C/'writer_coverage.py')
 parent_path=R/'runs/v1382_weekend_campaign/LEDGER.json';before=parent_path.read_bytes();parent=json.loads(before);assert parent['active_round']is None and not parent['models_now_authorized']
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  refused=False
  try:life.run({}, {}, {})
  except life.NotAdmitted as exc:assert str(exc)=='ACTUAL_ROUTE_FULL_QUALIFICATION_AND_BUDGET_MISSING';refused=True
  assert refused
  initialized=json.loads((R/'runs/v1447_full_module_guard_identity/COMPLETION.json').read_text());assert initialized['passed']and initialized['native']['passed']and initialized['native']['canonical_vehicle_initializations']==1 and initialized['native']['actual_native']==0
  frozen=json.loads((R/'runs/v1447_full_module_guard_identity/SOURCE_FREEZE.json').read_text())['files'];assert all(life.sha(R/p)==h for p,h in frozen.items())
  old,Adapter,factory,replay=life.physical_binding(O)
  assert Path(Adapter.compute.__code__.co_filename)==R/'experiments/v1114_coupled_steering_mode/coupled_control.py'
  assert Path(factory.create_vehicle.__code__.co_filename)==R/'experiments/v1067_causal_replan_brake_reserve/scene_binding.py'
  coverage=writers.coverage();assert set(coverage)=={'ACTUAL_ROS','MODELED_ROS','PLANNER','SUPERVISOR_LOG'}
  storage=budget.storage_preflight(json.loads((C/'LIMITS.json').read_text()));assert parent_path.read_bytes()==before
  assert not(O/'COMPLETE_INTEGRATED_ROUTE_QUALIFICATION.json').exists()and not(O/'ROUND_WINDOW.json').exists()
  life.io.atomic(O/'BINDING_QUALIFICATION.json',dict(passed=True,models=0,analytical_integrations=0,allocator_recomputations=0,physical_native=0,actual_replay_native=0,actual_cpu=[2],original_writeguard=True,constructor_step_compute_profile_guard=True,real_production_lifecycle_no_admission_refused=True,actual_V1447_initializer_runtime_evidence_referenced_not_reexecuted=True,exact_original_factory_Adapter_and_replay_binding=True,external_writer_source_coverage=coverage,all_runs_storage_peak=storage,complete_route_admission_absent=True,physical_admission=False,source_hashes={str(p.relative_to(R)):life.sha(p)for p in C.iterdir()if p.is_file()}))
  print(json.dumps(dict(passed=True,models=0,physical_native=0,writer_roles=list(coverage),complete_route_admission=False)))

if __name__=='__main__':main()
