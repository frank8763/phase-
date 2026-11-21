"""Explicit byte cap for one isolated ROS/planner/log writer.

The native owner reserves the full cap before any child starts. This counter
only grants writes inside the declared task directory and never opens models.
Every output-producing entry still has to use this seam before qualification.
"""
import fcntl
import json
import os
from pathlib import Path
R=Path(__file__).resolve().parents[2]
BLOCK=4096

def charge_bytes(value):
 assert type(value)is int and value>=0
 return ((value+BLOCK-1)//BLOCK)*BLOCK

class WriterBudget:
 def __init__(self,output,*,role,maximum_bytes,source_identity):
  self.output=Path(output).resolve();assert self.output.is_relative_to(R/'runs')and self.output.is_dir()
  assert role in {'ACTUAL_ROS','MODELED_ROS','PLANNER','SUPERVISOR_LOG'}and type(maximum_bytes)is int and 16384<=maximum_bytes<=32*1024**2
  assert isinstance(source_identity,str)and len(source_identity)==64
  self.role=role;self.maximum=maximum_bytes;self.identity=source_identity
  self.path=self.output/('WRITER_'+role+'_BYTES.json');self.lock_path=self.output/('WRITER_'+role+'_BYTES.lock')
  with self.lock_path.open('a')as lock:
   fcntl.flock(lock,fcntl.LOCK_EX)
   if self.path.exists():self._read()
   else:self._put(dict(role=role,maximum_bytes=maximum_bytes,source_identity=source_identity,charged_bytes=16384,grants=0,paths=[],models=0))

 def _read(self):
  value=json.loads(self.path.read_text());assert value['role']==self.role and value['maximum_bytes']==self.maximum and value['source_identity']==self.identity
  assert 0<=value['charged_bytes']<=self.maximum;return value

 def _put(self,value):
  temporary=self.path.with_suffix('.json.pending');temporary.write_text(json.dumps(value,allow_nan=False)+'\n');temporary.replace(self.path)

 def reserve(self,path,pending_bytes):
  path=Path(path);assert path.is_absolute()and path.is_relative_to(self.output)and not path.is_symlink()
  assert path.parent.resolve().is_relative_to(self.output)
  assert type(pending_bytes)is int and pending_bytes>=0
  with self.lock_path.open('a')as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);value=self._read()
   name=str(path.relative_to(self.output));new_path=name not in value['paths']
   requested=pending_bytes+(2*len(name.encode())+8192 if new_path else 0)
   assert value['charged_bytes']+requested<=self.maximum,'CHILD_OUTPUT_BYTE_CAP_EXHAUSTED'
   value['charged_bytes']+=requested;value['grants']+=1
   if new_path:value['paths'].append(name)
   self._put(value)
   return dict(value,last_granted_bytes=requested)

 def reserve_control(self,path,pending_bytes):
  # These are the only two supervisory control files outside the task folder.
  # Native, ROS and planner roles cannot obtain this capability.
  path=Path(path);allowed={R/'REVIEW_PENDING':'REVIEW_PENDING',R/'runs/v1382_weekend_campaign/LEDGER.json':'WEEKEND_LEDGER',R/'runs/v1382_weekend_campaign/LEDGER.json.tmp':'WEEKEND_LEDGER_ATOMIC_STAGE'}
  assert self.role=='SUPERVISOR_LOG'and path in allowed and not path.is_symlink()
  assert type(pending_bytes)is int and pending_bytes>=0
  name='@CONTROL/'+allowed[path]
  with self.lock_path.open('a')as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);value=self._read();new=name not in value['paths']
   requested=pending_bytes+(2*len(name)+8192 if new else 0)
   assert value['charged_bytes']+requested<=self.maximum,'SUPERVISOR_CONTROL_BYTE_CAP_EXHAUSTED'
   value['charged_bytes']+=requested;value['grants']+=1
   if new:value['paths'].append(name)
   self._put(value);return dict(value,last_control_target=str(path))

 def atomic(self,path,value,writer):
  encoded=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False,default=lambda x:x.tolist()).encode()+b'\n'
  self.reserve(path,2*charge_bytes(len(encoded))+8192);return writer(path,value)

 def append(self,path,value,stream):
  encoded=json.dumps(value,separators=(',',':'),allow_nan=False,default=lambda x:x.tolist())+'\n'
  self.reserve(path,len(encoded.encode()));stream.write(encoded);stream.flush()

 @classmethod
 def from_environment(cls):
  import hashlib
  output=Path(os.environ['PHASE_BOUNDED_TASK_OUTPUT']);role=os.environ['PHASE_BOUNDED_WRITER_ROLE'];identity=os.environ['PHASE_BOUNDED_SOURCE_ID']
  path=output/'EXTERNAL_WRITER_RESERVATIONS.json';authority=json.loads(path.read_text());assert authority['source_identity']==identity
  assert role in authority['writers']and authority['writers'][role]['source_hook_coverage_qualified']is True
  assert hashlib.sha256((output/'APPROVAL.json').read_bytes()).hexdigest()==authority['approval_sha256']
  return cls(output,role=role,maximum_bytes=authority['writers'][role]['maximum_bytes'],source_identity=identity)
