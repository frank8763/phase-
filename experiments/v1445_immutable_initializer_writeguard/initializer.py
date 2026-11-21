"""One bounded canonical factory call; no route owner, commands or integrations."""
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
contract=exact('v1445_initializer_exact_contract',C/'contract.py')
io=exact('v1445_initializer_original_atomic',R/'experiments/v1383_exact_timed_handoff/evidence_io.py')

def run(task,approval,window):
 contract.admit(task,approval,window)
 caches=exact('v1445_task_only_cache_scope',C/'task_cache.py')
 guards=exact('v1445_immutable_original_guard',C/'guard_binding.py')
 with caches.TaskLocalCaches(task['output']),guards.bind_original_guard(task['output'])as receipt:
  value=_run(task,approval,window)
  if value.get('passed'):assert receipt['installed_original_guard_count']==1,'ORIGINAL_INITIALIZER_GUARD_NOT_BOUND'
  return value

def call_factory_once(factory_call,*,save,result):
 assert result['canonical_factory_call_attempts']==0 and not result.get('factory_call_reserved',False),'INITIALIZER_FACTORY_ALREADY_ATTEMPTED'
 result['factory_call_reserved']=True
 save('FACTORY_CALL_STARTED.json',dict(result))
 result.update(canonical_factory_call_attempts=1,canonical_vehicle_initializations=None,initializer_inflight_unknown=True)
 vehicle=factory_call()
 result.update(canonical_vehicle_initializations=1,initializer_inflight_unknown=False)
 return vehicle

def save_error(result,exc,save,*,stage):
 if result.get('first_error')is None:result['first_error']=dict(stage=stage,error=repr(exc),traceback=traceback.format_exc())
 else:result['secondary_errors'].append(dict(stage=stage,error=repr(exc)))
 try:save('FIRST_ERROR.json',result['first_error'])
 except BaseException as saving:result['secondary_errors'].append(dict(stage='SAVE_FIRST_ERROR',error=repr(saving)))

