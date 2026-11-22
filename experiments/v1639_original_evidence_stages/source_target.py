"""Only new grant/terminal/buffer paths; zero original policy/model/FFI."""
import ast,fcntl,hashlib,importlib.abc,io,json,os,runpy,sys,time,traceback
from pathlib import Path
from context import C,O,R,put,read,sha,load

def main():
 start=time.monotonic();os.environ['MUJOCO_GL']='osmesa';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
 load('v1639_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'mujoco','torch','OpenGL','jax','rclpy','kernel','factory','vehicle','runtime'}:raise AssertionError('SOURCE_ONLY_NO_MODEL_IMPORT:'+name)
 sys.meta_path.insert(0,Ban())
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 source=read(R/'runs/v1636_cached_original_runtime/SOURCE_FREEZE.json')['files'].copy()
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,source_only=True,actual_runtime_qualified=False)
 try:
  assert read(R/'runs/v1636_cached_original_runtime/POST_ROUND_STORAGE_BARRIER.json')['passed']
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
  for n in ['AUTHORIZATION.json','TASKS_LOCKED.json','PILOT_TASK.json','LIMITS_DRAFT.json','PILOT_SPEC_AMENDMENT.json']:source[str((O/n).relative_to(R))]=sha(O/n)
  initial=R/'runs/v1636_cached_original_runtime/pilot_WE_full/INITIAL_FULL_STATE.npz';source[str(initial.relative_to(R))]=sha(initial)
  assert all(sha(R/n)==h for n,h in source.items())
  reused=[]
  for n in ['context.py','runtime_binding.py','history_binding.py','work.py','quota.py','audit_binding.py','transforms.py','pilot_entry.py','source_owner.py']:
   new=ast.dump(ast.parse((C/n).read_text()),include_attributes=False).replace(C.name,'v1636_cached_original_runtime')
   old=ast.dump(ast.parse((R/'experiments/v1636_cached_original_runtime'/n).read_text()),include_attributes=False)
   assert new==old,('UNEXPECTED_UNCHANGED_BODY',n);reused.append(n)
  import numpy as np,gzip,ctypes
  original_dll=ctypes.CDLL
  def noffi(*a,**k):raise AssertionError('SOURCE_ONLY_NO_DLL')
  ctypes.CDLL=noffi
  def profile(frame,event,arg):
   if event=='call':assert not any(x in frame.f_code.co_filename for x in ['/coupled_model.py','/coupled_control.py','/factory.py','/vehicle.py'])
  sys.setprofile(profile)
  from quota import EvidenceQuota,base
  resources=load('v1639_new_resources',C/'resources.py');capture=load('v1639_new_buffered_capture',C/'capture.py')
  root=O/'source_target';root.mkdir();q=EvidenceQuota(root,read(O/'LIMITS_DRAFT.json'));q.bind_external_names([]);q.write_enforcement_active=True
  boundary=load('v1639_original_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
  atomic=load('v1639_original_atomic',R/'experiments/v1383_exact_timed_handoff/evidence_io.py').atomic
  resources.reserve_terminal(q);q.hold('SOFTWARE_existing_capture_pending',70*1024**2)
  negatives=[];emitted=0;charges=0
  def charge(path,n):
   nonlocal emitted,charges
   emitted+=n;charges+=1;return q.charge_write(path,n)
  def refuse(label,fn):
   try:fn()
   except(AssertionError,OSError,ValueError):negatives.append(label)
   else:raise AssertionError('SOURCE_NEGATIVE_ACCEPTED:'+label)
  with boundary.OutputBoundary(root,charge):
   grant=resources.prepare(q,'STOPPED_EVENT_PREPARATION')
   assert grant['capacity_bytes']<=224*1024**2-70*1024**2-resources.TERMINAL_BYTES-base.ERROR_RESERVE
   with np.load(initial,allow_pickle=False)as z:full_raw=sum((44950+1)*z[k].nbytes for k in z.files)
   pending=2*base.round_block(full_raw)+65536+8192*6
   assert pending>32*1024**2
   q.admit(pending,'SOFTWARE_DECLARED_NPLUS1_PRECHARGE_NO_ARRAY_CREATION')
   refuse('explicit_capacity_cannot_steal_holds',lambda:resources.prepare(q,'STOPPED_EVENT_PREPARATION',cap=224*1024**2))
   resources.prepare(q,'STOPPED_EVENT_PREPARATION')
   data=[dict(native_tick=i,time=i*.01,xy=[-.2,.3],ranges=[.1,.2,.3],note='测试α\\n')for i in range(4096)]
   expected=io.StringIO();json.dump(data,expected);expected_bytes=expected.getvalue().encode()
   secondary=[];original_text=capture.TextChunks;input_chunks=[0]
   class Counted(original_text):
    def write(self,text):input_chunks[0]+=1;return super().write(text)
   capture.TextChunks=Counted
   try:
    before=charges
    with capture.exact_compressed_paths(root,secondary):
     with gzip.open(root/'SENSORS.json.gz','xt')as stream:json.dump(data,stream)
     refuse('duplicate_target_no_retry',lambda:gzip.open(root/'SENSORS.json.gz','xt').__enter__())
     refuse('foreign_gzip_target',lambda:gzip.open(root/'FOREIGN.json.gz','xt').__enter__())
    assert not secondary and gzip.decompress((root/'SENSORS.json.gz').read_bytes())==expected_bytes
    gzip_charge_calls=charges-before;assert gzip_charge_calls<input_chunks[0]//100
   finally:capture.TextChunks=original_text
   refuse('writable_descriptor_still_refused',lambda:original_text(io.BytesIO()).fileno())
   class Broken:
    def __init__(self,*a,**k):pass
    def write(self,value):raise OSError('SOFTWARE_BUFFER_WRITE_FAILURE')
    def close(self):raise OSError('SOFTWARE_GZIP_CLOSE_FAILURE')
   old_gzip=gzip.GzipFile;gzip.GzipFile=Broken;secondary=[];primary=ValueError('SOFTWARE_PRIMARY_JSON_FAILURE')
   try:
    try:
     with capture.exact_compressed_paths(root,secondary):
      with gzip.open(root/'CONTACTS.json.gz','xt')as stream:
       stream.write('durable-prefix');raise primary
    except ValueError as error:assert error is primary
    else:raise AssertionError('PRIMARY_ERROR_LOST')
    assert [z['stage']for z in secondary]==['UTF8_BUFFER_FLUSH','GZIP_CLOSE']
   finally:gzip.GzipFile=old_gzip
   failed=original_text(Broken())
   failed.write('small')
   refuse('buffer_first_write_failure',failed.flush);refuse('buffer_poison_no_retry',failed.flush)
   resources.prepare(q,'COMPLETE_ZERO_TAIL_OR_CLOSURE',ttl=300);q.grant['expires_monotonic']=time.monotonic()-1
   refuse('expired_normal_writer_cannot_consume_terminal',lambda:q.charge_write(root/'FORBIDDEN',1))
   refuse('oversized_terminal_record',lambda:resources.save_terminal(q,{'huge':'x'*(1024**2)},lambda:None))
   q.release('SOFTWARE_existing_capture_pending')
   record=dict(passed=True,source_only=True,models=0,FFI_loads=0,FFI_calls=0,physical_native=0,replay_native=0,raw_JSON_bytes=len(expected_bytes),original_JSON_bytewise_roundtrip=True,input_JSON_write_chunks=input_chunks[0],actual_gzip_charge_calls=gzip_charge_calls,software_Nplus1_pending_bytes=pending,large_arrays_not_created=True,first_error_preserved=True,secondary_faults=secondary,negative_cases=negatives,all_holds_respected=True,no_task_or_root_cap_increase=True)
   resources.save_terminal(q,record,lambda:q.atomic(root/'QUALIFICATION.json',record,atomic))
   assert resources.TERMINAL_KEY not in q.holds and q.grant is None
  q.write_enforcement_active=False;sys.setprofile(None);ctypes.CDLL=original_dll
  try:runpy.run_path(str(C/'driver.py'),run_name='__main__')
  except AssertionError as error:assert str(error)=='NEW_ORIGINAL_CONTRACT_PILOT_NOT_ADMITTED'
  else:raise AssertionError('UNADMITTED_DRIVER_EXECUTED')
  put(O/'SOURCE_FREEZE.json',dict(files=source,source_only=True,models_authorized=False))
  result.update(passed=True,source_members=len(source),negative_cases=len(negatives),unchanged_modules_reused=reused,real_CLI_missing_admission_refused=True,source_proof_sha256=sha(root/'QUALIFICATION.json'))
 except BaseException as error:
  sys.setprofile(None);result.update(first_error=repr(error),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=source,models_authorized=False))
 finally:
  result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
