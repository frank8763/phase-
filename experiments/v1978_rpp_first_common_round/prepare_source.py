"""Once full RPP common01 admission proof; no new numerical constructors."""
from context import R,C,O,read,sha,put,load
import ast,fcntl,importlib.abc,os,runpy,subprocess,sys,time,traceback

def main():
 start=time.monotonic();assert not(O/'SOURCE_ONCE_CLAIM.json').exists();put(O/'SOURCE_ONCE_CLAIM.json',dict(unix=time.time(),models=0));files={};result=dict(passed=False,closed=False,models=0,explicit_RPP_DLL_loads=0,controller_constructors=0,solver_calls=0,physical_native=0,replay_native=0)
 try:
  prior=R/'runs/v1973_rpp_file_input_ready_barrier';assert read(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']and read(prior/'COMPONENT_POST_STORAGE_BARRIER.json')['passed'];files.update(read(prior/'SOURCE_FREEZE.json')['files'])
  component=read(prior/'COMPLETION.json');m=read(prior/'actual/RESULT.json');assert component['passed']and component['closed']and component['actual_native']==component['own_replay_native']==2210 and m['independent_audit']['passed']and m['replay']['passed']and not m['secondary_errors']and not m['first_error'];assert not component['whole_navigation_passed']
  for n,h in read(O/'PRIOR_CLOSED_BARRIERS.json')['proof_paths_SHA256'].items():assert sha(R/n)==h and read(R/n)['passed']
  software=read(O/'SOFTWARE_CHECK_PROOF.json');assert software['passed']and len(software['negative_frames'])==5 and len(software['navigation_branch_tests'])==4
  old=R/'experiments/v1922_dwa_five_admission_checked';unchanged=[]
  for n in ['capture.py','error_stop.py','resources.py','work.py','history_binding.py','runtime_binding.py','response.py','evidence_service.py','generic_audit.py']:
   expected=(old/n).read_text().replace('v1922_dwa_five_admission_checked',C.name).replace('v1923_dwa_five_checked_queue',C.name);assert expected==(C/n).read_text(),'ORIGINAL_SAFETY_MODULE_CHANGED:'+n;unchanged.append(n)
  folders=[C,R/'experiments/v1979_rpp_common_source_recovery',R/'experiments/v1980_rpp_common_runtime_recovery',R/'experiments/v1975_mppi_sync_api_preparation',R/'experiments/v1976_mppi_plugin_sync_api',R/'experiments/v1977_rpp_current_vehicle_runtime_recovery']
  for folder in folders:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for p in [prior/'COMPONENT_POST_STORAGE_BARRIER.json',prior/'COMPLETION.json',prior/'actual/RESULT.json',prior/'actual/FINAL_INDEPENDENT_AUDIT.json',R/'runs/v1977_rpp_current_vehicle_runtime_recovery/ARCHIVE_INDEX.json',R/'runs/v1977_rpp_current_vehicle_runtime_recovery/FULL_REMOTE_VERIFIED.json',R/'runs/v1976_mppi_plugin_sync_api/BUILD_RESULT.json',R/'runs/v1976_mppi_plugin_sync_api/libphase_mppi_sync.so']+[O/n for n in ['PILOT_TASK.json','LIMITS_DRAFT.json','NATIVE_DEPENDENCIES.json','PRIOR_CLOSED_BARRIERS.json','AUTHORIZATION.json','SOFTWARE_CHECK_PROOF.json','SOFTWARE_DEVELOPMENT_FAILURE_01.json']]:files[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in files.items());task=read(O/'PILOT_TASK.json');shared=next(row['task']for row in read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json')['tasks']if row['task']['task_id']==task['common_task_id'])
  for k in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id','initial_axis_motion_direction']:assert task[k]==shared[k]
  assert not task['component_not_navigation']and task['maximum_control_native']==57600 and read(O/'LIMITS_DRAFT.json')['maximum_actual_native']==60000
  ledger=read(R/'runs/v1805_common_algorithm_registry/LEDGER.json');assert all(not s['registered']and not s['closed']for s in ledger['slots']if s['method']=='RPP')
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
  assert 'automatic_successor=False'in(C/'campaign.py').read_text()
  proof=dict(passed=True,unchanged_original_safety_modules=unchanged,negative_cases=negative,original_RPP_binary_sha256=sha(R/'runs/v1943_rpp_synchronous_native_api/libphase_rpp_sync.so'),prior_real_current_vehicle_component_sha256=sha(prior/'COMPONENT_POST_STORAGE_BARRIER.json'),source_and_software_only=True,full_common_method_interface_gate_passed=True,first_actual_navigation_outcome_unknown=True,MPPI_build_only_not_runtime_qualified=True)
  put(O/'METHOD_ADMISSION_PROOF.json',proof);files[str((O/'METHOD_ADMISSION_PROOF.json').relative_to(R))]=sha(O/'METHOD_ADMISSION_PROOF.json');assert all(sha(R/n)==h for n,h in files.items())
  put(O/'SOURCE_FREEZE.json',dict(files=files,models_authorized=False));put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(prior.relative_to(R)),freeze_sha256=sha(prior/'SOURCE_FREEZE.json'),recovery_path=str((prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]));result.update(passed=True,source_members=len(files),software_proof=proof)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=files,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result)
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