def _run(task,approval,window):
 # No physical binding, factory import or native call is reachable before this.
 qualified=contract.admit(task,approval,window)
 import fcntl
 out=Path(task['output']);assert out.is_dir()and not(out/'FACTORY_CALL_STARTED.json').exists()
 quota_module=exact('v1445_initializer_narrow_quota',C/'quota.py');quota=quota_module.EvidenceQuota(out,qualified['limits'])
 console=contract.read(out/'CONSOLE_RESERVATION.json');assert console['maximum_bytes']==4*1024**2 and console['entry_gate_qualified']is True and console['owner_source_sha256']==contract.sha(C/'owner.py')
 quota.hold('initializer-parent-console',4*1024**2);quota.bind_external_names(['initializer-parent-console'])
 external=[dict(name='initializer-parent-console',reservation_key='initializer-parent-console',remaining_byte_cap=4*1024**2,source_and_byte_cap_verified=True,live=True)]
 boundary=exact('v1445_qualified_actual_output_boundary',R/'experiments/v1439_actual_ros_startup_close/bounded_io.py')
 zeros=exact('v1445_native_step_zero_guard',C/'zero_steps.py')
 result=dict(passed=False,closed=False,canonical_factory_call_attempts=0,canonical_vehicle_initializations=0,initializer_inflight_unknown=False,internal_factory_model_constructions=None,actual_native=0,private_prediction_native=0,allocator_compute=0,own_replay_native=0,first_error=None,secondary_errors=[],physical_route_admission=False)
 def save(name,value):
  path=out/name
  return quota.error_atomic(path,value,io.atomic)if name=='FIRST_ERROR.json'else quota.atomic(path,value,io.atomic)
 def check():
  assert window['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
  assert min(window['absolute_deadline_unix']-time.time(),window['hard_stop_monotonic']-time.monotonic())>30,'INITIALIZER_MODEL_STAGE_DUAL_CLOCK_EXHAUSTED'
 def stopped(*_):raise TimeoutError('INITIALIZER_ONLY_LOCAL_HARD_STOP')
 previous=signal.signal(signal.SIGALRM,stopped);signal.signal(signal.SIGTERM,stopped)
 signal.setitimer(signal.ITIMER_REAL,max(.001,min(window['absolute_deadline_unix']-time.time(),window['hard_stop_monotonic']-time.monotonic())-15))
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);quota.write_enforcement_active=True
  try:
   with boundary.OutputBoundary(out,quota.charge_write):
    quota.prepare_grant(16*1024**2,phase='CANONICAL_INITIALIZER_ONLY',valid_for_s=180,external_writers=external);check()
    life=exact('v1445_actual_frozen_lifecycle_binding',R/'experiments/v1439_actual_ros_startup_close/lifecycle.py')
    old,Adapter,factory,_=life.physical_binding(out);np=old.np
    import mujoco as mj
    native_saves=[]
    def admit_save(path,bytes_count):
     check();quota.charge_write(path,bytes_count);native_saves.append(dict(path=str(Path(path).relative_to(out)),prewrite_cap_bytes=bytes_count))
    with zeros.forbid_steps(mj)as violations,boundary.native_model_saves(mj,admit_save):
     vehicle=call_factory_once(lambda:factory.create_vehicle(out/'physics',task),save=save,result=result)
     check();assert vehicle.count==0 and vehicle.d.time==0. and not vehicle.rows and not vehicle.commands
     before=life.owner_module.native_module.state_digest(vehicle);previous_adapter=vehicle.adapter
     vehicle.adapter=Adapter(vehicle.m,mj,vehicle.dt,encoders=previous_adapter.encoders);vehicle.adapter.virtual_rate=.6;vehicle.adapter.last=previous_adapter.last.copy();vehicle.adapter.integral=previous_adapter.integral
     assert before==life.owner_module.native_module.state_digest(vehicle),'INITIALIZER_ADAPTER_CHANGED_T0_FULL_STATE'
     arrays=dict(time=np.asarray([vehicle.d.time]),**{k:np.asarray(getattr(vehicle.d,k))[None].copy()for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']},applied_ctrl=np.empty((0,len(vehicle.d.ctrl))))
     assert all(np.isfinite(value).all()for value in arrays.values()),'INITIALIZER_T0_NONFINITE'
     quota.save_npz(out/'INITIAL_FULL_STATE.npz',arrays,np)
     with np.load(out/'INITIAL_FULL_STATE.npz',allow_pickle=False)as stream:assert all(np.array_equal(stream[k],v)for k,v in arrays.items())
     setup=contract.read(out/'physics/SETUP.json');assert setup['model_sha256']==contract.sha(out/'physics/scene_model.mjb')
     assert native_saves and not violations
     assert os.environ.get('MESA_SHADER_CACHE_DISABLE')=='true'and not list(out.rglob('mesa_shader_cache*')),'NATIVE_MESA_CACHE_WRITE_PATH_UNQUALIFIED'
     save('INITIALIZER_SOURCE_RECEIPT.json',dict(zero_native=True,n_actions=0,n_plus_one_states=1,not_full200_tail_or_replay=True,actual_t0_full_state_sha256=before,body=list(vehicle.body()),encoders=[float(x)for x in vehicle.steering_sample()],model_sha256=setup['model_sha256'],native_model_save_caps=native_saves,actual_cpu=sorted(os.sched_getaffinity(0)),all_internal_factory_model_constructions=None))
     result.update(passed=True,native_model_save_size_and_actual_file_qualified=True,full_t0_state_roundtrip=True,zero_step_guard_violations=[],source_unchanged=all(contract.sha(R/p)==h for p,h in qualified['source_hashes'].items()))
     assert result['source_unchanged']
  except BaseException as exc:
   quota.retire_grant();save_error(result,exc,save,stage='CANONICAL_INITIALIZER_ONLY')
  finally:
   quota.retire_grant();result.update(closed=True,closed_unix=time.time())
   if result['first_error']is not None or result['secondary_errors']:result['passed']=False
   try:save('RESULT.json',result)
   except BaseException as exc:
    result['passed']=False;result['secondary_errors'].append(dict(stage='SAVE_FINAL_RESULT',error=repr(exc)));os.write(2,(json.dumps(result,allow_nan=False)+'\n').encode())
   quota.write_enforcement_active=False;signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous)
 return result
