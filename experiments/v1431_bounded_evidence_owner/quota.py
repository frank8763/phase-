"""All-runs inode allocation and per-task evidence admission before a write."""
import json
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

class EvidenceQuota:
 def __init__(self,output,limits):
  self.output=Path(output).resolve();self.limits=dict(limits);self.last=None
  assert self.output.is_relative_to(R/'runs')and self.output.is_dir()and not Path(output).is_symlink()
  assert limits['storage_limit_bytes']==10*1024**3 and limits['maximum_task_evidence_bytes']==224*1024**2
  assert limits['remaining_archive_download_reserve_bytes']==256*1024**2 and limits['root_reserve_bytes']==512*1024**2

 def admit(self,pending_bytes,stage):
  needed=round_block(pending_bytes)+ERROR_RESERVE
  own=used(self.output);all_runs=used(R/'runs')
  proof=dict(stage=stage,requested_pending_bytes=pending_bytes,rounded_pending_and_error_reserve_bytes=needed,task_allocated_bytes=own,all_runs_allocated_bytes=all_runs,task_limit_bytes=self.limits['maximum_task_evidence_bytes'],root_peak_limit_bytes=self.limits['storage_limit_bytes'],checked_monotonic=time.monotonic())
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
