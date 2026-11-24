"""One new nonnumerical current-session/authority SOURCE; old math proof reused."""
import ast,copy,fcntl,importlib.abc,os,runpy,sys,time,traceback
from pathlib import Path
from context import C,O,R,read,put,sha,load,digest

def main():
 start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
 load('v1824_immutable_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','rclpy','kernel','vehicle','factory','ctypes','planner','fast_predict','scipy'}:raise AssertionError('SOURCE_NO_MODELS:'+name)
 sys.meta_path.insert(0,Ban())
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 files={};result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,reference_query_calls=0,source_only=True,actual_runtime_qualified=False)
 try:
  inherited=[]
  for version in ['v1806_dwa_common_phase','v1739_teb_current_cycle','v1818_prefix_auditor_exact_source']:
   base=R/'runs'/version;assert read(base/'SOURCE_QUALIFICATION.json')['passed']and read(base/'SOURCE_OUTER_CLOSED.json')['passed']
   recovery=read(base/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and not recovery['uncovered_members']
   for k,v in read(base/'SOURCE_FREEZE.json')['files'].items():assert k not in files or files[k]==v;files[k]=v
   inherited.append(dict(root=str(base.relative_to(R)),freeze_sha256=sha(base/'SOURCE_FREEZE.json'),recovery_path=str((base/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(base/'CURRENT_SOURCE_REMOTE_RECOVERY.json')))
  prior_index=R/'runs/v1733_teb_loader_recovery/ARCHIVE_INDEX.json';prior_remote=R/'runs/v1733_teb_loader_recovery/FULL_REMOTE_VERIFIED.json'
  assert read(prior_remote)['passed']and read(R/'runs/v1733_teb_loader_recovery/TRANSPORT_CLEANUP.json')['passed']
  bridge_name='experiments/v1732_teb_runtime_ref_binding/bridge.cpp';expected=read(R/'runs/v1732_teb_runtime_ref_binding/INPUT_BINDING.json')['files_SHA256'][bridge_name]
  assert next(row['sha256']for row in read(prior_index)['files']if row['path']==bridge_name)==expected==sha(R/bridge_name)
  for name in [bridge_name,'runs/v1732_teb_runtime_ref_binding/INPUT_BINDING.json','runs/v1732_teb_runtime_ref_binding/BUILD_COMMAND.json','runs/v1732_teb_runtime_ref_binding/BUILD_RESULT.json','runs/v1733_teb_loader_recovery/ARCHIVE_INDEX.json','runs/v1733_teb_loader_recovery/FULL_REMOTE_VERIFIED.json','runs/v1733_teb_loader_recovery/TRANSPORT_CLEANUP.json']:
   files[name]=sha(R/name)
  prior_failure=read(R/'runs/v1824_teb_common_phase/POST_ROUND_STORAGE_BARRIER.json');assert prior_failure['passed']and prior_failure['source_failed']and prior_failure['models']==0
  files['runs/v1824_teb_common_phase/POST_ROUND_STORAGE_BARRIER.json']=sha(R/'runs/v1824_teb_common_phase/POST_ROUND_STORAGE_BARRIER.json')
  for key,value in prior_failure['proof_paths_SHA256'].items():assert sha(R/key)==value;files[key]=value
  order_failure=R/'runs/v1829_teb_common_exact_bridge/POST_ROUND_STORAGE_BARRIER.json';prior=read(order_failure);assert prior['passed']and prior['source_failed']and prior['models']==0
  files[str(order_failure.relative_to(R))]=sha(order_failure)
  for key,value in prior['proof_paths_SHA256'].items():assert sha(R/key)==value;files[key]=value
  for folder in [C,R/'experiments/v1835_teb_common_source_recovery',R/'experiments/v1836_teb_common_runtime_recovery',R/'experiments/v1837_teb_common_single',R/'experiments/v1838_teb_background_launch']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for name in ['PILOT_TASK.json','LIMITS_DRAFT.json','ROUND_AUTHORIZATION.json','TEB_CONFIG.json','EXACT_NATIVE_ALIASES.json','BINARY_BINDING.json','NATIVE_BINDING.json']:
   p=O/name;files[str(p.relative_to(R))]=sha(p)
  p=R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json';files[str(p.relative_to(R))]=sha(p)
  unchanged=[]
  for n in ['response.py','capture.py','resources.py','runtime_binding.py','work.py','history_binding.py','transforms.py','obstacles.py','generic_audit.py','error_stop.py']:
   assert(C/n).read_bytes()==(R/'experiments/v1806_dwa_common_phase'/n).read_bytes();unchanged.append(n)
  for n in ['api.py','frames.py','native_namespace.py']:
   assert(C/n).read_bytes()==(R/'experiments/v1739_teb_current_cycle'/n).read_bytes();unchanged.append(n)
  assert(O/'TEB_CONFIG.json').read_bytes()==(R/'runs/v1739_teb_current_cycle/TEB_CONFIG.json').read_bytes()
  registry=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');task=read(O/'PILOT_TASK.json');shared=registry['tasks'][0]['task']
  assert registry['task_count']==12 and registry['method_count']==10 and registry['slot_count']==120 and not registry['physical_admission']
  assert task['task_id']=='common_01__TEB'and task['maximum_control_native']==57600 and task['native_limit']==60000
  for k in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id','initial_axis_motion_direction']:assert task[k]==shared[k]
  # Exact pinned author overload has no missing global path parameter. Preserve
  # update old TEBs, class exploration, original optimizer and selection order.
  cpp=R/'runs/v1728_teb_final_link_build/source/src/homotopy_class_planner.cpp';assert files[str(cpp.relative_to(R))]==sha(cpp)
  body=cpp.read_text().split('bool HomotopyClassPlanner::plan(const PoseSE2& start, const PoseSE2& goal, const geometry_msgs::Twist* start_vel, bool free_goal_vel)',1)[1].split('bool HomotopyClassPlanner::getVelocityCommand',1)[0]
  tokens=['updateAllTEBs(&start, &goal, start_vel);','exploreEquivalenceClassesAndInitTebs(start, goal, cfg_->obstacles.min_obstacle_dist, start_vel, free_goal_vel);','optimizeAllTEBs(cfg_->optim.no_inner_iterations, cfg_->optim.no_outer_iterations);','selectBestTeb();']
  assert [body.index(x)for x in tokens]==sorted(body.index(x)for x in tokens)
  bridge=R/'experiments/v1732_teb_runtime_ref_binding/bridge.cpp';assert files[str(bridge.relative_to(R))]==sha(bridge)
  assert 'p.planner->plan(teb_local_planner::PoseSE2(q->x,q->y,q->yaw),teb_local_planner::PoseSE2(q->goal_x,q->goal_y,q->goal_yaw),&velocity,false)'in bridge.read_text()
  # Software-only synthetic measured-clock envelope; not an actual observation.
  obs=load('v1824_source_receipts',C/'observation.py');frames=load('v1824_source_unchanged_frames',C/'frames.py');contract=load('v1824_source_session_contract',C/'session_contract.py')
  now=time.monotonic();p=dict(body=[0.,0.,0.,0.,0.],body_lateral=0.,native_tick=0,sim_time=0.,body_measured_at=now,sent_at=now,steering=dict(native_tick=0,measured_at=now))
  scan=dict(native_tick=0,time=0.,xy=[0.,0.],yaw=0.,ranges=[3.]*32)
  receipt=dict(schema='PHASE_CURRENT_MEASUREMENT_V1',packet_acquisitions=1,packet=p,packet_sha256=digest(p),before_monotonic=now-.001,after_monotonic=now+.001,scan=scan)
  obs.verify(receipt,0,0.);cfg=read(O/'TEB_CONFIG.json');wire=frames.encode(receipt,[4.,-2.,0.],[[0.,3.]],cfg)
  freeze='a'*64;envelope=dict(sequence=1,wire=wire,wire_sha256=digest(wire),source_freeze_sha256=freeze)
  session=contract.Session(freeze,cfg);assert session.accept(envelope)==wire
  second=copy.deepcopy(envelope);second['sequence']=2;second['wire'].update(source_native=10,source_sim_time=.1);second['wire_sha256']=digest(second['wire']);session.accept(second);assert session.sequence==2 and session.last_native==10
  negatives=[]
  for kind in ['duplicate','skip','freeze','digest','config','futureclock','truth','oldcontrols','firstnonzero','NaN','obstacletruth']:
   bad=copy.deepcopy(envelope)
   if kind=='duplicate':bad['sequence']=0
   if kind=='skip':bad['sequence']=2
   if kind=='freeze':bad['source_freeze_sha256']='b'*64
   if kind=='digest':bad['wire_sha256']='0'*64
   if kind=='config':bad['wire']['config']['forward']=.09
   if kind=='futureclock':bad['wire']['source_sim_time']=.01
   if kind=='truth':bad['wire']['actor_truth_supplied']=True
   if kind=='oldcontrols':bad['wire']['historical_controls_supplied']=True
   if kind=='firstnonzero':bad['wire'].update(source_native=10,source_sim_time=.1)
   if kind=='NaN':bad['wire']['query']['x']=float('nan')
   if kind=='obstacletruth':bad['wire']['obstacles'][0]['actor_truth']=True
   if kind not in {'digest','NaN'}:bad['wire_sha256']=digest(bad['wire'])
   probe=contract.Session(freeze,cfg)
   try:probe.accept(bad)
   except (AssertionError,ValueError):assert probe.poisoned;negatives.append(kind)
   else:raise AssertionError('INVALID_SESSION_INPUT_ACCEPTED:'+kind)
   try:probe.accept(envelope)
   except AssertionError as e:assert str(e)=='TEB_SESSION_POISONED_NO_RETRY'
   else:raise AssertionError('SESSION_RETRY_AFTER_POISON')
  session.refuse()
  try:session.accept(second)
  except AssertionError as e:assert str(e)=='TEB_SESSION_POISONED_NO_RETRY';negatives.append('finite_refusal_poison')
  else:raise AssertionError('METHOD_REFUSAL_RETRY')
  # Real production structure: one create call, persistent while scope, one
  # destroy in finally; mailbox is always RO in child, no writable PIPE/rawfd.
  worker=ast.parse((C/'native_worker.py').read_text());calls=[n for n in ast.walk(worker)if isinstance(n,ast.Call)]
  for method in ['phase_teb_create','phase_teb_destroy','phase_teb_plan']:assert sum(isinstance(n.func,ast.Attribute)and n.func.attr==method for n in calls)==1
  client=(C/'client.py').read_text();assert 'stdin=subprocess.DEVNULL'in client and 'subprocess.PIPE'in client and 'stdin=subprocess.PIPE'not in client and 'os.write('not in client
  assert 'assert not self.closed and not self.poisoned'in client and 'TEB_NATIVE_SESSION_NOT_CLOSED'in client
  for name,args,reason in [('pilot_entry.py',[],'TEB_NAVIGATION_NOT_ADMITTED'),('driver.py',[],'TEB_NAVIGATION_NOT_ADMITTED'),('native_worker.py',['--serve-current'],'TEB_NATIVE_NOT_ADMITTED')]:
   prior=sys.argv[:];sys.argv=[str(C/name),*args]
   try:
    try:runpy.run_path(str(C/name),run_name='__main__')
    except AssertionError as e:assert str(e)==reason;negatives.append('unadmitted_'+name)
    else:raise AssertionError('UNADMITTED_CLI_ALLOWED:'+name)
   finally:sys.argv=prior
  assert all(sha(R/n)==h for n,h in files.items())
  put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=inherited))
  put(O/'SOURCE_QUALIFICATION_PROOF.json',dict(passed=True,unchanged_modules=unchanged,source_only_fake_metadata_not_runtime=True,original_point_goal_overload_confirmed=True,no_external_reference_silently_added=True,one_create_plan_destroy_callsite_and_persistent_scope=True,original_binary_and_all_dependencies_reused=True,original_TEB_config_unchanged=True,session_two_current_messages_and_poison_verified=True,child_readonly_mailbox_parent_all_writes_quota=True,old_numerical_suite_not_repeated=True,negative_cases=negatives))
  put(O/'SOURCE_FREEZE.json',dict(files=files,models_authorized=False));result.update(passed=True,source_members=len(files),negative_cases=len(negatives),common_method='TEB',common_task='common_01',source_proof_sha256=sha(O/'SOURCE_QUALIFICATION_PROOF.json'))
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=files,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
