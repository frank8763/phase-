"""New bounded original-contract WE driver; no old execution main is called."""
import fcntl,os,signal,time,traceback
from pathlib import Path
from context import SOURCE,C,O,R,OLD,load,read,put,sha,admission,remaining

def run():
 assignment=read(O/'PILOT_TASK.json')
 authority,window,source=admission(assignment) # before any numerical import
 out=Path(assignment['output']);limits=read(O/'LIMITS_DRAFT.json')
 caches=load('v1624_reused_taskcache',R/'experiments/v1447_full_module_guard_identity/task_cache.py')
 guards=load('v1624_reused_immutableguard',R/'experiments/v1447_full_module_guard_identity/guard_binding.py')
 history=load('v1629_exact_original_history_guard',C/'history_binding.py')
 history.install(out,source)
 with caches.TaskLocalCaches(out),guards.bind_original_guard(out):
  return execute(assignment,window,source,limits,out)

def execute(task,window,source,limits,out):
 from quota import EvidenceQuota
 quota=EvidenceQuota(out,limits);quota.bind_external_names([]);quota.write_enforcement_active=True
 resources=load('v1639_evidence_stage_resources',C/'resources.py');resources.reserve_terminal(quota)
 io=load('v1624_original_output_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
 atomic=load('v1624_original_evidence_atomic',C/'compact_json.py').atomic
 start=time.monotonic();v=None;capture=None;ledger=None;initial=None;phase='bootstrap';inside=False;actual=0;replayed=0;journal=[];finish_attempted=False
 result=dict(passed=False,closed=False,models=0,canonical_factory_call_attempts=0,canonical_vehicle_initializations=0,internal_factory_model_constructions=None,
  initializer_inflight_unknown=False,first_error=None,secondary_errors=[],new_actual_native=0,own_replay_native=0,
  historical_reconstruction_native=0,historical_controls_used=0,private_mujoco_native=0,training_updates=0,
  formal_retained_commit=False,final_stop_executed=False,universal_error_support_verified=False,
  original_contract=True,weekend_contract_qualified=False,formal_prospective_task=True,mechanism_variant='full')
 def save(name,value):return quota.atomic(out/name,value,atomic)
 def refresh(stage,cap=None,ttl=1800):
  return resources.prepare(quota,stage,cap=cap,ttl=ttl)
 def clock(*_):raise TimeoutError('ORIGINAL_CONTRACT_ROOT_OR_STAGE_DEADLINE')
 def arm(seconds):signal.setitimer(signal.ITIMER_REAL,max(.01,min(seconds,remaining(window)-5)))
 def first(error,where):
  detail=dict(stage=where,error=repr(error),traceback=traceback.format_exc())
  if result['first_error']is None:result['first_error']=detail
  else:result['secondary_errors'].append(detail)
 def attempt(where,fn):
  try:return fn()
  except BaseException as error:first(error,where);return None
 originalalarm=signal.signal(signal.SIGALRM,clock);originalterm=signal.signal(signal.SIGTERM,clock)
 with(O/'execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:
   with io.OutputBoundary(out,quota.charge_write):
    arm(180);refresh('CANONICAL_INITIALIZER_PREPARATION',16*1024**2,180)
    runtime=load('v1624_new_original_runtime',C/'runtime_binding.py')
    binding=runtime.bind(out,window,'full',prepared_sources=source);old=binding['old'];q=binding['q'];np=q.np
    save('CACHED_LIBRARY_BINDING.json',binding['cached_library_binding'])
    refresh('CANONICAL_INITIALIZER_PREPARATION',16*1024**2,180)
    physical=load('v1624_qualified_physical_binding',R/'experiments/v1449_route_initializer_binding/lifecycle.py').physical_binding(out)
    _,Adapter,factory,replay=physical
    save('INITIALIZATION_ATTEMPT.json',dict(unix=time.time(),attempt=1,actual_before=0))
    result.update(canonical_factory_call_attempts=1,initializer_inflight_unknown=True,canonical_vehicle_initializations=None)
    import mujoco as mj
    with io.native_model_saves(mj,quota.charge_write):v=factory.create_vehicle(out/'physics',task)
    result.update(models=1,canonical_vehicle_initializations=1,initializer_inflight_unknown=False)
    old.pin();assert v.count==0 and float(v.d.time)==0
    scene=load('v1624_original_scene_contract',R/'experiments/v1089_route_scene_contract/contract.py')
    result['scene_contract']=scene.verify_live(v,task)
    previous=v.adapter;v.adapter=Adapter(v.m,mj,v.dt,encoders=previous.encoders)
    v.adapter.virtual_rate=.6;v.adapter.last=previous.last.copy();v.adapter.integral=previous.integral
    initial={k:np.asarray(getattr(v.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};initial['time']=np.asarray(v.d.time)
    quota.save_npz(out/'INITIAL_FULL_STATE.npz',initial,np)
    save('CANONICAL_INITIAL_PACKET.json',binding['packet'](v))
    capture=load('v1624_qualified_complete_capture',C/'capture.py').CaptureBudget(quota);capture.update(v)
    work=load('v1624_counted_modelwork',C/'work.py');ledger=work.ModelWork(limits,window['normal_end_unix']);ledger.bind(q)
    service=load('v1912_hybrid_predictive_evidence',C/'evidence_service.py')
    binding['predictive_arrays']=service.Service(q,setup=read(out/'physics/SETUP.json'),task=task,source=source,out=out,quota=quota,ledger=ledger,window=window)
    native=v.native;step=v.step
    def counted(*args):
     nonlocal inside,actual,replayed
     assert remaining(window)>5
     inside=True;answer=native(*args);inside=False
     if phase=='replay':replayed+=1
     else:actual+=1
     return answer
    v.native=counted
    def applied(vr,wr,stale=False):
     assert phase in {'normal','error_stop'}
     assert time.time()<window['normal_end_unix']if phase=='normal'else remaining(window)>900
     assert v.count<limits['maximum_actual_native']-(200 if phase=='normal'else 0)
     capture.update(v,requested_native=1)
     row=dict(before_native=v.count,phase=getattr(v,'_chain_phase','fresh_normal'),parked_target=getattr(v.adapter,'parked_target',None),request=[float(vr),float(wr),bool(stale)],last_ctrl=v.adapter.last.tolist(),integral=float(v.adapter.integral),applied=False)
     journal.append(row);before=v.count;step(float(vr),float(wr),bool(stale));row['applied']=True
     assert v.count==before+1;old.previous.body_gate(binding['packet'](v))
     if v.count%500==0:save('ACTUAL_PROGRESS.json',dict(native=v.count,phase=phase,modelwork=ledger.snapshot()))
    v.step=applied;v._chain_phase='fresh_normal';phase='normal';arm(window['normal_end_unix']-time.time());refresh('STOPPED_EVENT_PREPARATION')
    navigator=load('v1691_current_DWA_navigation',C/'navigation.py')
    result['navigation']=navigator.run(v,binding,task,source,out,save,quota,refresh)
    assert result['navigation']['passed']and result['navigation']['whole_goal_with_original_stop']and result['navigation']['actual_original_goal_reached']
    result.update(full_fresh_t0_navigation=True,current_interface_component=False,final_stop_executed=True,whole_navigation_passed=False,actual_original_goal_reached=True,exposed_development_not_independent_benchmark=False,common_prospective_task=True)
  except BaseException as error:
   result['passed']=False;first(error,phase)
  finally:
   if 'binding'in locals():result['secondary_errors'].extend(binding.get('native_peer_secondary_errors',[]))
   quota.retire_grant();arm(min(1200,remaining(window)-5))
   with io.OutputBoundary(out,quota.charge_write):
    attempt('CLOSE_GRANT',lambda:refresh('COMPLETE_ZERO_TAIL_OR_CLOSURE',ttl=300))
    if v is not None:
     if result['first_error']and not inside and v.count<=limits['maximum_actual_native']-200 and remaining(window)>1000:
      phase='error_stop';v.adapter.parked_target=None
      result['error_stop_progress']={}
      error_tail=load('v1672_unchanged_error_stop_scan',C/'error_stop.py')
      def tail():return error_tail.complete(v,result['error_stop_progress'])
      result['error_stop']=attempt('COMPLETE_ERROR_STOP',tail)
     result.update(new_actual_native=None if inside and phase!='replay'else actual,total_actual_model_native=None if inside and phase!='replay'else actual,fully_recorded_native=len(v.rows),model_native_inflight_unknown=inside)
     attempt('SAVE_FINAL_PACKET',lambda:save('ACTUAL_FINAL_PACKET.json',binding['packet'](v)))
     result.pop('_evidence',None);attempt('SAVE_DIRECT_SEGMENTS',lambda:save('DIRECT_SEGMENTS.json',result.pop('_direct_segments',[])))
     if capture is not None:
      finish_attempted=True;result['physical']=attempt('COMPLETE_PHYSICAL_CAPTURE',lambda:capture.finish(v));result['evidence_saved']=result['physical']is not None
     if capture is not None:result['secondary_errors'].extend(capture.secondary_close_errors)
     if initial is not None:
      arrays={k:np.concatenate([initial[k][None],np.asarray([row[k]for row in v.rows])],axis=0)for k in initial}
      attempt('NPLUS1_FRESH_CLOSE_GRANT',lambda:resources.prepare_nplus1_after_capture(quota,phase,inside,result.get('evidence_saved')))
      attempt('SAVE_NPLUS1',lambda:quota.save_npz(out/'FULL_STATE_NPLUS1.npz',arrays,np))
     attempt('JOURNAL_QUIESCENT_FRESH_GRANT',lambda:refresh('COMPLETE_ZERO_TAIL_OR_CLOSURE',ttl=300))
     attempt('SAVE_JOURNAL',lambda:save('APPLIED_JOURNAL.json',journal))
     if result.get('evidence_saved')and not inside and len(v.rows)==actual and remaining(window)>800:
      phase='replay';arm(300);attempt('REPLAY_GRANT',lambda:refresh('COMPLETE_ZERO_TAIL_OR_CLOSURE',ttl=300))
      result['replay_state_initializations']=1
      result['replay']=attempt('FULL_STATE_OWN_REPLAY',lambda:replay(v,min(time.time()+290,window['absolute_deadline_unix']-600),out/'physics'))
      result['own_replay_native']=None if inside else replayed
     result['error']=result['first_error']
     result['known_recovery_counts']=dict(getattr(v,'_chain_counts',{}),observer_cpp_native=getattr(getattr(v,'_chain_engine',None),'native',None))
     if not inside and actual>0 and (result.get('replay')or{}).get('passed')and remaining(window)>600:
      phase='independent_audit';audit_seconds=load('SVG_finite_close_audit_budget',C/'audit_budget.py').seconds(remaining(window))
      arm(audit_seconds)
      if ledger is not None:ledger.deadline=min(time.time()+audit_seconds-10.,window['absolute_deadline_unix']-30)
      result['independent_audit_budget_s']=audit_seconds
      attempt('AUDIT_GRANT',lambda:refresh('STOPPED_EVENT_PREPARATION',ttl=min(1200,audit_seconds+20)))
      # Preserve the original auditor's FUNCTIONAL passed convention separately.
      # The canonical RESULT remains false until all independent evidence and
      # final source/clock checks pass. No optimistic scientific success write.
      audit_input=dict(result,passed=False,exposed_development_not_independent_benchmark=False,common_prospective_task=True,independent_audit_pending=True)
      attempt('SAVE_FUNCTIONAL_AUDIT_INPUT',lambda:save('FUNCTIONAL_AUDIT_INPUT.json',audit_input))
      auditor=load('v1672_current_component_independent_audit',C/'audit_component.py')
      result['independent_audit']=attempt('ORIGINAL_COMPONENT_INDEPENDENT_AUDIT',lambda:auditor.audit(task,audit_input,source,predictive_arrays=binding['predictive_arrays']))
     result['passed']=bool((result.get('navigation')or{}).get('passed')and result['first_error']is None and not result['secondary_errors']and (result.get('replay')or{}).get('passed')and (result.get('independent_audit')or{}).get('passed')and (result.get('independent_audit')or{}).get('whole_navigation_passed'))
    result['whole_navigation_passed']=bool(result['passed']);result['formal_SVG_task_executed']=True
    if ledger is not None:
     result['model_work']=ledger.snapshot();result['parallel_resource_report']=__import__('cpu_policy').report()
     if 'binding'in locals()and 'predictive_arrays'in binding:result['predictive_evidence_accounting']=binding['predictive_arrays'].snapshot()
    result.update(closed=True,wall_s=time.monotonic()-start,source_unchanged=all(sha(R/n)==h for n,h in source.items()if Path(n).name not in {'NATIVE_TRACE.npz','BODY_COMMANDS.json','SENSORS.json.gz','CONTACTS.json.gz','ACTUAL_CAUSAL_ENTRY_INPUT.json'}),source_hash_check_scope='runtime-safe source subset; allsource including historicalraw must be verified by owner AFTER childexit',full_source_verification_deferred_to_owner=True)
    if not result['source_unchanged']or remaining(window)<=0:result['passed']=False;result['whole_navigation_passed']=False
    try:resources.save_terminal(quota,result,lambda:save('RESULT.json',result))
    except BaseException as error:
     first(error,'SAVE_RESULT');result['passed']=False;os.write(2,(__import__('json').dumps(result,default=lambda a:a.tolist())+'\n').encode())
   quota.write_enforcement_active=False;signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,originalalarm);signal.signal(signal.SIGTERM,originalterm)
 return result

if __name__=='__main__':
 try:
  result=run();print(__import__('json').dumps(dict(passed=result['passed'],closed=result['closed'],first_error=result['first_error'])));raise SystemExit(0 if result['passed']else 1)
 except BaseException as error:
  if isinstance(error,SystemExit):raise
  put(O/'CLI_REFUSAL.json',dict(passed=False,closed=True,error=repr(error),models=0,physical_native=0,refused_before_admission=True));raise
