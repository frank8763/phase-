"""Once closure-capture qualification, software calls only; no numerical imports."""
import ast,fcntl,importlib.abc,os,runpy,sys,time,traceback
from context import C,O,R,ROOT,SOURCE,put,read,sha,load

def main():
 start=time.monotonic()
 assert O==SOURCE and SOURCE==R/'runs'/C.name
 os.environ['MUJOCO_GL']='osmesa'
 sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
 import resource_policy
 resource_policy.apply()
 load('v1649_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(SOURCE)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','OpenGL','jax','rclpy','kernel','factory','vehicle','route_tools','ctypes'}:
    raise AssertionError('CLOSURE_SOURCE_NO_NUMERICAL_IMPORT:'+name)
 sys.meta_path.insert(0,Ban())
 with(SOURCE/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open()
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 prior=R/'runs/v1646_prefix_audit_scope'
 source=read(prior/'SOURCE_FREEZE.json')['files'].copy()
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,source_only=True,actual_runtime_qualified=False)
 try:
  closed=ROOT/'rounds/phase_01__no_onward'
  barrier=read(closed/'POST_ROUND_STORAGE_BARRIER.json');assert barrier['passed']
  for a,b in [('closed_result_path','closed_result_sha256'),('remote_proof_path','remote_proof_sha256'),('cleanup_proof_path','cleanup_proof_sha256')]:
   assert sha(R/barrier[a])==barrier[b]
  assert read(prior/'SOURCE_QUALIFICATION.json')['passed']
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
  for p in [prior/'SOURCE_QUALIFICATION.json',prior/'source_target/QUALIFICATION.json',closed/'POST_ROUND_STORAGE_BARRIER.json',closed/'ERROR_STOP_SENSOR_GAP_DIAGNOSIS.json',R/'runs/v1650_comparison_completion/AUTHORIZATION.json']:
   source[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in source.items())
  reused=[]
  old=R/'experiments/v1646_prefix_audit_scope'
  for n in ['resources.py','capture.py','history_binding.py','work.py','quota.py','transforms.py','phase_contract.py','audit_seams.py','audit_binding.py','context.py','runtime_binding.py','entry.py','owner.py']:
   assert(C/n).read_bytes()==(old/n).read_bytes();reused.append(n)
  oldtail="      def tail():\n       for _ in range(200):v.step(0.,0.,False)\n       return dict(applied=200)\n"
  newtail="      result['error_stop_progress']={}\n      error_tail=load('v1649_actual_closure_sensor_receipts',C/'error_stop.py')\n      def tail():return error_tail.complete(v,result['error_stop_progress'])\n"
  assert(old/'driver.py').read_text().count(oldtail)==1
  assert(C/'driver.py').read_text()==(old/'driver.py').read_text().replace(oldtail,newtail)
  helper=load('v1649_software_tested_closure',C/'error_stop.py')
  class SoftwareVehicle:
   def __init__(self,origin=36425,fault=None):
    self.count=origin;self.sensor_rows=[dict(native_tick=origin)]if origin%5==0 else []
    self.actions=[];self.fault=fault
   def step(self,v,w,stale):
    assert(v,w,stale)==(0.,0.,False)
    self.actions.append((v,w,stale));self.count+=1
   def scan(self):
    if self.fault=='raise':raise OSError('SOFTWARE_SCAN_FAILURE')
    if self.fault=='advance':self.count+=1
    value=dict(native_tick=self.count+(1 if self.fault=='wrong_tick'else 0))
    if self.fault!='no_append':self.sensor_rows.append(value)
    return value
  # Reproduce the exact old caller's missing sensor coverage with no physics.
  tree=ast.parse((old/'driver.py').read_text())
  node=next(x for x in ast.walk(tree)if isinstance(x,ast.FunctionDef)and x.name=='tail')
  v=SoftwareVehicle();scope=dict(v=v)
  exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(old/'driver.py'),'exec'),scope)
  assert scope['tail']()==dict(applied=200)
  missing=sorted(set(range(36425,36626,5))-{x['native_tick']for x in v.sensor_rows})
  assert missing==list(range(36430,36626,5))
  positives=[];negatives=[]
  for origin in [36425,36426]:
   v=SoftwareVehicle(origin);progress={};answer=helper.complete(v,progress)
   assert answer['applied']==200 and len(v.actions)==200 and v.count==origin+200
   assert set(range(origin+(5-origin%5)%5,origin+201,5)).issubset({x['native_tick']for x in v.sensor_rows})
   assert progress['closed']and progress['complete200']and not progress['step_inflight_unknown']
   positives.append(dict(origin=origin,software_actions=200,software_scans=answer['current_sensor_rows']))
   before=(v.count,len(v.actions),len(v.sensor_rows))
   try:helper.complete(v,progress)
   except AssertionError as e:assert str(e)=='ERROR_STOP_CAPTURE_NO_RETRY';negatives.append('no_retry_'+str(origin))
   else:raise AssertionError('CLOSURE_RETRY_ACCEPTED')
   assert before==(v.count,len(v.actions),len(v.sensor_rows))
  for fault in ['raise','advance','wrong_tick','no_append']:
   v=SoftwareVehicle(fault=fault);progress={}
   try:helper.complete(v,progress)
   except (AssertionError,OSError):pass
   else:raise AssertionError('SCAN_FAULT_ACCEPTED:'+fault)
   assert progress['closed']and not progress['complete200']and progress['applied']==5
   before=(v.count,len(v.actions),len(v.sensor_rows))
   try:helper.complete(v,progress)
   except AssertionError:pass
   else:raise AssertionError('FAULT_RETRY_ACCEPTED')
   assert before==(v.count,len(v.actions),len(v.sensor_rows));negatives.append(fault)
  for name in ['entry.py','driver.py']:
   try:runpy.run_path(str(C/name),run_name='__main__')
   except AssertionError as e:assert str(e)=='REGISTERED_PHASE_ASSIGNMENT_NOT_ADMITTED'
   else:raise AssertionError('UNADMITTED_SOURCE_ACCEPTED')
  target=SOURCE/'source_target';target.mkdir()
  proof=dict(passed=True,source_only=True,models=0,physical_native=0,replay_native=0,FFI_loads=0,software_vehicle_not_model=True,old_driver_missing_samples_reproduced=len(missing),positive_cases=positives,negative_cases=negatives,driver_only_replaced_error_tail=True,unchanged_modules_reused=reused,prior_source_proof_sha256=sha(prior/'source_target/QUALIFICATION.json'),all_original_numeric_audit_gates_unchanged=True,closed_cases_not_rerun=True,real_unadmitted_CLI_refused=True)
  put(target/'QUALIFICATION.json',proof)
  put(SOURCE/'SOURCE_FREEZE.json',dict(files=source,source_only=True,models_authorized=False))
  result.update(passed=True,source_members=len(source),qualified_case_id='WEST_EAST',qualified_variants=['full','no_onward'],negative_cases=len(negatives),unchanged_modules_reused=reused,source_proof_sha256=sha(target/'QUALIFICATION.json'))
 except BaseException as error:
  result.update(first_error=repr(error),traceback=traceback.format_exc());put(SOURCE/'FAILED_SOURCE_FREEZE.json',dict(files=source,models_authorized=False))
 finally:
  result.update(closed=True,wall_s=time.monotonic()-start);put(SOURCE/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
