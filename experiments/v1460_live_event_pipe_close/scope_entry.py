"""Changed owned-child pipe close plus previously unexecuted source gates."""
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
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;F=R/'experiments/v1458_live_first_event_runtime';FO=R/'runs'/F.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*_):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy'}:raise AssertionError('LIVE_EVENT_PIPE_ENTRY_MODELS_FORBIDDEN:'+name)

def qualify(task):
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'ENTRY_ONCE_CLAIM.json').exists()
 (O/'ENTRY_ONCE_CLAIM.json').write_text(json.dumps(dict(unix=time.time(),models=0,scope='OWNED_CHILD_PIPE_CLOSE_AND_REMAINING_SOURCE_GATES'))+'\n')
 finder=NoModels();sys.meta_path.insert(0,finder);previous=sys.getprofile()
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_filename.startswith(str(R)+'/')and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py','vehicle_control.py'}:raise AssertionError('NEW_PIPE_ENTRY_CONSTRUCTOR_STEP_COMPUTE_FORBIDDEN')
 sys.setprofile(forbid);result=dict(passed=False,models=0,physical_native=0,allocator_recomputations=0,actual_replay_native=0,software_only=True);first=None;negative=[]
 io=exact('v1460_original_atomic',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');contract=exact('v1460_current_contract',C/'contract.py')
 def rejected(label,fn):
  try:fn()
  except (AssertionError,RuntimeError,FileExistsError,FileNotFoundError):negative.append(label);return
  raise AssertionError('NEW_PIPE_SCOPE_NEGATIVE_ACCEPTED:'+label)
 try:
  parentpath=R/'runs/v1382_weekend_campaign/LEDGER.json';before=parentpath.read_bytes();parent=json.loads(before);assert parent['active_round']is None and not parent['models_now_authorized']
  with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   prior=contract.read(FO/'CLOSED_REVIEW.json');assert prior['passed']is False and prior['source_derived_completed_prefix_only']is True and '/dev/null'in prior['first_error']['error']
   oldfreeze=contract.read(FO/'SOURCE_FREEZE.json')['files'];assert all(contract.sha(R/p)==h for p,h in oldfreeze.items())
   # Reuse only production functions identical under the explicit scope/output
   # relocation. Do not reexecute the previously passed CPU3/pipe/stop fixtures.
   reused=[]
   for p in sorted(C.glob('*.py')):
    if p.name=='scope_entry.py':continue
    assert ast.dump(ast.parse(p.read_text().replace('v1460_live_event_pipe_close','v1458_live_first_event_runtime').replace('v1460','v1458')))==ast.dump(ast.parse((F/p.name).read_text())),'UNDECLARED_PRODUCTION_CHANGE:'+p.name
    reused.append(p.name)
   ros=contract.read(FO/'ROS_SCOPE_QUALIFICATION.json');assert ros['passed']and ros['actual_cpu']==[3]and ros['ROS_nodes']==ros['models']==0
   assert (FO/'software_scope/real_child.console').read_bytes()==b'Phase bounded stdout\n'
   life=exact('v1460_exact_scope_lifecycle',C/'lifecycle.py');sup=exact('v1460_exact_parent_owner',C/'supervisor.py');context=exact('v1460_exact_ROS_scope',C/'route_context.py')
   rejected('new_native_scope_missing_admission',lambda:life.run(task,{},{}));rejected('new_once_owner_scope_missing_admission',lambda:sup.launch('first_event'))
   rejected('new_ROS_context_scope_missing_admission',lambda:context.authorize(task,{}))
   rejected('missing_current_remote_source_recovery',lambda:contract.verify_source_recovery({str(C.relative_to(R))+'/native_entry.py':contract.sha(C/'native_entry.py')}))
   assert life.O==sup.O==context.O==contract.O==O and life.C==R/'experiments/v1449_route_initializer_binding'
   # Exact changed path: a real owned software child uses only PIPE/STDOUT.
   software=O/'software_pipe_close';software.mkdir();child=subprocess.Popen(['taskset','-c','5','/usr/bin/python3.12','-B','-c','import time;time.sleep(10)'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
   try:
    identity=sup.process_identity(child.pid);bad=dict(identity,start_ticks=identity['start_ticks']+1)
    rejected('tampered_owned_child_identity',lambda:sup.close_recorded_process(bad));assert child.poll()is None
    sup.close_recorded_process(identity);child.wait(timeout=4);child.stdout.close();assert child.returncode is not None
   finally:
    if child.poll()is None:sup.terminate(child)
    if child.stdout is not None and not child.stdout.closed:child.stdout.close()
   sample=dict(rounds=[dict(id='software_round',actual_native=3,own_replay_native=2,canonical_initializations=1)],active_round='software_round',models_now_authorized=True,actual_total_native=91,own_replay_native=80)
   err=[dict(stage='SOFTWARE_FIRST',error='primary'),dict(stage='SOFTWARE_SECOND',error='secondary')]
   unknown=sup.owner_failure_account(sample,'software_round',err,child_completion_exists=False);known=sup.owner_failure_account(sample,'software_round',err,child_completion_exists=True)
   assert unknown['rounds'][0]['actual_native']is None and unknown['rounds'][0]['own_replay_native']is None and unknown['rounds'][0]['accounting_unknown']and unknown['actual_total_native']==91 and sample['active_round']=='software_round'
   assert known['rounds'][0]['actual_native']==3 and known['rounds'][0]['owner_errors']==err
   io.atomic(software/'OWNER_UNKNOWN_AND_FIRST_ERROR.json',dict(software_only=True,unknown_child=unknown,known_child=known,not_actual_parent_mutation=True))
   coverage=exact('v1460_frozen_writer_coverage',C/'writer_coverage.py').coverage();assert set(coverage)=={'ACTUAL_ROS','MODELED_ROS','PLANNER','SUPERVISOR_LOG'}
   limits=contract.read(C/'LIMITS.json');sup.budget.limits_check(limits);storage=sup.budget.storage_preflight(limits)
   now=time.time();mono=time.monotonic();window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=now+5400,hard_stop_monotonic=mono+5400,boot_id=parent['boot_id']);contract.clocks(window,parent,reserve_s=1260)
   rejected('scope_clock_pair_mismatch',lambda:contract.clocks(dict(window,hard_stop_monotonic=mono+5399),parent,reserve_s=1260));rejected('scope_boot_mismatch',lambda:contract.clocks(dict(window,boot_id='wrong'),parent,reserve_s=1260))
   original=next(x for x in contract.read(R/'experiments/v1370_overnight_controller_matrix/TASKS.json')if x['task_id']=='rpp_default_horizon_m1_s01_main');remap={'task_id','run_id','output','run_root','native_limit','depends_on','role'}
   assert {k:v for k,v in original.items()if k not in remap}=={k:v for k,v in task.items()if k not in remap}
   init=contract.read(R/'runs/v1447_full_module_guard_identity/COMPLETION.json');closure=contract.read(R/'runs/v1454_bounded_gzip_closure/CLOSED_REVIEW.json');assert init['passed']and closure['passed']and closure['actual_native']==closure['own_replay_native']==closure['independent_allocator_recomputations']==200
   inherited={}
   for directory in ['v1456_route_closure_binding','v1454_bounded_gzip_closure']:
    files=contract.read(R/'runs'/directory/'SOURCE_FREEZE.json')['files'];assert all(contract.sha(R/p)==h for p,h in files.items());inherited.update(files)
   inherited.update({str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()})
   assert parentpath.read_bytes()==before and not(O/'ROUND_WINDOW.json').exists()and not(O/'first_event').exists()and not(O/'LIVE_FIRST_EVENT_ONLY_ADMISSION.json').exists()
   result.update(passed=True,actual_cpu=[2],original_writeguard=True,constructor_step_compute_profile_guard=True,negatives_rejected=negative,entry_gates={key:True for key in contract.GATES},external_writer_hook_qualification={key:row['source_scope_qualified']for key,row in coverage.items()},writer_source_proofs=coverage,source_hashes=inherited,storage_preflight=storage,reused_completed_prefix_source_SHA=contract.sha(FO/'CLOSED_REVIEW.json'),reused_CPU3_ROS_scope_SHA=contract.sha(FO/'ROS_SCOPE_QUALIFICATION.json'),reused_stdout_raw_SHA=contract.sha(FO/'software_scope/real_child.console'),normalized_unchanged_production_files=reused,real_owned_child_PIPE_closed=True,whole_route_admission=False,live_event_runtime_passed=False,partial_navigation_attempts=0,source_remote_recovery_still_required=True,old_entry_failure_preserved=True)
 except BaseException as exc:
  import traceback
  first=dict(error=repr(exc),traceback=traceback.format_exc());result['first_error']=first
 finally:
  sys.setprofile(previous);sys.meta_path.remove(finder);io.atomic(O/'SCOPE_QUALIFICATION.json',result);io.atomic(O/'ENTRY_CLOSED.json',dict(closed=True,passed=result['passed'],models=0,first_error=first))
  files=result.get('source_hashes')or{str(p.relative_to(R)):contract.sha(p)for p in C.iterdir()if p.is_file()};io.atomic(O/'SOURCE_FREEZE.json',dict(files=files,entry_passed=result['passed'],models=0,whole_route_admission=False))
 return 0 if result['passed']else 1
