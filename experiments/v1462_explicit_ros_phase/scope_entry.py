"""Real CPU3 production phase import and unchanged scope-source reuse only."""
import argparse
import ast
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;F=R/'experiments/v1460_live_event_pipe_close';FO=R/'runs'/F.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*_):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch'}:raise AssertionError('PHASE_IMPORT_MODELS_FORBIDDEN:'+name)

def ros_phase():
 assert sorted(os.sched_getaffinity(0))==[3];sys.meta_path.insert(0,NoModels());sys.path.insert(0,str(C))
 import rclpy
 from rclpy.node import Node
 def forbidden(*_,**__):raise AssertionError('PHASE_IMPORT_ROS_NODE_OR_CONTROLLER_FORBIDDEN')
 rclpy.init=forbidden;Node.__init__=forbidden;subprocess.Popen=forbidden
 module=exact('v1462_real_production_ROS_phase_source',C/'route_ros.py')
 try:__import__('phase_budget')
 except ModuleNotFoundError:old_red=True
 else:raise AssertionError('OLD_IMPLICIT_PHASE_IMPORT_RED_NOT_REPRODUCED')
 now=time.time();mono=time.monotonic();window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=now+5400,hard_stop_monotonic=mono+5400,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 limits=module.read(C/'LIMITS.json');phase=module.phase_clock(window,limits)
 assert Path(phase.__class__.__init__.__code__.co_filename)==R/'experiments/v1449_route_initializer_binding/phase_budget.py'
 end=phase.enter('normal');assert abs(end['absolute_deadline_unix']-(now+4140))<1e-6 and abs(end['hard_stop_monotonic']-(mono+4140))<1e-6
 assert phase.caps==limits['phase_wall_caps_s']and not any(x in sys.modules for x in ['mujoco','vehicle','factory','torch'])
 print(json.dumps(dict(passed=True,old_implicit_phase_import_refused=old_red,real_production_ROS_import=True,explicit_phase_source='experiments/v1449_route_initializer_binding/phase_budget.py',normal_cap_s=4140,actual_cpu=[3],ROS_nodes=0,controller_processes=0,models=0,physical_native=0)))

