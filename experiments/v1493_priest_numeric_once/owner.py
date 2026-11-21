"""Prepare software input once, then a separately admitted exact numeric owner."""
import argparse
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
common=exact('v1493_frozen_worker_common',R/'experiments/v1492_priest_optimizer_worker/common.py')
put=common.put;read=common.read;sha=common.sha;digest=common.digest

def prepare():
 with(O/'PREPARE_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models=0),f)
 assert sorted(os.sched_getaffinity(0))==[4]and os.environ.get('PHASE_REPO')==str(R)
 parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and not parent['models_now_authorized']
 try:
  with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   freeze=read(common.O/'SOURCE_FREEZE.json');assert freeze['entry_passed']and read(common.O/'ENTRY_QUALIFICATION.json')['passed']
   sources=freeze['files'].copy();assert all(sha(R/n)==h for n,h in sources.items())
   old=R/'experiments/v1485_priest_current_polynomial_seam'
   prepared=exact('v1493_existing_prepared_core',old/'core_identity.py').PreparedCore(source_manifest=sources)
   boundary=exact('v1493_original_boundary_hint',old/'causal_boundary.py')
   full=dict(time=0.,qpos=[.3,0.,0.,1.,0.,0.,0.],qvel=[0.]*6,ctrl=[0.]*4,mocap_pos=[],mocap_quat=[])
   origin=dict(body=[.3,0.,0.,0.,0.],body_lateral=0.,native_tick=0,sim_time=0.,steering=dict(position=[0.,0.],velocity=[0.,0.]),controller_memory=dict(last_ctrl=[0.]*4,integral=0.),parked_target=None,steering_motion_active=False,coupled_episode=False)
   snapshot=dict(model='PERIODIC',online_actor_truth=False,periodic=None,last_observed_time=None)
   current=dict(kind='PHASE_PRIEST_CURRENT_POLYNOMIAL_INPUT',schema=1,run_id='V1493_SOFTWARE_ONLY_NOT_ACTUAL_INPUT',software_fixture_not_actual=True,origin=origin,fullstate=full,fullstate_sha256=digest(full),fixed_origin_native=0,fixed_origin_sim_time=0.,rear_pose_world=[0.,0.,0.],rear_velocity_world=[0.,0.],author_initial_boundary_hint=boundary.initial_hint(full,None,native_tick=0),core_identity_sha256=prepared.identity_sha256,core_identity=prepared.value,source_manifest_sha256=prepared.source_manifest_sha256,public_map_sha256=prepared.public_map_sha256,causal_snapshot=snapshot,causal_snapshot_sha256=digest(snapshot),causal_forecast=None,observation_stage='NO_DYNAMIC_RETURN_YET_NO_MEASURED_FUTURE',gear_memory=dict(gear=0,brake_start=None,last_tick=-1),next_segment=dict(gear=1,poses=[[0.,0.,0.],[1.,0.,0.]]),proposal_only=True,physical_admission=False)
   current['input_sha256']=digest(current);initial=boundary.boundary_state(current)
   port=exact('v1493_frozen_port_source',R/'experiments/v1487_priest_optimizer_contract/cpu_source.py').prepare_cpu_source();port.pop('source')
   request=exact('v1493_actual_request_builder',R/'experiments/v1487_priest_optimizer_contract/optimizer_request.py').build(current,prepared=prepared,boundary_state=initial,port_identity=port)
   assert request['constructor_kwargs']['num_obs_2']==0 and request['initial_state']==[0.]*6
   task=O/'numeric';task.mkdir();put(task/'CURRENT_INPUT.json',current);put(task/'OPTIMIZER_REQUEST.json',request);put(task/'SOURCE_MANIFEST.json',sources)
   numerical=sources.copy()
   for p in C.iterdir():
    if p.is_file():numerical[str(p.relative_to(R))]=sha(p)
   put(O/'NUMERIC_SOURCE_FREEZE.json',dict(files=numerical,worker_source_freeze_sha256=sha(common.O/'SOURCE_FREEZE.json'),worker_manifest_sha256=digest(sources),models=0,software_input_only=True,optimizer_executed=False))
   put(O/'FIXED_INPUTS.json',dict(input_sha256=current['input_sha256'],request_sha256=request['request_sha256'],input_file_sha256=sha(task/'CURRENT_INPUT.json'),request_file_sha256=sha(task/'OPTIMIZER_REQUEST.json'),software_fixture_not_actual=True,models=0,optimizer_calls=0))
   put(O/'PREPARATION_COMPLETION.json',dict(passed=True,closed=True,models=0,optimizer_calls=0,JAX_author_imported=False,real_current_capture=False,source_frozen=True))
 except BaseException as e:put(O/'PREPARATION_ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),models=0));raise

def usage():
 seen=set();total=0
 for root,dirs,files in os.walk(R/'runs',followlinks=False):
  for p in [Path(root)]+[Path(root)/n for n in files]:
   st=p.lstat();key=(st.st_dev,st.st_ino)
   if key not in seen:seen.add(key);total+=st.st_blocks*512
 return total

def launch():
 assert sorted(os.sched_getaffinity(0))==[4]and os.environ.get('PHASE_REPO')==str(R)
 assert not(O/'NUMERIC_ONCE_CLAIM.json').exists()and read(O/'PREPARATION_COMPLETION.json')['passed']
 source=read(O/'NUMERIC_SOURCE_FREEZE.json');assert all(sha(R/n)==h for n,h in source['files'].items())
 recovery=read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['numeric_source_freeze_sha256']==sha(O/'NUMERIC_SOURCE_FREEZE.json')
 assert read(R/'runs/v1382_weekend_campaign/LEDGER.json')['active_round']is None
 before=usage();peak=before+560*1024**2;assert peak<10*1024**3,'NUMERIC_FULL_EVIDENCE_ARCHIVE_ROOT_PEAK_REFUSED'
 task=O/'numeric';current=read(task/'CURRENT_INPUT.json');request=read(task/'OPTIMIZER_REQUEST.json');start=time.monotonic();end=min(start+600,start+1795395600-time.time())
 authority=dict(scope='PRIEST_OPTIMIZER_ONLY',mode='OPTIMIZER',models_authorized=False,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),source_manifest_sha256=source['worker_manifest_sha256'],input_sha256=current['input_sha256'],request_sha256=request['request_sha256'],kernel_source_sha256=request['port_identity']['ported_sha256'],dependency_index_sha256=sha(R/'runs/v1491_priest_dependency_target/EXTRACTED_INDEX.json'),dependency_remote_proof_sha256=sha(R/'runs/v1490_priest_dependency_recovery/FULL_REMOTE_VERIFIED.json'),qualified_distribution_versions={'jax':'0.4.30','jaxlib':'0.4.30','numpy':'2.2.6','scipy':'1.14.1','matplotlib':'3.10.9'},optimizer_writer_maximum_bytes=2*1024**2,absolute_deadline_unix=min(time.time()+600,1795395600),hard_stop_monotonic=end,software_current_input_only=True)
 claim=dict(started_unix=time.time(),authority=authority,full_reserved_peak_bytes=peak,models=0)
 with(O/'NUMERIC_ONCE_CLAIM.json').open('x')as f:json.dump(claim,f)
 put(task/'APPROVAL.json',authority);put(R/'runs/v1487_priest_optimizer_contract/OPTIMIZER_ONLY_ADMISSION.json',authority)
 put(task/'CURRENT_SOURCE_REMOTE_RECOVERY.json',dict(passed=True,source_freeze_sha256=source['worker_source_freeze_sha256'],actual_delta_proof=recovery))
 result=dict(passed=False,closed=False,scope='ONCE_SOFTWARE_INPUT_REAL_CPU_PRIEST_PROPOSAL',models=0,physical_native=0,optimizer_calls=None,optimizer_work_unknown=True)
 try:
  sandbox=exact('v1493_frozen_bounded_sandbox',R/'experiments/v1492_priest_optimizer_worker/sandbox.py')
  writer=exact('v1493_exact_parent_budget',R/'experiments/v1436_pathlib_control_rename/writer_budget.py').WriterBudget(task,role='SUPERVISOR_LOG',maximum_bytes=8*1024**2,source_identity=source['worker_manifest_sha256'])
  proof=sandbox.run(task,mode='OPTIMIZER',writer=writer,wall_s=max(1,end-time.monotonic()-2));put(O/'WORKER_RESULT.json',proof)
  terminal=proof['terminal']['result'];result.update(passed=proof['returncode']==0 and terminal['passed'],worker_returncode=proof['returncode'],inner_result=terminal,optimizer_calls=terminal.get('optimizer_calls'),optimizer_work_unknown=not terminal.get('passed',False),first_error=terminal.get('original_error'))
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  result.update(closed=True,wall_s=time.monotonic()-start,source_unchanged=all(sha(R/n)==h for n,h in source['files'].items()),software_current_input_not_actual=True,actual_control_domain_qualified=False,whole_route_passed=False)
  put(O/'COMPLETION.json',result)
 return 0 if result['passed']else 1

if __name__=='__main__':
 if '--prepare'in sys.argv:prepare()
 elif '--launch'in sys.argv:raise SystemExit(launch())
 else:raise RuntimeError('EXPLICIT_PREPARE_OR_ONCE_LAUNCH_SCOPE_REQUIRED')
