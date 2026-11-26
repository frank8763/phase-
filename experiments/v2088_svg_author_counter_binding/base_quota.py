"""All-runs inode allocation and per-task evidence admission before a write."""
import json
import importlib.util
from contextlib import contextmanager
from pathlib import Path
import subprocess
import time
R=Path(__file__).resolve().parents[2]
ERROR_RESERVE=64*1024
BLOCK=4096

def round_block(n):
 assert type(n)is int and n>=0
 return ((n+BLOCK-1)//BLOCK)*BLOCK

def used(path):return int(subprocess.check_output(['du','-sx','-B1',str(path)],text=True,timeout=10).split()[0])

def measure(output,limits):
 s=importlib.util.spec_from_file_location('v1615_fixed_writer_census',Path(__file__).with_name('census.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 return m.measure(output,limits,used)

class EvidenceQuota:
 def __init__(self,output,limits):
  self.output=Path(output).resolve();self.limits=dict(limits);self.last=None;self.holds={};self.spending=set()
  assert self.output.is_relative_to(R/'runs')and self.output.is_dir()and not Path(output).is_symlink()
  assert limits['storage_limit_bytes']==15*1024**3 and limits['maximum_task_evidence_bytes']==24*1024**2
  assert limits['remaining_archive_download_reserve_bytes']==32*1024**2 and limits['root_reserve_bytes']==512*1024**2

 def _held(self):return sum(value for key,value in self.holds.items()if key not in self.spending)

 def hold(self,key,pending_bytes):
  assert isinstance(key,str)and key and type(pending_bytes)is int and pending_bytes>=0
  previous=self.holds.get(key);self.holds[key]=round_block(pending_bytes)
  try:self.admit(0,'HOLD:'+key)
  except BaseException:
   if previous is None:self.holds.pop(key,None)
   else:self.holds[key]=previous
   raise

 def release(self,key):
  assert key in self.holds and key not in self.spending
  del self.holds[key]

 @contextmanager
 def spend(self,key):
  assert key in self.holds and key not in self.spending
  self.spending.add(key)
  try:yield
  finally:self.spending.remove(key)

 def admit(self,pending_bytes,stage):
  held=self._held();needed=round_block(pending_bytes)+ERROR_RESERVE+held
  own,all_runs=measure(self.output,self.limits)
  proof=dict(stage=stage,requested_pending_bytes=pending_bytes,unwritten_holds_bytes=held,rounded_pending_and_error_reserve_bytes=needed,task_allocated_bytes=own,all_runs_allocated_bytes=all_runs,task_limit_bytes=self.limits['maximum_task_evidence_bytes'],root_peak_limit_bytes=self.limits['storage_limit_bytes'],checked_monotonic=time.monotonic())
  assert own+needed<=self.limits['maximum_task_evidence_bytes'],'EVIDENCE_TASK_WRITE_QUOTA_REFUSED:'+json.dumps(proof,separators=(',',':'))
  reserve=self.limits['remaining_archive_download_reserve_bytes']+self.limits['root_reserve_bytes']
  assert all_runs+needed+reserve<=self.limits['storage_limit_bytes'],'EVIDENCE_ALL_RUNS_WRITE_QUOTA_REFUSED:'+json.dumps(proof,separators=(',',':'))
  self.last=proof;return proof

 def atomic(self,path,value,writer):
  path=Path(path);assert path.is_relative_to(self.output)and not path.is_symlink()
  # Original JSON writer expands native arrays/scalars; account its actual
  # serialization before both old+temporary copies can coexist.
  raw=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False,default=lambda x:x.tolist()).encode()+b'\n'
  self.admit(2*round_block(len(raw))+2*BLOCK,'ATOMIC_JSON:'+path.name)
  return writer(path,value)

 def save_npz(self,path,arrays,np):
  path=Path(path);assert path.is_relative_to(self.output)and not path.is_symlink()and not path.exists()
  raw=sum(np.asarray(value).nbytes for value in arrays.values())
  self.admit(2*round_block(raw)+65536+8192*len(arrays),'COMPLETE_NPZ:'+path.name)
  with path.open('xb')as stream:np.savez_compressed(stream,**arrays)

 def error_atomic(self,path,value,writer):
  # Only a small first-error record may consume the already retained64KiB.
  path=Path(path);assert path.is_relative_to(self.output)and not path.is_symlink()
  raw=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False,default=lambda x:x.tolist()).encode()+b'\n'
  assert 2*round_block(len(raw))+8192<=ERROR_RESERVE,'ERROR_RECORD_EXCEEDS_RESERVED_BYTES'
  own,total=measure(self.output,self.limits);needed=2*round_block(len(raw))+8192+self._held()
  assert own+needed<=self.limits['maximum_task_evidence_bytes']and total+needed+self.limits['remaining_archive_download_reserve_bytes']+self.limits['root_reserve_bytes']<=self.limits['storage_limit_bytes']
  return writer(path,value)
