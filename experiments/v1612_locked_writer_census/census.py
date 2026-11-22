"""Serialize only charged writer-counter mutation while GNU du measures all bytes.

No file exclusion, errno suppression, quota change or rescan. Payload writers
can still run; any other du failure closes the round. Acquire before freshwire.
"""
from contextlib import ExitStack,contextmanager
import fcntl
import json
import os
from pathlib import Path
import stat
import time
R=Path(__file__).resolve().parents[2]
CAPS={'ACTUAL_ROS':24*1024**2,'PLANNER':8*1024**2,'SUPERVISOR_LOG':8*1024**2}

@contextmanager
def locked(output,limits,*,timeout_s=.5):
 output=Path(output)
 assert output.is_absolute()and output.resolve()==output and output.is_relative_to(R/'runs')and output.is_dir()
 assert limits['storage_limit_bytes']==15*1024**3 and limits['maximum_task_evidence_bytes']==224*1024**2
 assert 0<timeout_s<=.5
 registry=json.loads((output/'EXTERNAL_WRITER_RESERVATIONS.json').read_text())
 assert isinstance(registry['source_identity'],str)and len(registry['source_identity'])==64
 assert set(registry['writers'])==set(CAPS),'CENSUS_EXTERNAL_ROLE_SET'
 deadline=time.monotonic()+timeout_s
 with ExitStack()as stack:
  for role,cap in sorted(CAPS.items()):
   row=registry['writers'][role]
   assert row['maximum_bytes']==cap and row['source_hook_coverage_qualified']is True,'CENSUS_ROLE_CAP_OR_SOURCE'
   p=output/('WRITER_'+role+'_BYTES.lock')
   assert not p.is_symlink()and stat.S_ISREG(p.lstat().st_mode),'CENSUS_COUNTER_LOCK_NOT_REGULAR'
   stream=stack.enter_context(p.open('rb'))
   assert (p.lstat().st_dev,p.lstat().st_ino)==(os.fstat(stream.fileno()).st_dev,os.fstat(stream.fileno()).st_ino),'CENSUS_COUNTER_LOCK_REPLACED'
   while True:
    try:fcntl.flock(stream,fcntl.LOCK_SH|fcntl.LOCK_NB);break
    except BlockingIOError:
     assert time.monotonic()<deadline,'CENSUS_WRITER_LOCK_TIMEOUT'
     time.sleep(min(.001,max(0,deadline-time.monotonic())))
   assert (p.lstat().st_dev,p.lstat().st_ino)==(os.fstat(stream.fileno()).st_dev,os.fstat(stream.fileno()).st_ino),'CENSUS_COUNTER_LOCK_REPLACED'
   counter=json.loads((output/('WRITER_'+role+'_BYTES.json')).read_text())
   assert counter['role']==role and counter['maximum_bytes']==cap and counter['source_identity']==registry['source_identity'],'CENSUS_COUNTER_IDENTITY'
   assert 0<=counter['charged_bytes']<=cap,'CENSUS_COUNTER_OVER_CAP'
  assert time.monotonic()<=deadline,'CENSUS_WRITER_LOCK_TIMEOUT'
  # All original _put calls require the exclusive lock held from constructor,
  # reserve or reserve_control. Registered counters cannot rename until release.
  yield

def measure(output,limits,used):
 with locked(output,limits):
  return used(output),used(R/'runs')
