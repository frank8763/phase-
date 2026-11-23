"""One source/API qualification; no numerical solver or physical import."""
import ast,copy,ctypes,fcntl,importlib.abc,json,runpy,sys,time,traceback
from context import C,O,R,read,put,sha,load,digest
P=R/'experiments/v1690_dwa_origin_source_checks';PO=R/'runs'/P.name

def main():
 start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy
 resource_policy.apply();load('v1691_original_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','rclpy','kernel','vehicle','factory','bindings'}:raise AssertionError('SOURCE_NO_MODELS:'+name)
 sys.meta_path.insert(0,Ban());original=ctypes.CDLL
 def banned(*a,**k):raise AssertionError('SOURCE_NO_DLL')
 ctypes.CDLL=banned
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 files=read(PO/'SOURCE_FREEZE.json')['files'].copy()
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,reference_query_calls=0,actual_runtime_qualified=False)
 try:
  assert read(PO/'COMPLETION.json')['passed']and read(PO/'COMPLETION.json')['closed']
  barrier=read(PO/'POST_ROUND_STORAGE_BARRIER.json');assert barrier['passed']and all(sha(R/n)==h for n,h in barrier['proof_paths_SHA256'].items())
  assert read(PO/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    files[str(p.relative_to(R))]=sha(p)
  for folder,names in [(O,['PILOT_TASK.json','REFERENCE_CONFIG.json','LIMITS_DRAFT.json']),(PO,['SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','COMPLETION.json','RUNTIME_CLOSED_REVIEW.json','POST_ROUND_STORAGE_BARRIER.json'])]:
   for name in names:p=folder/name;files[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in files.items())
  reused=[]
  for name in ['source_owner.py','capture.py','resources.py','quota.py','work.py','history_binding.py','transforms.py','runtime_binding.py','error_stop.py','obstacles.py']:
   assert sha(C/name)==sha(P/name);reused.append(name)
  assert sha(C/'generic_audit.py')==sha(P/'audit_component.py')and sha(O/'REFERENCE_CONFIG.json')==sha(PO/'REFERENCE_CONFIG.json')
  task=read(O/'PILOT_TASK.json');old=read(PO/'PILOT_TASK.json')
  for key in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','dynamic','course_id','original_pool_task']:assert task[key]==old[key]
  assert task['task_id']=='dwa_receding_navigation'and task['native_limit']==60000 and task['maximum_control_native']==57600 and task['historical_prefix_native']==0
  limits=read(O/'LIMITS_DRAFT.json');prior=read(PO/'LIMITS_DRAFT.json')
  assert {k:v for k,v in limits.items()if k not in ['maximum_actual_native','maximum_replay_native']}=={k:v for k,v in prior.items()if k not in ['maximum_actual_native','maximum_replay_native']}
  assert limits['maximum_actual_native']==limits['maximum_replay_native']==60000
  assert 'runs/v1690_dwa_origin_source_checks/POST_ROUND_STORAGE_BARRIER.json'in(C/'owner.py').read_text()
  audit=load('v1691_original_generic_source',C/'generic_audit.py');fn,seam=audit.generic_ast(files)
  assert seam==read(PO/'SOURCE_QUALIFICATION.json')['original_generic_actual_audit_seam']
  obs=load('v1691_real_observation_source_cases',C/'observation.py')
  scan=dict(native_tick=15,time=.15,xy=[0.,0.],yaw=0.,ranges=[3.]*32,actor_truth=[99.,99.],raw_lidar=[1.]*32,future=[123.])
  clean=obs.scan_only(scan,15,.15);assert set(clean)==set(obs.KEYS)
  assert obs.scan_only(dict(clean),15,.15)==clean
  assert obs.points(clean)==[];one=copy.deepcopy(clean);one['ranges'][0]=1.;one['ranges'][8]=2.;points=obs.points(one)
  assert points[0]==[1.,0.]and abs(points[1][0])<=1e-12 and abs(points[1][1]-2.)<=1e-12
  now=time.monotonic();packet=dict(body=[1.,2.,0.,.01,0.],body_lateral=0.,native_tick=15,sim_time=.15,body_measured_at=now,sent_at=now,steering=dict(position=[0.,0.],velocity=[0.,0.],native_tick=15,measured_at=now),controller_memory=dict(last_ctrl=[0.,0.,0.,0.],integral=.1),dynamic_discovered=True,coupled_episode=False,steering_motion_active=False)
  receipt=dict(schema='DWA_CURRENT_ACQUISITION_V1',packet_acquisitions=1,packet=packet,packet_sha256=digest(packet),before_monotonic=now-.001,after_monotonic=now+.001,scan=clean)
  assert obs.verify(receipt,15,.15)==packet
  negatives=[]
  def reject(name,change,rehash=False):
   bad=copy.deepcopy(receipt);change(bad)
   if rehash:bad['packet_sha256']=digest(bad['packet'])
   try:obs.verify(bad,15,.15)
   except(AssertionError,KeyError):negatives.append(name)
   else:raise AssertionError('NEGATIVE_ACCEPTED:'+name)
  reject('future_packet_native',lambda x:x['packet'].__setitem__('native_tick',16),True)
  reject('packet_sim_time',lambda x:x['packet'].__setitem__('sim_time',.16),True)
  reject('packet_SHA',lambda x:x.__setitem__('packet_sha256','0'*64))
  reject('measurement_outside_interval',lambda x:x.__setitem__('after_monotonic',now-.1))
  reject('steering_clock',lambda x:x['packet']['steering'].__setitem__('measured_at',now+.1),True)
  reject('duplicate_acquisition',lambda x:x.__setitem__('packet_acquisitions',2))
  reject('old_scan',lambda x:x['scan'].update(native_tick=0,time=0.))
  reject('future_scan',lambda x:x['scan'].update(native_tick=20,time=.2))
  reject('bad_range_shape',lambda x:x['scan'].__setitem__('ranges',[1.]))
  reject('bad_range_domain',lambda x:x['scan']['ranges'].__setitem__(0,4.))
  reject('unwhitelisted_truth',lambda x:x['scan'].__setitem__('actor_truth',[0.,0.]))
  for name in ['pilot_entry.py','driver.py']:
   try:runpy.run_path(str(C/name),run_name='__main__')
   except AssertionError as e:assert str(e)=='DWA_NAVIGATION_NOT_ADMITTED';negatives.append('actual_'+name+'_unadmitted')
   else:raise AssertionError('CLI_ACCEPTED')
  # The original timed geometry constructor/API and default half-step reserve
  # are inspected without importing numerical code or rebuilding old tests.
  original_geometry=R/'experiments/v1067_causal_replan_brake_reserve/exact_timed.py'
  assert files[str(original_geometry.relative_to(R))]==sha(original_geometry)
  tree=ast.parse(original_geometry.read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='ExactTimedGeometry')
  init=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='__init__');assert [a.arg for a in init.args.args]==['self','known','prior','start']
  nav=(C/'navigation.py').read_text();response=(C/'response.py').read_text();driver=(C/'driver.py').read_text();independent=(C/'audit_component.py').read_text()
  assert "reference.bind(np,source,read(O/'REFERENCE_CONFIG.json'))"in nav and 'for offset in [0,5]'in nav and "source,config"not in nav
  assert "q.helper.checks"in response and "if k!='goal_upper'"in response and 'terminal_full_cycle_hold=terminal>=kernel.REQUIRED'in response
  assert "if not inside and actual>0"in driver and "canonical_first_error=result['first_error']"in independent and "result['whole_navigation_passed']=bool(result['passed'])"in driver
  assert "source_snapshot['periodic']==evidence.periodic.snapshot()"in independent and 'covered==normal'in independent and "nav['complete_zero_stop_native']==2200"in independent
  for filename in ['navigation.py','observation.py','response.py']:
   for node in ast.walk(ast.parse((C/filename).read_text())):
    if isinstance(node,ast.Assign):assert not any(ast.unparse(t)in {'v.count','v.d.time','v.adapter.last','v.adapter.integral'}for t in node.targets)
  assert all(sha(R/n)==h for n,h in files.items())
  put(O/'SOURCE_FREEZE.json',dict(files=files,source_only=True,models_authorized=False))
  result.update(passed=True,source_members=len(files),negative_cases=negatives,exact_pipeline_modules_reused=reused,original_generic_actual_audit_seam=seam,reference_config_byteidentical=True,old_task_seed_phase_unchanged=True,receipt_native_nonzero_software_verified=True,whitelist_scan_cost_points_verified=True,prefix_audit_preserves_canonical_first=True,sourcepass_not_actualpass=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=files))
 finally:
  ctypes.CDLL=original;result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
