"""Once pure measured-clock/closure-tag qualification, zero model imports."""
import ast,copy,ctypes,fcntl,importlib.abc,json,runpy,sys,time,traceback
from types import SimpleNamespace
from context import C,O,R,read,put,sha,load
P=R/'runs/v1691_dwa_receding_navigation'

def main():
 started=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy
 resource_policy.apply();load('v1694_original_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','rclpy','kernel','vehicle','factory','bindings'}:raise AssertionError('SOURCE_NO_NUMERICAL_IMPORT:'+name)
 sys.meta_path.insert(0,Ban());original=ctypes.CDLL
 def banned(*args,**kwargs):raise AssertionError('SOURCE_NO_DLL')
 ctypes.CDLL=banned
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 source=read(P/'SOURCE_FREEZE.json')['files'].copy()
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,solver_calls=0,actual_client_runtime_qualified=False)
 try:
  closed=read(P/'COMPLETION.json');assert closed['closed']and not closed['passed']
  barrier=read(P/'POST_ROUND_STORAGE_BARRIER.json');assert barrier['passed']and all(sha(R/n)==h for n,h in barrier['proof_paths_SHA256'].items())
  assert read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
  for name in ['SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','COMPLETION.json','RUNTIME_CLOSED_REVIEW.json','POST_ROUND_STORAGE_BARRIER.json','FUNCTIONAL_BOUNDARY_DIAGNOSIS.json']:
   p=P/name;source[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in source.items())
  contract=load('v1694_production_contract',C/'contract.py')
  scan=dict(native_tick=20,time=.20000000000000004,xy=[1.,2.],yaw=.1,ranges=[3.]*32)
  now=time.monotonic();packet=dict(body=[1.,2.,.1,0.,0.],native_tick=20,sim_time=.2,body_measured_at=now,sent_at=now,steering=dict(position=[0.,0.],velocity=[0.,0.],native_tick=20,measured_at=now),controller_memory=dict(last_ctrl=[0.,0.,0.,0.],integral=.1))
  receipt=dict(schema='PHASE_CURRENT_MEASUREMENT_V1',packet_acquisitions=1,packet=packet,packet_sha256=contract.digest(packet),before_monotonic=now-.001,after_monotonic=now+.001,scan=scan)
  immutable=contract.digest(receipt)
  assert contract.verify_receipt(receipt,20)==packet and contract.digest(receipt)==immutable
  # Actual receipt acquisition at accumulated simtime; exactly one callback.
  callbacks=[]
  def sample(v):
   callbacks.append(v.count);p=copy.deepcopy(packet);stamp=time.monotonic();p.update(sim_time=v.d.time,body_measured_at=stamp,sent_at=stamp);p['steering']['measured_at']=stamp;return p
  v=SimpleNamespace(count=20,d=SimpleNamespace(time=.20000000000000004))
  fresh=contract.acquire(v,sample,dict(scan,raw_lidar=[123.],actor_truth=[99.,99.]))
  assert callbacks==[20]and set(fresh['scan'])==set(contract.SCAN_KEYS)and contract.verify_receipt(fresh,20)==fresh['packet']
  assert scan['time']==.20000000000000004 and receipt['packet']['sim_time']==.2
  negatives=[]
  def reject(name,change,rehash=False):
   bad=copy.deepcopy(receipt);change(bad)
   if rehash:bad['packet_sha256']=contract.digest(bad['packet'])
   try:contract.verify_receipt(bad,20)
   except(AssertionError,KeyError,ValueError):negatives.append(name)
   else:raise AssertionError('NEGATIVE_ACCEPTED:'+name)
  reject('future_scan_tick',lambda x:x['scan'].update(native_tick=21,time=.21))
  reject('old_scan_tick',lambda x:x['scan'].update(native_tick=14,time=.14))
  reject('scan_clock_outside_original_tolerance',lambda x:x['scan'].__setitem__('time',.200001))
  reject('packet_clock_outside_original_tolerance',lambda x:x['packet'].__setitem__('sim_time',.200001),True)
  reject('future_packet_tick',lambda x:x['packet'].__setitem__('native_tick',21),True)
  reject('wrong_SHA',lambda x:x.__setitem__('packet_sha256','0'*64))
  reject('multiple_acquisitions',lambda x:x.__setitem__('packet_acquisitions',2))
  reject('outside_monotonic_interval',lambda x:x.__setitem__('after_monotonic',now-.1))
  reject('channel_clock',lambda x:x['packet']['steering'].__setitem__('measured_at',now+.01),True)
  reject('nonfinite_simclock',lambda x:x['packet'].__setitem__('sim_time',float('nan')))
  reject('range_shape',lambda x:x['scan'].__setitem__('ranges',[1.]))
  reject('range_domain',lambda x:x['scan']['ranges'].__setitem__(0,4.))
  reject('unwhitelisted_truth',lambda x:x['scan'].__setitem__('actor_truth',[0.,0.]))
  # Invoke unchanged production tail with SOFTWARE callbacks, not a vehicle.
  tail_path=R/'experiments/v1691_dwa_receding_navigation/error_stop.py';assert source[str(tail_path.relative_to(R))]==sha(tail_path)
  tail=load('v1694_original_tail_software_callbacks',tail_path)
  class Fake:
   def __init__(self):self.count=0;self.sensor_rows=[];self._chain_phase='NORMAL';self.journal=[]
   def step(self,*request):
    self.journal.append(dict(before_native=self.count,phase=self._chain_phase,request=list(request),applied=True));self.count+=1
   def scan(self):
    value=dict(native_tick=self.count);self.sensor_rows.append(value);return value
  fake=Fake();progress={};answer=contract.complete_closure(fake,progress,tail.complete)
  assert answer['applied']==200 and fake.count==200 and len(fake.sensor_rows)==41 and all(row['phase']==contract.CLOSURE_PHASE for row in fake.journal)
  assert all(row['request']==[0.,0.,False]for row in fake.journal)
  assert contract.partition_journal(fake.journal,'NORMAL')['error_stop']==list(range(200))
  def raising(v,progress):raise ValueError('ORIGINAL_FIRST_ERROR_SENTINEL')
  fake2=Fake()
  try:contract.complete_closure(fake2,{},raising)
  except ValueError as e:assert str(e)=='ORIGINAL_FIRST_ERROR_SENTINEL'and fake2._chain_phase==contract.CLOSURE_PHASE
  else:raise AssertionError('CLOSURE_SWALLOWED_FIRST_ERROR')
  rows=[dict(before_native=i,phase=phase,request=[0.,0.,False],applied=True)for i,phase in enumerate(['NORMAL','NORMAL','GOAL_STOP',contract.CLOSURE_PHASE])]
  groups=contract.partition_journal(rows,'NORMAL','GOAL_STOP');assert groups==dict(normal=[0,1],goal_stop=[2],error_stop=[3]),'ZERO_WAIT_IS_NORMAL_BY_PHASE'
  def badrows(name,change):
   bad=copy.deepcopy(rows);change(bad)
   try:contract.partition_journal(bad,'NORMAL','GOAL_STOP')
   except AssertionError:negatives.append(name)
   else:raise AssertionError('JOURNAL_NEGATIVE_ACCEPTED:'+name)
  badrows('unknown_phase',lambda x:x[2].__setitem__('phase','UNKNOWN'))
  badrows('normal_after_closure',lambda x:x[3].__setitem__('phase','NORMAL'))
  badrows('nonzero_error_stop',lambda x:x[3].__setitem__('request',[.01,0.,False]))
  badrows('native_gap',lambda x:x[2].__setitem__('before_native',5))
  badrows('unapplied',lambda x:x[1].__setitem__('applied',False))
  try:runpy.run_path(str(C/'entry.py'),run_name='__main__')
  except AssertionError as e:assert str(e)=='SOURCE_CONTRACT_HAS_NO_MODEL_AUTHORITY';negatives.append('real_CLI_no_model_authority')
  else:raise AssertionError('NUMERICAL_ENTRY_ACCEPTED')
  assert all(sha(R/n)==h for n,h in source.items())
  put(O/'SOURCE_FREEZE.json',dict(files=source,source_only=True,models_authorized=False))
  result.update(passed=True,source_members=len(source),negative_cases=negatives,actual_clock_tolerance_unchanged=1e-8,receipt_roundoff_software_positive=True,packet_and_scan_timestamps_unmodified=True,original_error_tail_sha256=sha(tail_path),software_fake_zero_callbacks=200,software_fake_scan_callbacks=41,physical_callbacks=0,canonical_first_error_preserved=True,journal_explicit_phase_partition=True,normal_zero_wait_not_closure=True,no_old_case_reaudited=True,sourcepass_not_client_runtime=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=source))
 finally:
  ctypes.CDLL=original;result.update(closed=True,wall_s=time.monotonic()-started);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
