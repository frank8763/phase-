"""Once new OS/source/finite-writer target, no author/JAX/model execution."""
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import time
import traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v1492_target_common',C/'common.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

def main():
 assert os.environ.get('PHASE_REPO')==str(R)and sorted(os.sched_getaffinity(0))==[4]
 O=c.O;claim=O/'ENTRY_ONCE_CLAIM.json'
 with claim.open('x')as f:json.dump(dict(pid=os.getpid(),unix=time.time(),models=0),f)
 started=time.monotonic();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('WORKER_IO_TARGET_90S')));signal.alarm(90)
 result=dict(passed=False,closed=False,scope='REAL_INNER_TMPFS_NATIVE_BYTE_SOURCE_AND_PIPE_ONLY',models=0,optimizer_calls=0,physical_native=0,JAX_or_author_imported=False);sources={}
 try:
  parent=c.read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and not parent['models_now_authorized']
  with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);sources=c.manifest()
   task=O/'io_target';task.mkdir();source_sha=c.digest(sources);c.put(task/'SOURCE_MANIFEST.json',sources)
   authority=dict(mode='IO_TARGET',models_authorized=False,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),source_manifest_sha256=source_sha,absolute_deadline_unix=min(time.time()+80,1795395600),hard_stop_monotonic=time.monotonic()+80)
   c.put(task/'APPROVAL.json',authority)
   negatives=[]
   for key,value in [('boot_id','foreign'),('models_authorized',True),('source_manifest_sha256','0'*64),('absolute_deadline_unix',0),('hard_stop_monotonic',0)]:
    bad=authority.copy();bad[key]=value
    try:c.validate_authority(bad,mode='IO_TARGET',source_manifest_sha256=source_sha,now_unix=time.time(),now_monotonic=time.monotonic(),boot_id=authority['boot_id'])
    except AssertionError:negatives.append(key)
    else:raise AssertionError('WORKER_AUTHORITY_NEGATIVE_ACCEPTED:'+key)
   writer=c.exact('v1492_parent_writer',R/'experiments/v1436_pathlib_control_rename/writer_budget.py').WriterBudget(task,role='SUPERVISOR_LOG',maximum_bytes=8*1024**2,source_identity=source_sha)
   sandbox=c.exact('v1492_new_sandbox',C/'sandbox.py');proof=sandbox.run(task,mode='IO_TARGET',writer=writer,wall_s=60)
   c.put(O/'IO_WORKER_RESULT.json',proof);assert proof['returncode']==0 and proof['terminal']['result']['passed']
   assert proof['terminal']['result']['JAX_not_loaded']and proof['archive_SHA_verified']
   result.update(passed=True,negative_cases=negatives,kernel_tmpfs_cap=True,native_ENOSPC=True,source_bound_originalguard=True,full_volatile_archive_SHA=True,actual_rusage=proof['terminal']['result']['rusage'],pipe_bytes=proof['pipe_bytes'],source_unchanged=all(c.sha(R/n)==h for n,h in sources.items()),not_optimizer_qualification=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  signal.alarm(0);result.update(closed=True,wall_s=time.monotonic()-started);c.put(c.O/'ENTRY_QUALIFICATION.json',result)
  if not sources:sources={str(p.relative_to(R)):c.sha(p)for p in C.iterdir()if p.is_file()}
  c.put(c.O/'SOURCE_FREEZE.json',dict(files=sources,scope='WORKER_OS_SOURCE_IO_ONLY',entry_passed=result['passed'],optimizer_runtime_qualified=False,models=0,physical_admission=False))
 return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
