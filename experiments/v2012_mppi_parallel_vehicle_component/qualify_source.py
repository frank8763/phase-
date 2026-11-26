"""Actual resource/CLI isolation checks; no plant/controller construction."""
from context import R,C,O,read,put,sha,load
import ast,json,os,subprocess,sys,time,traceback
def main():
 os.sched_setaffinity(0,{5});assert not(O/'SOURCE_ONCE.json').exists();put(O/'SOURCE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),models=0));files={};result=dict(passed=False,closed=False,models=0,algorithm_DLLs=0,controller_constructors=0,solver_queries=0,physics=0,replay=0)
 try:
  P=R/'runs/v2006_mppi_observed_dependency_scope';assert read(P/'POST_NUMERIC_STORAGE_BARRIER.json')['passed']and read(P/'RUNTIME_CLOSED_REVIEW.json')['passed']and read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered'];files.update(read(P/'SOURCE_FREEZE.json')['files']);prior=files.copy()
  old=R/'experiments/v1973_rpp_file_input_ready_barrier';unchanged=[]
  for name in ['capture.py','error_stop.py','resources.py','work.py','history_binding.py','response.py','evidence_service.py','generic_audit.py','observation.py']:
   assert(C/name).read_text()==(old/name).read_text().replace(old.name,C.name),name;unchanged.append(name)
  expected=(old/'runtime_binding.py').read_text().replace(old.name,C.name).replace("job['cpu']=2","job['cpu']=6").replace('224*1024**2','18*1024**2');assert expected==(C/'runtime_binding.py').read_text()
  original=(R/'experiments/v1067_causal_replan_brake_reserve/resource_policy.py').read_text();expected=original.replace("assert 2 in os.sched_getaffinity(0),'PHASE_CPU2_NOT_AVAILABLE'","assert 6 in os.sched_getaffinity(0),'PHASE_CPU6_NOT_AVAILABLE'").replace('os.sched_setaffinity(0,{2})','os.sched_setaffinity(0,{6})');assert expected==(C/'resource_policy.py').read_text()
  expected=(R/'experiments/v1615_private_namespace_scope/base_quota.py').read_text().replace("limits['maximum_task_evidence_bytes']==224*1024**2","limits['maximum_task_evidence_bytes']==18*1024**2").replace("limits['remaining_archive_download_reserve_bytes']==272*1024**2","limits['remaining_archive_download_reserve_bytes']==16*1024**2");assert expected==(C/'base_quota.py').read_text()
  assert(C/'granted_quota.py').read_text()==(R/'experiments/v1615_private_namespace_scope/quota.py').read_text().replace('==[2]','==[6]')
  rp=read(R/'experiments/v1370_overnight_controller_matrix/rpp_default_params.json')['local_costmap']['local_costmap']['ros__parameters'];mp=read(R/'experiments/v1344_causal_night_entry/coherent_mppi_causal_params.json')['local_costmap']['local_costmap']['ros__parameters']
  for key in ['footprint','footprint_padding','width','height','resolution','inflation_layer']:assert rp[key]==mp[key]
  expected=(R/'experiments/v1966_rpp_current_interface/current_map.py').read_text().replace('RPP','MPPI').replace('rpp','mppi').replace('experiments/v1370_overnight_controller_matrix/mppi_default_params.json','experiments/v1344_causal_night_entry/coherent_mppi_causal_params.json');assert expected==(C/'current_map.py').read_text()
  # Execute CPU policy in a separate actual process, with no simulation imports.
  script="import sys,os,json;sys.path.insert(0,"+repr(str(C))+");import cpu_policy;cpu_policy.install();os.sched_setaffinity(0,{2});assert os.sched_getaffinity(0)=={6};bad=[]\nfor pid,mask in [(1,{2}),(0,{8}),(0,{24})]:\n try:os.sched_setaffinity(pid,mask)\n except AssertionError:bad.append([pid,sorted(mask)])\n else:raise AssertionError('FORBIDDEN_RESOURCE_CHANGE_ACCEPTED')\nassert len(bad)==3;print(json.dumps(dict(passed=True,negative=bad,report=cpu_policy.report(),models=0)))"
  p=subprocess.run(['taskset','-c','6','/usr/bin/python3','-B','-c',script],cwd=R,capture_output=True,timeout=15);assert p.returncode==0,p.stderr.decode();cpu=json.loads(p.stdout);assert cpu['passed']and cpu['report']['actual_thread_affinities'];put(O/'CPU_POLICY_PROOF.json',cpu)
  # Per-lane lock is real; cross-owner acquisition must fail.
  import fcntl
  with(O/'execution.lock').open()as f:
   fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
   script="import fcntl;f=open("+repr(str(O/'execution.lock'))+");\ntry:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)\nexcept BlockingIOError:raise SystemExit(0)\nraise SystemExit(1)"
   assert subprocess.run(['taskset','-c','6','/usr/bin/python3','-B','-c',script],timeout=10).returncode==0
  env=dict(os.environ,PHASE_REPO=str(R),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
  p=subprocess.run(['taskset','-c','6','/usr/bin/python3','-B',str(C/'pilot_entry.py')],cwd=R,env=env,capture_output=True,timeout=10);assert p.returncode!=0 and b'MPPI_COMPONENT_NOT_ADMITTED'in p.stderr
  ros=load('source_exact_ros_namespace',R/'experiments/v856_nav2_foundation/ros_environment.py');env=ros.environment();env.update(CUDA_VISIBLE_DEVICES='',ROS_LOG_DIR='/tmp/source_mppi');env.pop('LD_PRELOAD',None);cmd=ros.command(['/usr/bin/python3.12','-I','-B','-S',str(C/'native_worker.py')]);i=cmd.index('--bind');assert cmd[i+1:i+3]==[str(R/'runs'),str(R/'runs')];cmd[i]='--ro-bind';p=subprocess.run(['taskset','-c','6',*cmd],cwd=R,env=env,capture_output=True,timeout=20);(O/'NATIVE_SOURCE_REFUSAL.console').write_bytes(p.stdout+p.stderr);lines=[json.loads(x[len(b'MPPI_CLOSED '):])for x in p.stdout.splitlines()if x.startswith(b'MPPI_CLOSED ')];assert p.returncode==1 and len(lines)==1 and lines[0]['constructors']==lines[0]['query_attempts']==0
  # The inherited exact OutputBoundary test is reused; the input codec is byte-identical except method labels/env.
  t=(C/'native_client.py').read_text();assert "cmd[i]='--ro-bind'"in t and "PHASE_COHERENT_NOISE='1'"in t and 'CPU6_inherited=True'in t
  limits=read(O/'LIMITS_DRAFT.json');assert limits['maximum_task_evidence_bytes']==18*1024**2 and limits['maximum_actual_native']==2410 and limits['maximum_replay_native']==2410
  task=read(O/'PILOT_TASK.json');assert task['maximum_control_native']==10 and task['stop_native']==2200 and task['component_not_navigation']
  for folder in [C,R/'experiments/v2013_mppi_vehicle_evidence']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for p in [O/n for n in ['PILOT_TASK.json','LIMITS_DRAFT.json','NATIVE_DEPENDENCIES.json','AUTHORIZATION.json','JOINT_RESOURCE_RESERVATION.json','CPU_POLICY_PROOF.json']]+[P/'POST_NUMERIC_STORAGE_BARRIER.json',P/'RUNTIME_CLOSED_REVIEW.json',R/'runs/v1973_rpp_file_input_ready_barrier/PILOT_TASK.json']:files[str(p.relative_to(R))]=sha(p)
  pins=read(O/'NATIVE_DEPENDENCIES.json');files.update(pins['repo_dependency_files']);assert all(sha(R/n)==h for n,h in files.items())
  proof=dict(passed=True,original_safety_modules_byte_exact=unchanged,original_predictor_and_resource_math_unchanged=True,task_quota_only_narrowed=True,CPU_actual_proof=cpu,actual_unadmitted_native_CLI_zero_constructor_query=True,actual_unadmitted_physical_CLI_before_model=True,duplicate_execution_lock_refused=True,current_map_formula_exact_and_original_parameter_values_equal=True,component_not_formal=True,algorithm_calls=0,physical_steps=0,prior_numeric_pass_preserved=True)
  put(O/'SOFTWARE_CHECK_PROOF.json',proof);files[str((O/'SOFTWARE_CHECK_PROOF.json').relative_to(R))]=sha(O/'SOFTWARE_CHECK_PROOF.json')
  put(O/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False));put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]));result.update(passed=True,source_members=len(files),proof=proof)
 except BaseException as e:
  result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(source_members_seen=len(files),models_authorized=False))
 finally:
  result['closed']=True;put(O/'SOURCE_QUALIFICATION.json',result);put(O/'SOURCE_OUTER_CLOSED.json',dict(closed=True,passed=result['passed'],models=0,constructors=0,queries=0))
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