def qualify(task):
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'ENTRY_ONCE_CLAIM.json').exists()
 (O/'ENTRY_ONCE_CLAIM.json').write_text(json.dumps(dict(unix=time.time(),models=0,scope='EXPLICIT_ROS_NORMAL_PHASE_DEPENDENCY_ONLY'))+'\n')
 finder=NoModels();sys.meta_path.insert(0,finder);previous=sys.getprofile()
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_filename.startswith(str(R)+'/')and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py','vehicle_control.py'}:raise AssertionError('PHASE_ENTRY_CONSTRUCTOR_STEP_COMPUTE_FORBIDDEN')
 sys.setprofile(forbid);result=dict(passed=False,models=0,physical_native=0,allocator_recomputations=0,actual_replay_native=0,software_only=True);first=None
 io=exact('v1462_original_atomic',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');contract=exact('v1462_current_scope',C/'contract.py')
 try:
  parentpath=R/'runs/v1382_weekend_campaign/LEDGER.json';before=parentpath.read_bytes();parent=json.loads(before);assert parent['active_round']is None and not parent['models_now_authorized']
  with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   prior=contract.read(FO/'SCOPE_QUALIFICATION.json');assert prior['passed']and prior['models']==prior['physical_native']==0
   oldfrozen=contract.read(FO/'SOURCE_FREEZE.json')['files'];assert all(contract.sha(R/p)==h for p,h in oldfrozen.items())
   reused=[]
   for p in sorted(C.glob('*.py')):
    if p.name in {'scope_entry.py','route_ros.py'}:continue
    source=p.read_text().replace('v1462_explicit_ros_phase','v1460_live_event_pipe_close').replace('v1462','v1460')
    assert ast.dump(ast.parse(source))==ast.dump(ast.parse((F/p.name).read_text())),'UNDECLARED_PHASE_CHANGE:'+p.name;reused.append(p.name)
   source=(C/'route_ros.py').read_text().replace('v1462','v1460');tree=ast.parse(source);tree.body=[node for node in tree.body if not(isinstance(node,ast.FunctionDef)and node.name=='phase_clock')]
   class RestoreOld(ast.NodeTransformer):
    def visit_Call(self,node):
     self.generic_visit(node)
     if isinstance(node.func,ast.Name)and node.func.id=='phase_clock':node.func=ast.Attribute(value=ast.Call(func=ast.Name(id='__import__',ctx=ast.Load()),args=[ast.Constant(value='phase_budget')],keywords=[]),attr='PhaseBudget',ctx=ast.Load())
     return node
   assert ast.dump(RestoreOld().visit(tree))==ast.dump(ast.parse((F/'route_ros.py').read_text())),'ROS_CHANGED_BEYOND_EXPLICIT_PHASE_BINDING'
   helper=exact('v1462_qualified_ROS_namespace_environment',R/'experiments/v1396_rpp_rpc_retirement/peer_environment.py');folder=O/'phase_import';folder.mkdir();ros,env=helper.environment(folder)
   probe=subprocess.run(ros.command(['taskset','-c','3','/usr/bin/python3.12','-B',str(C/'scope_entry.py'),'--ros-phase']),cwd=R,env=env,capture_output=True,text=True,timeout=30)
   (folder/'CPU3.console').write_text(probe.stdout+probe.stderr);assert probe.returncode==0,probe.stdout+probe.stderr
   phase_proof=json.loads(probe.stdout.strip().splitlines()[-1]);assert phase_proof['passed']and phase_proof['ROS_nodes']==phase_proof['models']==0
   io.atomic(O/'ROS_PHASE_QUALIFICATION.json',phase_proof)
   life=exact('v1462_exact_current_lifecycle',C/'lifecycle.py');sup=exact('v1462_exact_once_scope',C/'supervisor.py')
   try:life.run(task,{},{})
   except RuntimeError as exc:assert str(exc)=='LIVE_FIRST_EVENT_ENTRY_PREREQUISITES_MISSING_NO_MODELS'
   else:raise AssertionError('NEW_PHASE_SCOPE_MISSING_ADMISSION_ACCEPTED')
   # Writer hook source is identical except the pure admission/phase bootstrap;
   # no writer path, role or byte capability changes in that bootstrap function.
   writers=dict(prior['writer_source_proofs']);assert set(writers)=={'ACTUAL_ROS','MODELED_ROS','PLANNER','SUPERVISOR_LOG'}
   limits=contract.read(C/'LIMITS.json');sup.budget.limits_check(limits);storage=sup.budget.storage_preflight(limits)
   inherited=dict(oldfrozen);inherited.update({str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()})
   assert parentpath.read_bytes()==before and not(O/'ROUND_WINDOW.json').exists()and not(O/'first_event').exists()
   result.update(passed=True,actual_cpu=[2],original_writeguard=True,constructor_step_compute_profile_guard=True,entry_gates=prior['entry_gates'],external_writer_hook_qualification=prior['external_writer_hook_qualification'],writer_source_proofs=writers,source_hashes=inherited,storage_preflight=storage,reused_scope_entry_SHA=contract.sha(FO/'SCOPE_QUALIFICATION.json'),normalized_unchanged_production_files=reused,only_ROS_normal_phase_dependency_changed=True,actual_CPU3_phase_import_qualification=phase_proof,whole_route_admission=False,live_event_runtime_passed=False,old_failed_runtime_and_missing_RESULT_preserved=True,source_remote_recovery_still_required=True)
 except BaseException as exc:
  import traceback
  first=dict(error=repr(exc),traceback=traceback.format_exc());result['first_error']=first
 finally:
  sys.setprofile(previous);sys.meta_path.remove(finder);io.atomic(O/'SCOPE_QUALIFICATION.json',result);io.atomic(O/'ENTRY_CLOSED.json',dict(closed=True,passed=result['passed'],models=0,first_error=first))
  files=result.get('source_hashes')or{str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()};io.atomic(O/'SOURCE_FREEZE.json',dict(files=files,entry_passed=result['passed'],models=0,whole_route_admission=False))
 return 0 if result['passed']else 1

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--ros-phase',action='store_true');a=p.parse_args();assert a.ros_phase;ros_phase()
