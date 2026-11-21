"""Finite tmpfs worker: I/O target now, optimizer only with separate authority."""
import base64
import ctypes
import errno
import fcntl
import gzip
import hashlib
import importlib.abc
import importlib.util
import io
import json
import os
from pathlib import Path
import resource
import signal
import sys
import tarfile
import time
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v1492_worker_common',C/'common.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
class NoModels(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','rclpy','vehicle','factory'}:raise AssertionError('OPTIMIZER_MODEL_IMPORT_FORBIDDEN:'+name)

def main():
 task=Path(os.environ['PHASE_WORKER_TASK']);mode=os.environ['PHASE_WORKER_MODE'];volatile=task/'volatile';authority=c.read(task/'APPROVAL.json')
 assert sorted(os.sched_getaffinity(0))==[4]and os.environ.get('PHASE_REPO')==str(R)
 assert authority['mode']==mode and authority['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert time.time()<authority['absolute_deadline_unix']<=1795395600 and time.monotonic()<authority['hard_stop_monotonic']
 assert task.is_relative_to(R/'runs')and not task.is_symlink()
 source=c.read(task/'SOURCE_MANIFEST.json');assert c.digest(source)==authority['source_manifest_sha256']and all(c.sha(R/n)==h for n,h in source.items())
 c.validate_authority(authority,mode=mode,source_manifest_sha256=c.digest(source),now_unix=time.time(),now_monotonic=time.monotonic(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));resource.setrlimit(resource.RLIMIT_FSIZE,(2*1024**2,2*1024**2));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('INNER_WORKER_SCOPE_EXPIRED')));signal.alarm(30 if mode=='IO_TARGET'else 590)
 sys.meta_path.insert(0,NoModels());c.guard(volatile)
 boundary=c.exact('v1492_original_bounded_io',R/'experiments/v1436_pathlib_control_rename/bounded_io.py')
 budget_source=c.exact('v1492_original_writer_budget',R/'experiments/v1436_pathlib_control_rename/writer_budget.py')
 # Metadata bootstrap bounded by the same kernel tmpfs; before any author or
 # native compile activity. The initial16KiB writer debit covers its two files.
 writer=budget_source.WriterBudget(volatile,role='PLANNER',maximum_bytes=2*1024**2,source_identity=authority['source_manifest_sha256'])
 c.put(volatile/'APPROVAL.json',authority)
 registry=dict(source_identity=writer.identity,purpose='PRIEST_OPTIMIZER_ONLY',approval_sha256=c.sha(volatile/'APPROVAL.json'),writers={'PLANNER':dict(maximum_bytes=writer.maximum,source_hook_coverage_qualified=mode=='OPTIMIZER')})
 c.put(volatile/'EXTERNAL_WRITER_RESERVATIONS.json',registry)
 result=dict(passed=False,scope=mode,models=0,optimizer_calls=0,physical_native=0,author_or_JAX_imported=False,source_manifest_sha256=authority['source_manifest_sha256'],original_error=None)
 try:
  with boundary.OutputBoundary(volatile,writer.reserve)as active:
   if mode=='IO_TARGET':
    # Real native write bypasses Python hooks but cannot exceed the tmpfs.
    libc=ctypes.CDLL(None,use_errno=True);libc.open.argtypes=[ctypes.c_char_p,ctypes.c_int,ctypes.c_int];libc.write.argtypes=[ctypes.c_int,ctypes.c_void_p,ctypes.c_size_t];libc.write.restype=ctypes.c_ssize_t
    target=volatile/'NATIVE_CAP_PROBE';fd=libc.open(os.fsencode(target),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);assert fd>=0
    block=ctypes.create_string_buffer(b'x'*8192);count=0;failure=None
    try:
     for i in range(32):
      n=libc.write(fd,block,8192)
      if n<0:failure=ctypes.get_errno();break
      count+=n
    finally:libc.close(fd)
    assert failure==errno.ENOSPC and 0<count<65536,'FINITE_NATIVE_TMPFS_CAP_NOT_ENFORCED'
    probe=dict(native_partial_bytes=count,error=errno.errorcode[failure],sha256=c.sha(target),actual_statvfs_block_size=os.statvfs(volatile).f_frsize)
    target.unlink() # Only deterministic I/O stress fixture, proof saved below.
    try:(task/'FORBIDDEN_OUTSIDE_VOLATILE').write_text('forbidden')
    except (PermissionError,AssertionError):outside_rejected=True
    else:raise AssertionError('WORKER_VOLATILE_ESCAPE_ACCEPTED')
    c.put(volatile/'IO_PROOF.json',dict(probe=probe,outside_rejected=outside_rejected,models=0))
    result.update(passed=True,native_tmpfs_probe=probe,outside_write_rejected=True,charged_writer_bytes=writer._read()['charged_bytes'],JAX_not_loaded='jax'not in sys.modules,models=0)
   else:
    assert authority['scope']=='PRIEST_OPTIMIZER_ONLY'and authority['models_authorized']is False
    qualified=c.read(R/'runs/v1492_priest_optimizer_worker/ENTRY_QUALIFICATION.json');freeze=c.read(c.O/'SOURCE_FREEZE.json')
    assert qualified['passed']and freeze['entry_passed']and freeze['files']==source
    recovery=c.read(task/'CURRENT_SOURCE_REMOTE_RECOVERY.json')
    assert recovery['passed']and recovery['source_freeze_sha256']==c.sha(c.O/'SOURCE_FREEZE.json')
    request=c.read(task/'OPTIMIZER_REQUEST.json');current=c.read(task/'CURRENT_INPUT.json')
    loader=c.exact('v1492_qualified_kernel_loader',C/'kernel_loader.py')
    work=c.exact('v1492_separate_math_work',R/'experiments/v1487_priest_optimizer_contract/work_budget.py')
    def receipt(value):
     c.put(volatile/'WORK_PROGRESS.json',value)
     print(json.dumps(dict(kind='PRIEST_MATH_STAGE',source_manifest_sha256=authority['source_manifest_sha256'],value=value),separators=(',',':')),flush=True)
    math_budget=work.WorkBudget(receipt=receipt,absolute_deadline_unix=authority['absolute_deadline_unix'],hard_stop_monotonic=authority['hard_stop_monotonic'])
    with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
     fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
     kernel,jax,jnp,np=loader.load(authority=authority,request=request,lock=lock,output_boundary=active)
     result['author_or_JAX_imported']=True
     observer=c.exact('v1500_finite_live_thread_observer',R/'experiments/v1503_priest_namespace_observation/thread_observation.py')
     result['thread_affinities_after_kernel']=observer.observe('AFTER_KERNEL')
     call=c.exact('v1492_exact_author_call',C/'optimizer_call.py')
     output=call.run(request,current=current,kernel=kernel,jax=jax,jnp=jnp,np=np,budget=math_budget,authority=authority)
     result['thread_affinities_after_optimizer']=observer.observe('AFTER_OPTIMIZER')
    c.put(volatile/'OPTIMIZER_PROPOSAL.json',output)
    result.update(passed=True,optimizer_calls=math_budget.counts['optimizer_calls'],work_accounting=math_budget.counts.copy(),proposal_sha256=output['candidate']['proposal_sha256'],actual_control_domain_qualified=False,complete_response_witness_qualified=False,input_role='SAVED_ACTUAL_INPUT_MODEL_ONLY',saved_actual_input_not_fresh_wire=True)
   result['all_sources_unchanged']=all(c.sha(R/n)==h for n,h in source.items())
   assert result['all_sources_unchanged']
 except BaseException as e:
  result.update(passed=False,original_error=repr(e),traceback=traceback.format_exc())
  if 'math_budget'in locals():result.update(optimizer_calls=math_budget.counts['optimizer_calls'],work_accounting=math_budget.counts.copy())
  if 'observer'in locals()and isinstance(e,observer.ObservationError):result['thread_observation_failure']=e.proof
 finally:
  result['closed']=True;result['rusage']=dict(maxrss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,threads=len(list(Path('/proc/self/task').iterdir())),CPU=sorted(os.sched_getaffinity(0)))
  try:c.put(volatile/'RESULT.json',result)
  except BaseException as e:result['secondary_result_save_error']=repr(e)
  # Preserve every volatile regular file without exposing native writableFDs.
  files=sorted(p for p in volatile.rglob('*')if p.is_file());assert len(files)<=256
  members={};buffer=io.BytesIO()
  with gzip.GzipFile(fileobj=buffer,mode='wb',mtime=0)as compressor,tarfile.open(fileobj=compressor,mode='w|')as archive:
   for p in files:
    assert not p.is_symlink();data=p.read_bytes();name=str(p.relative_to(volatile));members[name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest());info=tarfile.TarInfo(name);info.size=len(data);archive.addfile(info,io.BytesIO(data))
  raw=buffer.getvalue();assert len(raw)<=4*1024**2
  final=dict(kind='PHASE_BOUNDED_WORKER_TERMINAL',result=result,volatile_members=members,volatile_archive_sha256=hashlib.sha256(raw).hexdigest(),volatile_archive_base64=base64.b64encode(raw).decode())
  print(json.dumps(final,separators=(',',':'),allow_nan=False),flush=True)
 return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
