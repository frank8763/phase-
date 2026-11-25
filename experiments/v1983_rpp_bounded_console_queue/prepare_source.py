"""Once full RPP common01 admission proof; no new numerical constructors."""
from context import R,C,O,read,sha,put,load
import ast,fcntl,importlib.abc,os,runpy,subprocess,sys,time,traceback

def main():
 start=time.monotonic();assert not(O/'SOURCE_ONCE_CLAIM.json').exists();put(O/'SOURCE_ONCE_CLAIM.json',dict(unix=time.time(),models=0));files={};result=dict(passed=False,closed=False,models=0,explicit_RPP_DLL_loads=0,controller_constructors=0,solver_calls=0,physical_native=0,replay_native=0)
 try:
  prior=R/'runs/v1978_rpp_first_common_round';assert read(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']and read(prior/'POST_ROUND_STORAGE_BARRIER.json')['passed'];files.update(read(prior/'SOURCE_FREEZE.json')['files'])
  component=read(prior/'COMPLETION.json');m=read(prior/'actual/RESULT.json');assert component['closed']and component['actual_native']==component['own_replay_native']==1015 and m['independent_audit']['passed']and m['replay']['passed'];assert component['machine_first_error']['error']=="AssertionError('RPP_PEER_CONSOLE_CAP')"and not component['whole_navigation_passed']
  for name in ['CONSOLE_SOFTWARE_PROOF.json','LIVE_WAIT_SOFTWARE_PROOF.json','DICTIONARY_SOFTWARE_PROOF.json','QUEUE_SOFTWARE_PROOF.json']:assert read(O/name)['passed']
  assert read(O/'CONSOLE_REPRODUCTION.json')['reproduced']and read(O/'CONSOLE_SOFTWARE_PROOF.json')['stress_queries']==12000
  for n,h in read(O/'PRIOR_CLOSED_BARRIERS.json')['proof_paths_SHA256'].items():assert sha(R/n)==h and read(R/n)['passed']
  software=read(O/'SOFTWARE_CHECK_PROOF.json');assert software['passed']and len(software['negative_frames'])==5 and len(software['navigation_branch_tests'])==4
  old=R/'experiments/v1922_dwa_five_admission_checked';unchanged=[]
  for n in ['capture.py','error_stop.py','resources.py','work.py','history_binding.py','runtime_binding.py','response.py','evidence_service.py','generic_audit.py']:
   expected=(old/n).read_text().replace('v1922_dwa_five_admission_checked',C.name).replace('v1923_dwa_five_checked_queue',C.name);assert expected==(C/n).read_text(),'ORIGINAL_SAFETY_MODULE_CHANGED:'+n;unchanged.append(n)
  folders=[C,R/'experiments/v1984_rpp_night_source_recovery',R/'experiments/v1986_rpp_night_runtime_recovery',R/'experiments/v1981_mppi_static_runtime_inputs',R/'experiments/v1982_rpp_night_queue_proposal',R/'experiments/v1985_verified_cloud_transport_cleanup']
  for folder in folders:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for p in [prior/'POST_ROUND_STORAGE_BARRIER.json',prior/'COMPLETION.json',prior/'RUNTIME_CLOSED_REVIEW.json',prior/'actual/RESULT.json',prior/'actual/FINAL_INDEPENDENT_AUDIT.json',R/'runs/v1985_verified_cloud_transport_cleanup/RESULT.json',R/'runs/v1985_verified_cloud_transport_cleanup/ELIGIBLE_MANIFEST.json',R/'runs/v1981_mppi_static_runtime_inputs/RESULT.json']+[O/n for n in ['PLAN_LOCKED.json','LIMITS_DRAFT.json','NATIVE_DEPENDENCIES.json','PRIOR_CLOSED_BARRIERS.json','AUTHORIZATION.json','SOFTWARE_CHECK_PROOF.json','CONSOLE_REPRODUCTION.json','CONSOLE_SOFTWARE_PROOF.json','LIVE_WAIT_SOFTWARE_PROOF.json','DICTIONARY_SOFTWARE_PROOF.json','QUEUE_SOFTWARE_PROOF.json','CONSOLE_DEVELOPMENT_FAILURE_01.json','SOFTWARE_DEVELOPMENT_FAILURE_02.json','DICTIONARY_DEVELOPMENT_CHECK_01.json']]:files[str(p.relative_to(R))]=sha(p)
  plan=read(O/'PLAN_LOCKED.json')['assignments'];assert len(plan)==11 and [v['round_id']for v in plan]==[f'common_{i:02d}__RPP'for i in range(2,13)]
  for row in plan:
   task=read(R/row['task_path']);shared=next(r['task']for r in read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json')['tasks']if r['task']['task_id']==task['common_task_id'])
   for k in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id','initial_axis_motion_direction']:assert task[k]==shared[k]
   assert task['task_id']==row['round_id']and not task['component_not_navigation']and task['maximum_control_native']==57600 and read(O/'LIMITS_DRAFT.json')['maximum_actual_native']==60000
   files[row['task_path']]=sha(R/row['task_path'])
  assert all(sha(R/n)==h for n,h in files.items());ledger=read(R/'runs/v1805_common_algorithm_registry/LEDGER.json')
  for row in plan:
   slot=next(s for s in ledger['slots']if s['method']=='RPP'and s['task_id']==row['common_task']);assert not slot['registered']and not slot['closed']
  class Ban(importlib.abc.MetaPathFinder):
   def find_spec(self,name,*args):
    if name.split('.')[0]in {'numpy','mujoco','torch','rclpy','kernel','vehicle','factory','planner','fast_predict'}:raise AssertionError('SOURCE_NO_MODEL:'+name)
  sys.meta_path.insert(0,Ban());negative=[]
  try:runpy.run_path(str(C/'pilot_entry.py'),run_name='__main__')
  except AssertionError as e:assert str(e)=='RPP_COMPONENT_NOT_ADMITTED';negative.append('real_physical_CLI_before_model')
  else:raise AssertionError('PHYSICAL_CLI_ACCEPTED')
  binding=load('RPP_production_binding_source_check',C/'binding.py')
  try:binding.bind(files)
  except FileNotFoundError:negative.append('native_binding_before_RPP_DLL')
  else:raise AssertionError('UNADMITTED_RPP_DLL')
  ros=load('RPP_original_ros_namespace_source_only',R/'experiments/v856_nav2_foundation/ros_environment.py');env=ros.environment();env.update(ROS_LOG_DIR='/tmp/phase_source_logs',CUDA_VISIBLE_DEVICES='');cmd=ros.command(['/usr/bin/python3.12','-I','-B','-S',str(C/'native_worker.py')]);i=cmd.index('--bind');cmd[i]='--ro-bind';p=subprocess.run(cmd,cwd=R,env=env,capture_output=True,timeout=20);(O/'NATIVE_CLI_SOURCE.console').write_bytes(p.stdout+p.stderr);lines=[__import__('json').loads(line[len(b'RPP_CLOSED '):])for line in p.stdout.splitlines()if line.startswith(b'RPP_CLOSED ')];assert p.returncode==1 and len(lines)==1 and lines[0]['constructors']==lines[0]['query_attempts']==0;negative.append('actual_isolated_ROS_peer_no_admission_no_RPP_DLL')
  assert "fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)"in(C/'driver.py').read_text()and "ownerlock"in(C/'owner.py').read_text()
  assert 'can_continue(review)'in(C/'campaign.py').read_text()and "'SOURCE_FREEZE.json'"in(C/'campaign.py').read_text()
  proof=dict(passed=True,unchanged_original_safety_modules=unchanged,negative_cases=negative,original_RPP_binary_sha256=sha(R/'runs/v1943_rpp_synchronous_native_api/libphase_rpp_sync.so'),prior_closed_runtime_barrier_sha256=sha(prior/'POST_ROUND_STORAGE_BARRIER.json'),source_and_software_only=True,full_common_method_interface_gate_passed=True,first_actual_navigation_outcome_unknown=True,MPPI_not_runtime_qualified=True,remaining_fixed_common_tasks=11,original_common01_technical_failure_not_retried=True,exact_lossless_console_and_static_path_transport=True,new_round_cache_cleanup_only_after_actual_remote_SHA=True)
  put(O/'METHOD_ADMISSION_PROOF.json',proof);files[str((O/'METHOD_ADMISSION_PROOF.json').relative_to(R))]=sha(O/'METHOD_ADMISSION_PROOF.json');assert all(sha(R/n)==h for n,h in files.items())
  put(O/'SOURCE_FREEZE.json',dict(files=files,models_authorized=False));put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(prior.relative_to(R)),freeze_sha256=sha(prior/'SOURCE_FREEZE.json'),recovery_path=str((prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]));result.update(passed=True,source_members=len(files),software_proof=proof)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=files,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result)
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
