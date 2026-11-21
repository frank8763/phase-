"""Once-only real actual-route ROS/controller standby and bounded close, no wire."""
import ast
import fcntl
import hashlib
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy','coupled_model','prediction'}:raise AssertionError('ACTUAL_ROS_STARTUP_NO_MODEL:'+name)

def main():
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'STARTUP_QUALIFICATION.json').exists()
 os.chdir(R);sys.meta_path.insert(0,NoModel())
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py'}:raise AssertionError('ACTUAL_ROS_STARTUP_PROFILE_MODEL_FORBIDDEN')
 sys.setprofile(forbid);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply();guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
 io=exact('v1439_small_atomic',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');writers=exact('v1439_startup_writer',C/'writer_budget.py');boundary=exact('v1439_current_output_boundary',C/'bounded_io.py');helper=exact('v1439_actual_ROS_namespace',R/'experiments/v1396_rpp_rpc_retirement/peer_environment.py');budget=exact('v1439_all_runs_peak',C/'budget.py')
 parent_path=R/'runs/v1382_weekend_campaign/LEDGER.json';parent_before=parent_path.read_bytes();parent=json.loads(parent_before);assert parent['active_round']is None and not parent['models_now_authorized']
 peak=budget.storage_preflight(json.loads((C/'LIMITS.json').read_text()));claim=json.loads((O/'STARTUP_QUALIFICATION_CLAIM.json').read_text());identity=hashlib.sha256((O/'STARTUP_QUALIFICATION_CLAIM.json').read_bytes()).hexdigest()
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  out=O/'startup_close_task';out.mkdir();task=json.loads((C/'TASKS.json').read_text())[0];task.update(task_id='startup_close_only',role='startup_close_only',run_id='V1439_ZERO_WIRE_ROS_START_CLOSE',output=str(out),run_root=str(O))
  now=time.time();mono=time.monotonic();window=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=min(now+60,parent['absolute_hard_stop_unix']),hard_stop_monotonic=min(mono+60,parent['hard_stop_monotonic']),boot_id=parent['boot_id'])
  approval=dict(models_authorized=False,scope='ZERO_MODEL_ACTUAL_ROS_START_CLOSE_QUALIFICATION',source_hashes=claim['source_hashes'])
  io.atomic(O/'STARTUP_CLOSE_TASK.json',task);io.atomic(O/'STARTUP_CLOSE_WINDOW.json',window);io.atomic(O/'STARTUP_CLOSE_AUTHORITY.json',approval);io.atomic(out/'APPROVAL.json',approval)
  io.atomic(out/'EXTERNAL_WRITER_RESERVATIONS.json',dict(purpose=approval['scope'],source_identity=identity,approval_sha256=hashlib.sha256((out/'APPROVAL.json').read_bytes()).hexdigest(),writers={'ACTUAL_ROS':dict(maximum_bytes=24*1024**2,source_hook_coverage_qualified=False)}))
  writer=writers.WriterBudget(out,role='SUPERVISOR_LOG',maximum_bytes=8*1024**2,source_identity=identity)
  ros,env=helper.environment(out);env.update(PHASE_BOUNDED_TASK_OUTPUT=str(out),PHASE_BOUNDED_WRITER_ROLE='ACTUAL_ROS',PHASE_BOUNDED_SOURCE_ID=identity)
  job=None;log=None;proof=dict(passed=False,closed=False,models=0,analytical_integrations=0,allocator_recomputations=0,physical_native=0,actual_replay_native=0,actual_parent_cpu=[2],parent_constructor_step_compute_profile_guard=True,original_writeguard=True,actual_scan_or_wire_sent=False,actual_controller_only_standby=True,physical_admission=False)
  start=time.monotonic()
  try:
   with boundary.OutputBoundary(out,writer.reserve):
    log=(out/'actual_ros.console').open('x');job=subprocess.Popen(ros.command(['taskset','-c','3','/usr/bin/python3.12','-B',str(C/'route_ros.py'),str(O/'STARTUP_CLOSE_TASK.json'),'--startup-close-qualification']),cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    ready_file=out/'STARTUP_CLOSE_READY.json'
    while not ready_file.exists():
     assert job.poll()is None and time.monotonic()-start<30,'ACTUAL_ROS_STARTUP_READY_MISSING'
     time.sleep(.02)
    ready=json.loads(ready_file.read_text());assert ready['actual_cpu']==[3]and ready['network_namespace']!=os.readlink('/proc/self/ns/net')
    assert ready['source_sha256']==hashlib.sha256((C/'route_ros.py').read_bytes()).hexdigest()and ready['params_sha256']==hashlib.sha256(Path(task['nav2_params']).read_bytes()).hexdigest()
    assert ready['controller_standby_only']and not ready['controller_activated']and not ready['controller_configured']and not ready['FollowPath_called']and ready['scan_messages']==0
    io.atomic(out/'PEER_STOP_REQUEST.json',dict(run_id=task['run_id'],requested_monotonic=time.monotonic(),no_native_action=True))
    while job.poll()is None:
     assert time.monotonic()-start<50,'ACTUAL_ROS_STARTUP_COMPLETE_CLOSE_TIMEOUT';time.sleep(.02)
    code=job.wait(timeout=2);log.close();log=None
   result=json.loads((out/'ROS_RESULT.json').read_text());assert code==1 and result['closed']and result['controller_server_exited']and result['functional_stop']=='COOPERATIVE_PEER_CLOSED'
   assert not result.get('error')and not result.get('cleanup_error')and result['evidence_write_errors']==[]
   assert result['published_scan_messages']==0 and result['commands']==0 and not result['actual_wire_received']and result['FollowPath_unexecuted_in_startup_scope']
   counter=json.loads((out/'WRITER_ACTUAL_ROS_BYTES.json').read_text());assert counter['source_identity']==identity and 16384<counter['charged_bytes']<=24*1024**2
   assert any(x.endswith('ROS_RESULT.json.tmp')for x in counter['paths'])and any(x.endswith('controller.console')for x in counter['paths'])
   assert parent_path.read_bytes()==parent_before
   proof.update(passed=True,ready=ready,ROS_result=result,wrapper_returncode=code,cooperative_stop_and_complete_controller_exit=True,inner_network_namespace_verified=True,zero_wire_zero_scan_zero_command_verified=True,writer_budget=counter,parent_log_writer_budget=json.loads(writer.path.read_text()),whole_route_PASS_claimed=False,modelsfalse_coveragefalse_qualification_authority=True,all_runs_peak=peak,actual_native_C_save_executed=False)
  except BaseException as exc:proof.update(error=repr(exc),traceback=traceback.format_exc())
  finally:
   errors=[]
   if job is not None and job.poll()is None:
    try:
     os.killpg(job.pid,signal.SIGTERM)
     try:job.wait(timeout=5)
     except subprocess.TimeoutExpired:os.killpg(job.pid,signal.SIGKILL);job.wait(timeout=3)
    except BaseException as exc:errors.append(dict(stage='FORCED_WRAPPER_CLOSE',error=repr(exc)))
   if log is not None:
    try:log.close()
    except BaseException as exc:errors.append(dict(stage='CLOSE_PARENT_LOG',error=repr(exc)))
   proof.update(closed=True,wall_s=time.monotonic()-start,secondary_close_errors=errors,source_hashes=claim['source_hashes'])
   if errors:proof['passed']=False
   io.atomic(O/'STARTUP_QUALIFICATION.json',proof)
  print(json.dumps(proof));return 0 if proof['passed']else 1

if __name__=='__main__':raise SystemExit(main())
