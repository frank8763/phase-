"""Targeted scope/stop/parent-pipe qualification; never model construction."""
import argparse
import ast
import copy
import fcntl
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*_):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy'}:raise AssertionError('LIVE_EVENT_ENTRY_MODELS_FORBIDDEN:'+name)

def ros_scope_check():
 assert sorted(os.sched_getaffinity(0))==[3]
 sys.meta_path.insert(0,NoModels());context=exact('v1458_exact_current_ROS_context',C/'route_context.py');task=context.read(C/'TASKS.json')[0]
 try:context.authorize(task,{})
 except RuntimeError as exc:assert str(exc)=='LIVE_FIRST_EVENT_ENTRY_PREREQUISITES_MISSING_NO_MODELS'
 else:raise AssertionError('ROS_CURRENT_SCOPE_MISSING_GATE_ACCEPTED')
 assert not any(x in sys.modules for x in ['mujoco','vehicle','factory','torch','rclpy'])
 print(json.dumps(dict(passed=True,actual_cpu=[3],exact_production_ROS_authorize_refused=True,ROS_nodes=0,controller_processes=0,models=0,physical_native=0)))

def qualify(task):
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]
 assert not(O/'ENTRY_ONCE_CLAIM.json').exists()
 (O/'ENTRY_ONCE_CLAIM.json').write_text(json.dumps(dict(unix=time.time(),models=0,scope='NEW_LIVE_EVENT_SCOPE_AND_PARENT_PIPE_ONLY'))+'\n')
 finder=NoModels();sys.meta_path.insert(0,finder);previous=sys.getprofile()
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_filename.startswith(str(R)+'/')and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py','vehicle_control.py'}:raise AssertionError('LIVE_EVENT_ENTRY_CONSTRUCTOR_STEP_COMPUTE_FORBIDDEN')
 sys.setprofile(forbid);result=dict(passed=False,models=0,physical_native=0,allocator_recomputations=0,actual_replay_native=0,software_only=True);first=None;negative=[]
 io=exact('v1458_original_atomic',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');contract=exact('v1458_current_scope',C/'contract.py')
 def rejected(name,fn):
  try:fn()
  except (AssertionError,RuntimeError,FileExistsError,FileNotFoundError):negative.append(name);return
  raise AssertionError('LIVE_EVENT_ENTRY_NEGATIVE_ACCEPTED:'+name)
 try:
  parentpath=R/'runs/v1382_weekend_campaign/LEDGER.json';before=parentpath.read_bytes();parent=json.loads(before);assert parent['active_round']is None and not parent['models_now_authorized']
  with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   life=exact('v1458_production_lifecycle_scope',C/'lifecycle.py');sup=exact('v1458_actual_once_supervisor_scope',C/'supervisor.py');stopper=exact('v1458_exact_event_stop',C/'event_stop.py')
   rejected('native_scope_missing_admission',lambda:life.run(task,{},{}))
   rejected('once_owner_scope_missing_admission',lambda:sup.launch('first_event'))
   rejected('missing_actual_source_remote_recovery',lambda:contract.verify_source_recovery({str(C.relative_to(R))+'/native_entry.py':contract.sha(C/'native_entry.py')}))
   rejected('whole_main_role_not_authorized',lambda:sup.launch('main'))
   rejected('repeat_role_not_authorized',lambda:sup.launch('repeat'))
   assert life.O==sup.O==contract.O==O and life.C==R/'experiments/v1449_route_initializer_binding'
   # Actual CPU3 pure production authorize, not another ROS lifecycle run.
   ros=subprocess.run(['taskset','-c','3','/usr/bin/python3.12','-B',str(C/'scope_entry.py'),'--ros-scope'],cwd=R,capture_output=True,text=True,timeout=10)
   assert ros.returncode==0,ros.stderr;rosproof=json.loads(ros.stdout);assert rosproof['passed']and rosproof['models']==0
   io.atomic(O/'ROS_SCOPE_QUALIFICATION.json',rosproof)
   # These event objects explicitly test software dispatch only. complete=True
   # is not a physics certificate and is never stored as an actual event PASS.
   native=SimpleNamespace(bridge_started=True,applied=71,vehicle=SimpleNamespace(count=71),in_step=False,mode_memory=SimpleNamespace(snapshot=lambda tick:dict(covered_native=tick)))
   owner=SimpleNamespace(transaction=SimpleNamespace(last_event=-1),bridge=None,native=native);pump=SimpleNamespace(stopped=False);s=stopper.FirstEventStop(owner,pump)
   s.before_iteration();assert s.after_iteration()is False and not pump.stopped
   rejected('not_complete_cannot_pass',s.require_complete)
   owner.transaction.last_event=0;owner.bridge=SimpleNamespace(complete=False,request=SimpleNamespace(current=dict(input_sha256='a'*64)))
   assert not s.after_iteration()and not pump.stopped
   owner.bridge.request.current['input_sha256']='b'*64;rejected('current_input_change',s.after_iteration);owner.bridge.request.current['input_sha256']='a'*64
   owner.transaction.last_event=1;rejected('second_event',s.before_iteration);rejected('foreign_event_after_iteration',s.after_iteration);owner.transaction.last_event=0
   native.in_step=True;owner.bridge.complete=True;rejected('inflight_actual_not_complete',s.after_iteration);native.in_step=False
   assert s.after_iteration()and pump.stopped and s.require_complete()['completed_native']==71
   rejected('completed_component_cannot_iterate_again',s.before_iteration)
   # Real small stdout child exercises the exact production BoundedConsole and
   # WriterBudget role under a finite explicit software-only counter.
   software=O/'software_scope';software.mkdir();writer_module=exact('v1458_frozen_counter_writer',C/'writer_budget.py')
   writer=writer_module.WriterBudget(software,role='SUPERVISOR_LOG',maximum_bytes=65536,source_identity='d'*64)
   logpath=software/'real_child.console';expected=b'Phase bounded stdout\n'
   with logpath.open('xb')as stream:
    bounded=sup.BoundedConsole(stream,writer,logpath)
    job=subprocess.Popen(['taskset','-c','5','/usr/bin/python3.12','-B','-c',"import os;os.write(1,b'Phase bounded stdout\\n')"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
    try:
     block=job.communicate(timeout=5)[0];assert job.returncode==0 and block==expected;bounded.feed(block)
     previous_bytes=writer._read()['charged_bytes'];rejected('bounded_parent_stdout_cap',lambda:bounded.feed(b'x'*65536))
     assert writer._read()['charged_bytes']==previous_bytes and bounded.charged==len(expected)
    finally:
     if job.poll()is None:sup.terminate(job)
   assert logpath.read_bytes()==expected
   # Exact known owned child identity is rejected before any signal if altered.
   child=subprocess.Popen(['taskset','-c','5','/usr/bin/python3.12','-B','-c','import time;time.sleep(10)'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
   try:
    identity=sup.process_identity(child.pid);bad=dict(identity,start_ticks=identity['start_ticks']+1)
    rejected('wrong_owned_process_identity',lambda:sup.close_recorded_process(bad));assert child.poll()is None
    sup.close_recorded_process(identity);child.wait(timeout=4)
   finally:
    if child.poll()is None:sup.terminate(child)
   sample=dict(rounds=[dict(id='software_round',actual_native=3,own_replay_native=2,canonical_initializations=1)],active_round='software_round',models_now_authorized=True,actual_total_native=91,own_replay_native=80)
   err=[dict(stage='SOFTWARE_FIRST',error='primary'),dict(stage='SOFTWARE_SECOND',error='secondary')]
   unknown=sup.owner_failure_account(sample,'software_round',err,child_completion_exists=False)
   assert unknown['rounds'][0]['actual_native']is None and unknown['rounds'][0]['own_replay_native']is None and unknown['rounds'][0]['accounting_unknown']and unknown['actual_total_native']==91 and sample['active_round']=='software_round'
   known=sup.owner_failure_account(sample,'software_round',err,child_completion_exists=True);assert known['rounds'][0]['actual_native']==3 and known['rounds'][0]['owner_errors']==err
   io.atomic(software/'OWNER_UNKNOWN_AND_FIRST_ERROR.json',dict(software_only=True,unknown_child=unknown,known_child=known,not_actual_parent_mutation=True))
   coverage=exact('v1458_current_writer_source',C/'writer_coverage.py').coverage();assert set(coverage)=={'ACTUAL_ROS','MODELED_ROS','PLANNER','SUPERVISOR_LOG'}
   limits=contract.read(C/'LIMITS.json');sup.budget.limits_check(limits);storage=sup.budget.storage_preflight(limits)
   now=time.time();mono=time.monotonic();window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=now+5400,hard_stop_monotonic=mono+5400,boot_id=parent['boot_id']);contract.clocks(window,parent,reserve_s=1260)
   bad=dict(window,hard_stop_monotonic=mono+5399);rejected('new_scope_clock_pair_mismatch',lambda:contract.clocks(bad,parent,reserve_s=1260))
   bad=dict(window,boot_id='wrong');rejected('new_scope_boot_mismatch',lambda:contract.clocks(bad,parent,reserve_s=1260))
   original=next(x for x in contract.read(R/'experiments/v1370_overnight_controller_matrix/TASKS.json')if x['task_id']=='rpp_default_horizon_m1_s01_main');remap={'task_id','run_id','output','run_root','native_limit','depends_on','role'}
   assert {k:v for k,v in original.items()if k not in remap}=={k:v for k,v in task.items()if k not in remap}
   init=contract.read(R/'runs/v1447_full_module_guard_identity/COMPLETION.json');closure=contract.read(R/'runs/v1454_bounded_gzip_closure/CLOSED_REVIEW.json');assert init['passed']and closure['passed']and closure['actual_native']==closure['own_replay_native']==closure['independent_allocator_recomputations']==200
   # Fixed method/native/freshness/geometry/RPC functions all remain exact frozen
   # dependencies; this qualification does not claim their new-state outcome.
   inherited={}
   for directory in ['v1456_route_closure_binding','v1454_bounded_gzip_closure']:
    files=contract.read(R/'runs'/directory/'SOURCE_FREEZE.json')['files'];assert all(contract.sha(R/p)==h for p,h in files.items());inherited.update(files)
   inherited.update({str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()})
   assert parentpath.read_bytes()==before and not(O/'ROUND_WINDOW.json').exists()and not(O/'first_event').exists()and not(O/'LIVE_FIRST_EVENT_ONLY_ADMISSION.json').exists()
   result.update(passed=True,actual_cpu=[2],original_writeguard=True,constructor_step_compute_profile_guard=True,negatives_rejected=negative,entry_gates={key:True for key in contract.GATES},external_writer_hook_qualification={key:row['source_scope_qualified']for key,row in coverage.items()},writer_source_proofs=coverage,source_hashes=inherited,storage_preflight=storage,real_CPU3_pure_ROS_context=rosproof,real_bounded_stdout_software_child_bytes=len(expected),whole_route_admission=False,live_event_runtime_passed=False,partial_navigation_attempts=0,newscope_software_stop_flags_not_physics=True,source_remote_recovery_still_required=True,initializer_and_closure_runtime_proof_referenced_not_rerun=True)
 except BaseException as exc:
  import traceback
  first=dict(error=repr(exc),traceback=traceback.format_exc());result['first_error']=first
 finally:
  sys.setprofile(previous);sys.meta_path.remove(finder);io.atomic(O/'SCOPE_QUALIFICATION.json',result);io.atomic(O/'ENTRY_CLOSED.json',dict(closed=True,passed=result['passed'],models=0,first_error=first))
  files=result.get('source_hashes')or{str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()}
  io.atomic(O/'SOURCE_FREEZE.json',dict(files=files,entry_passed=result['passed'],models=0,whole_route_admission=False))
 return 0 if result['passed']else 1

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--ros-scope',action='store_true');a=p.parse_args();assert a.ros_scope;ros_scope_check()
