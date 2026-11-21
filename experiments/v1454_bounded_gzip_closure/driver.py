"""One canonical initialization, original zero200, actual-source audit and replay."""
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import signal
import time
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
contract=exact('v1454_narrow_contract',C/'contract.py')
budgets=exact('v1454_native_budget',C/'native_budget.py')
io=exact('v1454_original_atomic',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')

def first_error(result,exc,save,stage):
 if result['first_error']is None:result['first_error']=dict(stage=stage,error=repr(exc),traceback=traceback.format_exc())
 else:result['secondary_errors'].append(dict(stage=stage,error=repr(exc)))
 try:save('FIRST_ERROR.json',result['first_error'])
 except BaseException as secondary:result['secondary_errors'].append(dict(stage='SAVE_FIRST_ERROR',error=repr(secondary)))

def factory_once(call,save,result):
 assert result['canonical_factory_call_attempts']==0 and not result.get('factory_reserved',False),'ZERO200_FACTORY_ALREADY_ATTEMPTED'
 result['factory_reserved']=True;save('FACTORY_CALL_STARTED.json',dict(result))
 result.update(canonical_factory_call_attempts=1,canonical_vehicle_initializations=None,initializer_inflight_unknown=True)
 v=call();result.update(canonical_vehicle_initializations=1,initializer_inflight_unknown=False);return v

def run(task,approval,window):
 q=contract.admit(task,approval,window) # before any physical import
 caches=exact('v1454_frozen_task_caches',R/'experiments/v1447_full_module_guard_identity/task_cache.py')
 guards=exact('v1454_frozen_immutable_guard',R/'experiments/v1447_full_module_guard_identity/guard_binding.py')
 with caches.TaskLocalCaches(task['output']),guards.bind_original_guard(task['output'])as receipt:return _run(task,approval,window,q,receipt)

def _run(task,approval,window,q,guard_receipt):
 out=Path(task['output']);limits=q['limits'];assert not(out/'FACTORY_CALL_STARTED.json').exists()
 quota=exact('v1454_scoped_quota',C/'quota.py').EvidenceQuota(out,limits)
 console=contract.read(out/'CONSOLE_RESERVATION.json');assert console['maximum_bytes']==4*1024**2 and console['owner_source_sha256']==contract.sha(C/'owner.py')and console['qualified']is True
 quota.hold('parent-console',4*1024**2);quota.bind_external_names(['parent-console'])
 external=[dict(name='parent-console',reservation_key='parent-console',remaining_byte_cap=4*1024**2,source_and_byte_cap_verified=True,live=True)]
 boundary=exact('v1454_original_boundary',R/'experiments/v1439_actual_ros_startup_close/bounded_io.py')
 result=dict(passed=False,closed=False,canonical_factory_call_attempts=0,canonical_vehicle_initializations=0,internal_factory_model_constructions=None,initializer_inflight_unknown=False,actual_native=0,own_replay_native=0,private_prediction_native=0,first_error=None,secondary_errors=[],physical_route_admission=False)
 budget=budgets.NativeBudget(window);v=None;capture=None;owner=None;pump=None;journal=None;initial_arrays=None;setup=None
 def save(name,value):
  fn=quota.error_atomic if name=='FIRST_ERROR.json'else quota.atomic
  return fn(out/name,value,io.atomic)
 def grant(phase,cap=8*1024**2):
  quota.retire_grant();return quota.prepare_grant(cap,phase=phase,valid_for_s=180,external_writers=external)
 def check(stage,n):
  budget.check();assert stage=='ACTUAL_STOP_TAIL'and n==1 and budget.stage=='actual_zero_tail'
  assert v is not None and v.count==budget.actual and budget.actual+n<=200
  capture.update(v,requested_native=n)
 def close_attempt(stage,fn):
  try:return fn()
  except BaseException as exc:first_error(result,exc,save,stage);return None
 def stopped(*_):raise TimeoutError('ZERO200_SHARED_PHASE_OR_ROOT_DEADLINE')
 oldalarm=signal.signal(signal.SIGALRM,stopped);oldterm=signal.signal(signal.SIGTERM,stopped)
 def arm():signal.setitimer(signal.ITIMER_REAL,max(.001,budget.remaining()))
 arm();started=time.monotonic()
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);quota.write_enforcement_active=True
  try:
   with boundary.OutputBoundary(out,quota.charge_write):
    grant('CANONICAL_INITIALIZER_ONLY',16*1024**2)
    life=exact('v1454_frozen_route_lifecycle',R/'experiments/v1449_route_initializer_binding/lifecycle.py')
    old,Adapter,factory,replay=life.physical_binding(out);np=old.np
    import mujoco as mj
    with budgets.guard_native_API(mj,budget):
     with boundary.native_model_saves(mj,quota.charge_write):v=factory_once(lambda:factory.create_vehicle(out/'physics',task),save,result)
     old.pin();budget.bind_actual(v.d);assert v.count==0 and not v.rows and not v.commands
     before=life.owner_module.native_module.state_digest(v);previous=v.adapter
     v.adapter=Adapter(v.m,mj,v.dt,encoders=previous.encoders);v.adapter.virtual_rate=.6;v.adapter.last=previous.last.copy();v.adapter.integral=previous.integral
     assert before==life.owner_module.native_module.state_digest(v)
     capture=exact('v1454_original_capture',C/'capture_budget.py').CaptureBudget(quota);capture.update(v)
     limited=exact('v1454_zero_only_owner',C/'closure_owner.py');owner=limited.ZeroTailOwner(v,output=out,run_id=task['run_id'],atomic=lambda p,x:save(Path(p).name,x),check=check)
     initial_arrays=dict(time=np.asarray(v.d.time),**{k:np.asarray(getattr(v.d,k)).copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']})
     quota.save_npz(out/'INITIAL_FULL_STATE.npz',initial_arrays,np);save('INITIAL_PACKET.json',owner.native.packet(None));setup=contract.read(out/'physics/SETUP.json')
     journal=(out/'ACTUAL_OWNER_JOURNAL.jsonl').open('x',buffering=1)
     def append(row):
      raw=json.dumps(row,separators=(',',':'),allow_nan=False)+'\n';quota.admit(2*len(raw.encode())+16384,'ORIGINAL_PREFIX_RECEIPT');journal.write(raw);journal.flush()
     pump=life.pump_module.Pump(owner,check_budget=check,append=append,model_peer=None)
     budget.enter('actual_zero_tail');arm();grant('ACTUAL_ZERO200')
     for _ in range(200):pump.prefix_step(None,stop_tail=True)
     assert budget.actual==v.count==len(v.rows)==owner.native.applied==200 and owner.native.last_zero_count==200
     assert all(row['request']==[0.,0.,False]for row in owner.native.events)
     journal.close();journal=None
     arrays={k:np.concatenate([initial_arrays[k][None],np.asarray([row[k]for row in v.rows])],axis=0)for k in initial_arrays}
     arrays['applied_ctrl']=np.asarray([row['ctrl']for row in v.rows]);assert len(arrays['qpos'])==201 and len(arrays['applied_ctrl'])==200
     quota.save_npz(out/'FULL_STATE_NPLUS1.npz',arrays,np)
     with np.load(out/'FULL_STATE_NPLUS1.npz',allow_pickle=False)as stream:assert all(np.array_equal(stream[k],value)for k,value in arrays.items())
     body=list(v.body());assert max(abs(x)for x in body[3:])<=.03 and max(abs(x)for x in v.steering_sample()[2:])<=.03 and max(abs(x)for x in v.adapter.last[2:])<=1e-8,'ZERO200_NOT_RESTED'
     result.update(complete200_applied_zero_tail=True,full_Nplus1_roundtrip=True)
     result['physical']=capture.finish(v)
     budget.enter('allocator');arm();grant('ALLOCATOR_ONLY')
     rows,events,_=exact('v1454_original_receipts',R/'experiments/v1423_integrated_route_audit/recorded.py').collect(out);assert len(rows)==200 and not events
     allocation=exact('v1454_original_actual_source_allocation',R/'experiments/v1430_actual_allocator_provenance/allocation.py')
     result['allocation']=allocation.audit(v,rows,contract.read(out/'INITIAL_PACKET.json'),initial_fullstate=initial_arrays,setup=setup,Adapter=Adapter,mj=mj,np=np,lock=lock,maximum_recomputations=200,deadline_unix=budget.phase_end_unix,deadline_monotonic=budget.phase_end_monotonic,save=lambda x:save('INDEPENDENT_ALLOCATION.json',x))
     assert result['allocation']['passed']and result['allocation']['allocator_recomputations']==200,'ZERO200_ACTUAL_ALLOCATOR_REFUSED'
     budget.enter('own_replay');arm();grant('OWN_REPLAY_ONLY')
     result['replay']=replay(v,budget.phase_end_unix,out/'physics');assert result['replay']['passed']and result['replay']['replay_native']==200,'ZERO200_OWN_REPLAY_REFUSED'
     budget.enter('closed');arm();grant('FINAL_EVIDENCE')
     assert budget.actual_compute==budget.allocator_compute==200 and not budget.violations
     assert guard_receipt['installed_original_guard_count']==1
     result['passed']=True
  except BaseException as exc:
   quota.retire_grant();first_error(result,exc,save,budget.stage)
  finally:
   quota.retire_grant()
   signal.setitimer(signal.ITIMER_REAL,max(.001,min(window['absolute_deadline_unix']-time.time(),window['hard_stop_monotonic']-time.monotonic())-2))
   with boundary.OutputBoundary(out,quota.charge_write):
    # Save the executed prefix only. No extra tail or retry after a first error.
    if journal is not None:close_attempt('CLOSE_JOURNAL',journal.close)
    if pump is not None:close_attempt('CLOSE_SOCKET',pump.close)
    if owner is not None:close_attempt('CLOSE_OWNER',owner.close)
    if v is not None and capture is not None and not capture.finish_attempted and 'physical'not in result:result['physical']=close_attempt('SAVE_EXECUTED_PREFIX',lambda:capture.finish(v))
    result.update(native_accounting=budget.snapshot(),actual_native=None if budget.inflight=='actual'else budget.actual,own_replay_native=None if budget.inflight=='replay'else budget.replay,closed=True,wall_s=time.monotonic()-started,source_unchanged=all(contract.sha(R/p)==h for p,h in q['source_hashes'].items()),native_Mesa_cache_disabled=os.environ.get('MESA_SHADER_CACHE_DISABLE')=='true',native_Mesa_cache_members=[str(p.relative_to(out))for p in out.rglob('mesa_shader_cache*')])
    if result['first_error']or result['secondary_errors']or not result['source_unchanged']or not result['native_Mesa_cache_disabled']or result['native_Mesa_cache_members']:result['passed']=False
    try:save('RESULT.json',result)
    except BaseException as exc:result['passed']=False;result['secondary_errors'].append(dict(stage='SAVE_RESULT',error=repr(exc)));os.write(2,(json.dumps(result,allow_nan=False)+'\n').encode())
   quota.write_enforcement_active=False;signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,oldalarm);signal.signal(signal.SIGTERM,oldterm)
 return result
