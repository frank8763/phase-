"""One actual bounded planner worker invocation on explicit public-map input."""
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
  if name.split('.')[0]in {'mujoco','vehicle','factory','torch','rclpy','coupled_model','prediction'}:raise AssertionError('PLANNER_WRITER_QUALIFICATION_NO_MODEL:'+name)

def main():
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[2]and not(O/'PLANNER_QUALIFICATION.json').exists()
 os.chdir(R);sys.meta_path.insert(0,NoModel())
 def forbid(frame,event,arg):
  if event=='call'and frame.f_code.co_name in {'__init__','step','compute'}and Path(frame.f_code.co_filename).name in {'coupled_model.py','prediction.py','kernel.py','coupled_control.py'}:raise AssertionError('PLANNER_PROFILE_MODEL_OR_COMPUTE_FORBIDDEN')
 sys.setprofile(forbid);sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
 apply();guard=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py';node=next(x for x in ast.parse(guard.read_text()).body if isinstance(x,ast.FunctionDef)and x.name=='write_guard');scope=dict(Path=Path,os=os,OUT=O);exec(compile(ast.Module(body=[node],type_ignores=[]),str(guard),'exec'),scope);sys.addaudithook(scope['write_guard'])
 io=exact('v1438_small_atomic',R/'experiments/v1383_exact_timed_handoff/evidence_io.py');writers=exact('v1438_actual_planner_writer',C/'writer_budget.py');boundary=exact('v1438_actual_output_boundary',C/'bounded_io.py');jobs=exact('v1438_actual_planning_job',C/'planning_job.py');budget=exact('v1438_storage_preflight',C/'budget.py')
 parent_path=R/'runs/v1382_weekend_campaign/LEDGER.json';parent_before=parent_path.read_bytes();parent=json.loads(parent_before);assert parent['active_round']is None and not parent['models_now_authorized']
 limits=json.loads((C/'LIMITS.json').read_text());peak=budget.storage_preflight(limits)
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  out=O/'planner_writer_task';out.mkdir();identity=hashlib.sha256((O/'PLANNER_QUALIFICATION_CLAIM.json').read_bytes()).hexdigest()
  approval=dict(models_authorized=False,scope='ZERO_MODEL_PLANNER_WRITER_QUALIFICATION');io.atomic(out/'APPROVAL.json',approval)
  io.atomic(out/'EXTERNAL_WRITER_RESERVATIONS.json',dict(purpose=approval['scope'],source_identity=identity,approval_sha256=hashlib.sha256((out/'APPROVAL.json').read_bytes()).hexdigest(),writers={'PLANNER':dict(maximum_bytes=8*1024**2,source_hook_coverage_qualified=False)}))
  os.environ.update(PHASE_BOUNDED_TASK_OUTPUT=str(out),PHASE_BOUNDED_SOURCE_ID=identity,PHASE_BOUNDED_WRITER_ROLE='PLANNER')
  # The new qualification branch must require a PLANNER role and false
  # production coverage; no fake complete activation registry is manufactured.
  os.environ['PHASE_BOUNDED_WRITER_ROLE']='ACTUAL_ROS'
  try:writers.WriterBudget.from_environment()
  except AssertionError:pass
  else:raise AssertionError('SOFTWARE_PLANNER_AUTHORITY_ACCEPTED_FOREIGN_ROLE')
  os.environ['PHASE_BOUNDED_WRITER_ROLE']='PLANNER'
  parent_writer=writers.WriterBudget(out,role='ACTUAL_ROS',maximum_bytes=24*1024**2,source_identity=identity)
  task=json.loads((C/'TASKS.json').read_text())[0];assert task['case_id']=='WEST_EAST'and task['seed']==10060001
  known_path=R/'experiments/v855_renewal_worker/KNOWN_FIELD.json';known=json.loads(known_path.read_text())
  request=dict(known=known,body=[*task['start_xy'],task['start_yaw'],0.,0.],goal=task['goal_xy'],ball=None,guard=.22,planner_mode=task['planner_mode'],native_tick=0,sim_time=0.,software_public_map_input_only=True)
  job=jobs.PlanningJob(out/'planner_jobs',timeout_s=20.,hard_stop_monotonic=time.monotonic()+30)
  started=time.monotonic();result=None
  try:
   with boundary.OutputBoundary(out,parent_writer.reserve):
    job.start(request)
    while result is None:
     assert time.monotonic()-started<25,'NEW_PLANNER_WORKER_QUALIFICATION_TIMEOUT'
     result=job.poll();time.sleep(.01)
  finally:job.cancel()
  assert result['actual_cpu']==[4]and result['models']==result['physical_native']==0 and not result.get('functional_timeout',False)and 'error'not in result
  counter=json.loads((out/'WRITER_PLANNER_BYTES.json').read_text())
  assert counter['role']=='PLANNER'and counter['source_identity']==identity and 16384<counter['charged_bytes']<=8*1024**2
  assert any(name.endswith('result01.tmp')for name in counter['paths']),'PRODUCTION_CHILD_RESULT_NOT_CHARGED'
  assert (out/'planner_jobs/result01.json').is_file()and not(out/'planner_jobs/result01.tmp').exists()
  assert parent_path.read_bytes()==parent_before and not(O/'COMPLETE_INTEGRATED_ROUTE_QUALIFICATION.json').exists()and not(O/'ROUND_WINDOW.json').exists()
  proof=dict(passed=True,models=0,analytical_integrations=0,allocator_recomputations=0,physical_native=0,actual_replay_native=0,actual_parent_cpu=[2],actual_worker_cpu=result['actual_cpu'],original_writeguard=True,parent_constructor_step_compute_profile_guard=True,production_PlanningJob_and_CPU4_FFI_worker_executed_once=True,source_public_map_sha256=hashlib.sha256(known_path.read_bytes()).hexdigest(),source_FFI_library_sha256=hashlib.sha256((R/'runs/v1358_terminal_contract/libsearch.so').read_bytes()).hexdigest(),software_WE_start_and_public_map_only=True,actual_scan_or_wire_created=False,ROS_nodes=0,modelsfalse_coveragefalse_qualification_authority=True,foreign_role_refused=True,child_result_tmp_and_rename_charged=True,worker_result=result,child_writer_budget=counter,parent_pipe_writer_budget=json.loads(parent_writer.path.read_text()),all_runs_peak=peak,wall_s=time.monotonic()-started,actual_native_C_save_executed=False,complete_route_admission_absent=True,physical_admission=False,source_hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in C.iterdir()if p.is_file()})
  io.atomic(O/'PLANNER_QUALIFICATION.json',proof);print(json.dumps(proof))

if __name__=='__main__':main()
