"""Once no-model SOURCE proof for current RPP interface and exact old gates."""
from context import R,C,O,read,sha,put,load
import ast,copy,fcntl,importlib.abc,os,runpy,subprocess,sys,time,traceback

def main():
 start=time.monotonic();assert not(O/'SOURCE_ONCE_CLAIM.json').exists();put(O/'SOURCE_ONCE_CLAIM.json',dict(unix=time.time(),models=0));files={};result=dict(passed=False,closed=False,models=0,explicit_RPP_DLL_loads=0,controller_constructors=0,solver_calls=0,physical_native=0,replay_native=0)
 try:
  prior=R/'runs/v1968_rpp_current_vehicle_component';assert read(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']and read(prior/'COMPONENT_POST_STORAGE_BARRIER.json')['passed'];files.update(read(prior/'SOURCE_FREEZE.json')['files'])
  for n,h in read(O/'PRIOR_CLOSED_BARRIERS.json')['proof_paths_SHA256'].items():assert sha(R/n)==h and read(R/n)['passed']
  software=read(R/'runs/v1966_rpp_current_interface/SOFTWARE_RESULT.json');assert software['passed']and len(software['map']['negative_cases'])==9 and len(software['map']['cases'])==8
  old=R/'experiments/v1922_dwa_five_admission_checked';unchanged=[]
  for n in ['capture.py','error_stop.py','resources.py','work.py','history_binding.py','runtime_binding.py','response.py','evidence_service.py','generic_audit.py']:
   expected=(old/n).read_text().replace('v1922_dwa_five_admission_checked',C.name).replace('v1923_dwa_five_checked_queue',C.name);assert expected==(C/n).read_text(),'ORIGINAL_SAFETY_MODULE_CHANGED:'+n;unchanged.append(n)
  for folder in [C,R/'experiments/v1966_rpp_current_interface',R/'experiments/v1967_remaining_method_cpu_preparation',R/'experiments/v1974_rpp_file_input_ready_source_recovery']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for folder in [R/'experiments/v855_renewal_worker',R/'experiments/v1370_overnight_controller_matrix']:
   for p in folder.glob('*.py'):files[str(p.relative_to(R))]=sha(p)
  for p in [R/'runs/v1971_rpp_file_input_component/SOURCE_QUALIFICATION.json',R/'runs/v1971_rpp_file_input_component/FAILED_SOURCE_FREEZE.json',R/'runs/v1971_rpp_file_input_component/SOURCE_OUTER_CLOSED.json',R/'experiments/v1331_common_static_map/PUBLIC_STATIC_GRID.json',R/'experiments/v1370_overnight_controller_matrix/rpp_default_params.json',R/'experiments/v1938_current_causal_solver_wire/wire.py',R/'runs/v1966_rpp_current_interface/SOFTWARE_RESULT.json',R/'runs/v1967_remaining_method_cpu_preparation/RESULT.json']+[O/n for n in ['PILOT_TASK.json','LIMITS_DRAFT.json','NATIVE_DEPENDENCIES.json','PRIOR_CLOSED_BARRIERS.json','AUTHORIZATION.json']]:files[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in files.items());task=read(O/'PILOT_TASK.json');original=read(R/'runs/v1639_original_evidence_stages/PILOT_TASK.json')
  for k in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id']:assert task[k]==original[k]
  assert task['component_not_navigation']and task['maximum_control_native']==10 and read(O/'LIMITS_DRAFT.json')['maximum_actual_native']==2410
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
  # Exact persistent peer real CLI with no admission; readonly namespace, RPP DLL remains uncalled.
  ros=load('RPP_original_ros_namespace_source_only',R/'experiments/v856_nav2_foundation/ros_environment.py');env=ros.environment();env.update(ROS_LOG_DIR='/tmp/phase_source_logs',CUDA_VISIBLE_DEVICES='');cmd=ros.command(['/usr/bin/python3.12','-I','-B','-S',str(C/'native_worker.py')]);i=cmd.index('--bind');cmd[i]='--ro-bind';p=subprocess.run(cmd,cwd=R,env=env,capture_output=True,timeout=20);(O/'NATIVE_CLI_SOURCE.console').write_bytes(p.stdout+p.stderr);lines=[__import__('json').loads(line[len(b'RPP_CLOSED '):])for line in p.stdout.splitlines()if line.startswith(b'RPP_CLOSED ')];assert p.returncode==1 and len(lines)==1 and lines[0]['constructors']==lines[0]['query_attempts']==0;negative.append('actual_isolated_ROS_peer_no_admission_no_RPP_DLL')
  # Ensure model and source isolation in actual argv, not a flag alone.
  client=(C/'native_client.py').read_text();assert "cmd[i]='--ro-bind'"in client and 'subprocess.PIPE'in client and "env.update(ROS_DOMAIN_ID='196',ROS_LOG_DIR='/tmp/phase_rpp_logs'"in client
  assert "fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)"in(C/'driver.py').read_text()
  from qualify_transport import check
  transport=check();put(O/'TRANSPORT_SOFTWARE_PROOF.json',transport)
  proof=dict(passed=True,exact_output_boundary_file_input_transport=transport,unchanged_original_safety_modules=unchanged,map_software_sha256=sha(R/'runs/v1966_rpp_current_interface/SOFTWARE_RESULT.json'),negative_cases=negative,original_RPP_binary_sha256=sha(R/'runs/v1943_rpp_synchronous_native_api/libphase_rpp_sync.so'),readonly_ROS_peer_pipe_only=True,source_only=True,complete_vehicle_runtime_qualified=False)
  put(O/'SOFTWARE_CHECK_PROOF.json',proof);files[str((O/'SOFTWARE_CHECK_PROOF.json').relative_to(R))]=sha(O/'SOFTWARE_CHECK_PROOF.json');files[str((O/'TRANSPORT_SOFTWARE_PROOF.json').relative_to(R))]=sha(O/'TRANSPORT_SOFTWARE_PROOF.json');assert all(sha(R/n)==h for n,h in files.items())
  put(O/'SOURCE_FREEZE.json',dict(files=files,models_authorized=False));put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(prior.relative_to(R)),freeze_sha256=sha(prior/'SOURCE_FREEZE.json'),recovery_path=str((prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]));result.update(passed=True,source_members=len(files),software_proof=proof)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=files,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);put(O/'SOURCE_OUTER_CLOSED.json',dict(passed=result['passed'],closed=True,models=0,software_only=True))
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
