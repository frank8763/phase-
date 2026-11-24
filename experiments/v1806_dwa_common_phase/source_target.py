"""Software common task, native receipt, closure-tag binding; no numerical work."""
import ast,copy,fcntl,importlib.abc,os,runpy,sys,time,traceback,types
from pathlib import Path
from context import C,O,R,read,put,sha,load,digest

def main():
 start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply();load('v1806_original_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','rclpy','kernel','vehicle','factory','ctypes','planner','fast_predict','scipy'}:raise AssertionError('SOURCE_NO_MODELS:'+name)
 sys.meta_path.insert(0,Ban())
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 bases=[R/'runs/v1691_dwa_receding_navigation',R/'runs/v1694_shared_observation_closure',R/'runs/v1802_closure_grant_refresh'];files={};result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,reference_query_calls=0,source_only=True,actual_runtime_qualified=False)
 try:
  inherited=[]
  for base in bases:
   assert read(base/'SOURCE_QUALIFICATION.json')['passed']and read(base/'SOURCE_OUTER_CLOSED.json')['passed'];recovery=read(base/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and not recovery['uncovered_members']
   for k,v in read(base/'SOURCE_FREEZE.json')['files'].items():assert k not in files or files[k]==v;files[k]=v
   inherited.append(dict(root=str(base.relative_to(R)),freeze_sha256=sha(base/'SOURCE_FREEZE.json'),recovery_path=str((base/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(base/'CURRENT_SOURCE_REMOTE_RECOVERY.json')))
  for folder in [C,R/'experiments/v1805_common_algorithm_registry',R/'experiments/v1807_dwa_common_recovery',R/'experiments/v1808_dwa_common_runtime_recovery']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for p in [O/'PILOT_TASK.json',O/'REFERENCE_CONFIG.json',O/'LIMITS_DRAFT.json',O/'ROUND_AUTHORIZATION.json',R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json',R/'runs/v1805_common_algorithm_registry/AUTHORIZATION.json']:files[str(p.relative_to(R))]=sha(p)
  unchanged=[]
  for n in ['response.py','work.py','quota.py','history_binding.py','transforms.py','obstacles.py','generic_audit.py','audit_component.py']:
   assert(C/n).read_bytes()==(R/'experiments/v1691_dwa_receding_navigation'/n).read_bytes();unchanged.append(n)
  for n in ['resources.py','capture.py']:assert(C/n).read_bytes()==(R/'experiments/v1802_closure_grant_refresh'/n).read_bytes();unchanged.append(n)
  assert(O/'REFERENCE_CONFIG.json').read_bytes()==(R/'runs/v1691_dwa_receding_navigation/REFERENCE_CONFIG.json').read_bytes()
  # Verify the only navigation change is truthful result metadata. All requests,
  # objectives/grid/horizon/weights and gates remain byte-for-byte function AST.
  old=ast.parse((R/'experiments/v1691_dwa_receding_navigation/navigation.py').read_text());new=ast.parse((C/'navigation.py').read_text())
  changed=[n for n in ast.walk(new)if isinstance(n,ast.keyword)and n.arg=='common_benchmark'];assert len(changed)==1 and changed[0].value.value is True;changed[0].value=ast.Constant(False);assert ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False)
  registry=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');assert registry['task_count']==12 and registry['method_count']==10 and registry['slot_count']==120 and not registry['physical_admission']
  parent=read(R/'runs/v1643_formal_parent_metadata/TASKS_LOCKED.json');assert len({x['task']['phase']for x in registry['tasks']})==12
  for row,original in zip(registry['tasks'],parent['tasks']):
   for k in ['case_id','seed','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id','native_limit','stop_native','initial_axis_motion_direction','sensor_seed_unchanged']:assert row['task'][k]==original['task'][k]
   assert row['task']['phase']!=original['task']['phase']
  task=read(O/'PILOT_TASK.json');shared=registry['tasks'][0]['task'];assert task['task_id']=='common_01__DWA'and task['maximum_control_native']==57600
  for k in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id','initial_axis_motion_direction']:assert task[k]==shared[k]
  obs=load('v1806_current_observation',C/'observation.py');shared_contract=load('v1806_pinned_shared_contract',R/'experiments/v1694_shared_observation_closure/contract.py');assert obs.scan_only.__code__.co_code==shared_contract.scan_only.__code__.co_code
  now=time.monotonic();p=dict(body=[0.,0.,0.,0.,0.],native_tick=16940,sim_time=169.39999999999,body_measured_at=now,sent_at=now,steering=dict(native_tick=16940,measured_at=now));scan=dict(native_tick=16940,time=169.4,xy=[0.,0.],yaw=0.,ranges=[3.]*32)
  receipt=dict(schema='DWA_CURRENT_ACQUISITION_V1',packet_acquisitions=1,packet=p,packet_sha256=digest(p),before_monotonic=now-.001,after_monotonic=now+.001,scan=scan);assert obs.verify(receipt,16940,169.4)==p
  negatives=[]
  for kind in ['future','stale','truth','packetSHA']:
   bad=copy.deepcopy(receipt)
   if kind=='future':bad['scan'].update(native_tick=16945,time=169.45)
   if kind=='stale':bad['scan'].update(native_tick=16930,time=169.3)
   if kind=='truth':bad['scan']['actor_truth']=[0,0]
   if kind=='packetSHA':bad['packet_sha256']='0'*64
   try:obs.verify(bad,16940,169.4)
   except AssertionError:negatives.append(kind)
   else:raise AssertionError('INVALID_CURRENT_RECEIPT_ALLOWED')
  # Real production wrapper calls exact original 200zero tail with fake software
  # callbacks. No native integration: distinguish callback count from actual steps.
  stop=load('v1806_closure_wrapper',C/'error_stop.py');vehicle=types.SimpleNamespace(count=0,_chain_phase='DWA_RECEDING_CURRENT',commands=[],sensor_rows=[])
  def step(a,b,stale=False):assert vehicle._chain_phase=='ERROR_STOP_CLOSURE'and a==b==0;vehicle.count+=1;vehicle.commands.append([a,b])
  def scanfn():vehicle.sensor_rows.append({'native_tick':vehicle.count});return {'native_tick':vehicle.count}
  vehicle.step=step;vehicle.scan=scanfn;progress={};answer=stop.complete(vehicle,progress);assert vehicle.count==200 and len(vehicle.sensor_rows)==41 and progress['applied']==200
  for name in ['pilot_entry.py','driver.py']:
   try:runpy.run_path(str(C/name),run_name='__main__')
   except AssertionError as e:assert str(e)=='DWA_NAVIGATION_NOT_ADMITTED';negatives.append('unadmitted_'+name)
   else:raise AssertionError('UNADMITTED_CLI_ALLOWED')
  assert all(sha(R/n)==h for n,h in files.items());put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=inherited));put(O/'SOURCE_QUALIFICATION_PROOF.json',dict(passed=True,unchanged_modules=unchanged,original_DWA_reference_config_unchanged=True,original_navigation_AST_preserved_except_result_metadata=True,common12_physical_conditions_equal_except_newSHAphase=True,old_query_numerical_tests_not_repeated=True,actual_clock_roundoff_and_whitelist_verified=True,real_closure_wrapper_fake_callback200_and41scan=True,negative_cases=negatives))
  put(O/'SOURCE_FREEZE.json',dict(files=files,models_authorized=False));result.update(passed=True,source_members=len(files),negative_cases=len(negatives),common_method='DWA',common_task='common_01',source_proof_sha256=sha(O/'SOURCE_QUALIFICATION_PROOF.json'))
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=files,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
