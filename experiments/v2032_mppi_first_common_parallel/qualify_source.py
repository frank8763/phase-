"""First formal MPPI CPU6 source/owner admission; zero algorithm constructors."""
from context import R,C,O,read,put,sha,load
from pathlib import Path
import ast,json,os,subprocess,time,traceback
def main():
 os.sched_setaffinity(0,{5});assert not(O/'SOURCE_ONCE.json').exists();put(O/'SOURCE_ONCE.json',dict(unix=time.time(),models=0));files={};result=dict(passed=False,closed=False,models=0,algorithm_DLLs=0,controller_constructors=0,optimizer_queries=0,physics=0,replay=0)
 try:
  P=R/'runs/v2027_mppi_journal_snapshot_consistency';old=R/'experiments/v2027_mppi_journal_snapshot_consistency';F=R/'experiments/v1990_rpp_unexecuted_output_audit';H=R/'experiments/v2033_mppi_first_common_evidence'
  assert read(P/'SOURCE_QUALIFICATION.json')['passed']and read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']and read(P/'COMPONENT_POST_STORAGE_BARRIER.json')['passed']and read(P/'COMPLETION.json')['passed'];files.update(read(P/'SOURCE_FREEZE.json')['files']);prior=files.copy();same=[]
  for n in ['capture.py','error_stop.py','resources.py','work.py','history_binding.py','response.py','evidence_service.py','generic_audit.py','observation.py','resource_policy.py','cpu_policy.py','granted_quota.py','current_map.py']:
   assert(C/n).read_text()==(old/n).read_text().replace(old.name,C.name),'ORIGINAL_COMPONENT_SAFETY_BODY_CHANGED:'+n;same.append(n)
  expected=(old/'runtime_binding.py').read_text().replace(old.name,C.name).replace('18*1024**2','224*1024**2');assert(C/'runtime_binding.py').read_text()==expected
  expected=(old/'base_quota.py').read_text().replace(old.name,C.name).replace('18*1024**2','224*1024**2').replace('16*1024**2','272*1024**2');assert(C/'base_quota.py').read_text()==expected
  expected=(F/'navigation.py').read_text().replace(F.name,C.name).replace('RPP','MPPI').replace('rpp','mppi').replace("R/'experiments/v1966_mppi_current_interface/current_map.py'","C/'current_map.py'");assert(C/'navigation.py').read_text()==expected
  expected=(F/'audit_component.py').read_text().replace(F.name,C.name).replace('RPP','MPPI').replace('rpp','mppi').replace("R/'experiments/v1966_mppi_current_interface/current_map.py'","C/'current_map.py'");assert(C/'audit_component.py').read_text()==expected
  for n in ['messages.py','request_dictionary.py','console_codec.py']:assert(C/n).read_bytes()==(F/n).read_bytes()
  software=read(O/'SOFTWARE_CHECK_PROOF.json');assert software['passed']and len(software['negative_frames'])==5 and len(software['navigation_branch_tests'])==4
  rng=read(R/'runs/v2034_mppi_original_rng_object/BUILD_RESULT.json');assert rng['passed']and rng['actual_algorithm_DLLs']==rng['actual_controller_constructors']==rng['actual_optimizer_queries']==0
  seeds=read(O/'RNG_SCHEDULE_LOCKED.json');assert len(seeds['assignments'])==12
  import hashlib
  for row in seeds['assignments']:
   expected=hashlib.sha256(('PHASE_COMMON_MPPI_RNG_V1\0'+row['task_id']).encode()).hexdigest();assert row['derivation_sha256']==expected and row['seed32']==int(expected[:8],16)
  task=read(O/'PILOT_TASK.json');registered=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');original=registered['tasks'][0]['task']
  for k in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id','initial_axis_motion_direction']:assert task[k]==original[k]
  assert task['task_id']=='common_01__MPPI'and task['maximum_control_native']==57600 and task['native_limit']==60000 and task['stop_native']==2200 and not task['component_not_navigation']
  limits=read(O/'LIMITS_DRAFT.json');assert limits['maximum_actual_native']==limits['maximum_replay_native']==60000 and limits['maximum_task_evidence_bytes']==224*1024**2
  # Real independent entry refuses before any physical import/namespace spawn.
  env=dict(os.environ,PHASE_REPO=str(R),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
  p=subprocess.run(['taskset','-c','6','/usr/bin/python3','-B',str(C/'run_phase.py')],cwd=R,env=env,capture_output=True,timeout=10);assert p.returncode!=0 and b'MPPI_INDEPENDENT_PHASE_NOT_ADMITTED'in p.stderr
  p=subprocess.run(['taskset','-c','6','/usr/bin/python3','-B',str(C/'pilot_entry.py')],cwd=R,env=env,capture_output=True,timeout=10);assert p.returncode!=0 and b'MPPI_COMPONENT_NOT_ADMITTED'in p.stderr
  # Exact Phase namespace with only this qualification scratch writable.
  entry=load('independent_Phase_scope_source',C/'run_phase.py');scratch=O/'namespace_software';scratch.mkdir();cmd=entry.namespace(C/'pilot_entry.py',scratch);position=next(i for i,x in enumerate(cmd)if x.endswith('/envs/mk_mujoco/bin/python'))
  script="import pathlib,os,json;out=pathlib.Path("+repr(str(scratch))+");out.joinpath('PASS').write_text('software-only');blocked=[]\nfor p in [pathlib.Path("+repr(str(C/'FORBIDDEN_WRITE'))+"),pathlib.Path("+repr(str(P/'FORBIDDEN_WRITE'))+")]:\n try:p.write_text('forbidden')\n except OSError:blocked.append(str(p))\n else:raise AssertionError('CROSS_SCOPE_WRITE_ALLOWED')\nassert os.sched_getaffinity(0)=={6}and len(blocked)==2;print(json.dumps(dict(passed=True,CPU=6,blocked=blocked,models=0)))"
  probe=cmd[:position]+[cmd[position],'-B','-c',script];p=subprocess.run(['taskset','-c','6',*probe],cwd=R,env=env,capture_output=True,timeout=20);assert p.returncode==0,p.stderr.decode();namespace=json.loads(p.stdout);put(O/'NAMESPACE_SOFTWARE_PROOF.json',namespace)
  # Real readonly native CLI without authority has no DLL/seed/constructor calls.
  ros=load('unchanged_ROS_namespace_source',R/'experiments/v856_nav2_foundation/ros_environment.py');env=ros.environment();env.update(CUDA_VISIBLE_DEVICES='',ROS_LOG_DIR='/tmp/source_mppi');env.pop('LD_PRELOAD',None);cmd=ros.command(['/usr/bin/python3.12','-I','-B','-S',str(C/'native_worker.py')]);i=cmd.index('--bind');cmd[i]='--ro-bind';p=subprocess.run(['taskset','-c','6',*cmd],cwd=R,env=env,capture_output=True,timeout=20);(O/'NATIVE_SOURCE_REFUSAL.console').write_bytes(p.stdout+p.stderr);closed=[json.loads(x[len(b'MPPI_CLOSED '):])for x in p.stdout.splitlines()if x.startswith(b'MPPI_CLOSED ')];assert p.returncode==1 and len(closed)==1 and closed[0]['constructors']==closed[0]['query_attempts']==0
  # Exercise append-only registration overlay/duplicate refusal only on scratch.
  events=load('new_parallel_method_events_software',C/'parallel_events.py');temporary=O/'events_software';temporary.mkdir();events.EVENTS=temporary
  claim=dict(method='MPPI',task_id='common_01',registered=True,closed=False);fake=temporary/'common_01__MPPI.REGISTERED.json';events.write_once(fake,claim)
  try:events.write_once(fake,claim)
  except FileExistsError:duplicate_refused=True
  else:raise AssertionError('DUPLICATE_PARALLEL_EVENT_ACCEPTED')
  combined=events.combined();assert combined['denominator']==120 and combined['parallel_events_authoritative_until_base_consolidation']
  assert not(R/'runs/v1805_common_algorithm_registry/PARALLEL_METHOD_EVENTS/common_01__MPPI.REGISTERED.json').exists()
  # Source path inventory catches accidental global method-name rewrites.
  missing=[]
  for p in C.glob('*.py'):
   tree=ast.parse(p.read_text())
   for node in ast.walk(tree):
    if isinstance(node,ast.BinOp)and isinstance(node.op,ast.Div)and isinstance(node.left,ast.Name)and node.left.id=='R'and isinstance(node.right,ast.Constant)and isinstance(node.right.value,str):
     n=node.right.value
     if n.startswith(('runs/','experiments/','runtime/'))and not(R/n).exists()and 'PARALLEL_METHOD_EVENTS'not in n:missing.append((p.name,n))
  assert not missing,missing
  for folder in [C,H,R/'experiments/v2031_mppi_registered_rng_binding',R/'experiments/v2034_mppi_original_rng_object',R/'experiments/v2030_closed_dwa_derived_cache_cleanup']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for folder in [R/'runs/v2030_closed_dwa_derived_cache_cleanup',R/'runs/v2034_mppi_original_rng_object']:
   for p in folder.glob('*.json'):files[str(p.relative_to(R))]=sha(p)
  for p in [O/n for n in ['PILOT_TASK.json','LIMITS_DRAFT.json','NATIVE_DEPENDENCIES.json','AUTHORIZATION.json','JOINT_RESOURCE_RESERVATION.json','PLAN_LOCKED.json','RNG_SCHEDULE_LOCKED.json','SOFTWARE_CHECK_PROOF.json','NAMESPACE_SOFTWARE_PROOF.json']]+[P/n for n in ['SOURCE_QUALIFICATION.json','COMPLETION.json','COMPONENT_POST_STORAGE_BARRIER.json','RUNTIME_CLOSED_REVIEW.json']]+[R/'runs/v2031_mppi_registered_rng_binding/BUILD_RESULT.json']:
   files[str(p.relative_to(R))]=sha(p)
  files.update(read(O/'NATIVE_DEPENDENCIES.json')['repo_dependency_files']);assert all(sha(R/n)==h for n,h in files.items())
  proof=dict(passed=True,original_component_safety_modules_same=same,original_full_RPP_navigation_and_audit_only_method_labels_and_MPPI_frontend_source_changed=True,full_route_software_branch_proof_sha256=sha(O/'SOFTWARE_CHECK_PROOF.json'),only_own_output_writable_actual_namespace_proof=namespace,unadmitted_actual_Phase_and_native_CLI_zero_models_algorithms=True,append_only_parallel_registration_duplicate_refused=duplicate_refused,synthetic_combined_denominator=120,actual_common_slots_claimed=0,old_zero_component_not_repeated=True,actual_RNG_helper_binding_before_constructor_required=True,task_parameters_original_exact=True,scientific_outcome_pending=True)
  put(O/'METHOD_ADMISSION_PROOF.json',proof);files[str((O/'METHOD_ADMISSION_PROOF.json').relative_to(R))]=sha(O/'METHOD_ADMISSION_PROOF.json')
  put(O/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False));put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]));result.update(passed=True,source_members=len(files),proof=proof)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(source_members_seen=len(files),models_authorized=False))
 finally:result['closed']=True;put(O/'SOURCE_QUALIFICATION.json',result);put(O/'SOURCE_OUTER_CLOSED.json',dict(passed=result['passed'],closed=True,models=0,constructors=0,queries=0))
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
