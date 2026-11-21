"""Pure source identities and immutable original guard for one bounded owner."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import types
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def put(p,v):
 p=Path(p);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');t.replace(p)
def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def guard(output):
 source=R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py'
 code=compile(source.read_text(),str(source),'exec',dont_inherit=True)
 function=next(x for x in code.co_consts if isinstance(x,types.CodeType)and x.co_name=='write_guard')
 original=types.FunctionType(function,dict(Path=Path,os=os,OUT=output),'write_guard')
 binding=exact('v1492_immutable_original_guard',R/'experiments/v1447_full_module_guard_identity/guard_binding.py')
 sys.addaudithook(binding.bind_function(original,output))
 return dict(original_source_sha256=sha(source),immutable_original_guard=True)

def manifest():
 values=read(R/'runs/v1485_priest_current_polynomial_seam/SOURCE_FREEZE.json')['files'].copy()
 for folder in [C,R/'experiments/v1487_priest_optimizer_contract']:
  for p in folder.iterdir():
   if p.is_file():values[str(p.relative_to(R))]=sha(p)
 values['runs/v1491_priest_dependency_target/EXTRACTED_INDEX.json']=sha(R/'runs/v1491_priest_dependency_target/EXTRACTED_INDEX.json')
 for row in read(R/'runs/v1491_priest_dependency_target/EXTRACTED_INDEX.json')['files']:values[row['path']]=row['sha256']
 for n in ['runs/v1490_priest_dependency_recovery/FULL_REMOTE_VERIFIED.json','runs/v1491_priest_dependency_target/COMPLETION.json','experiments/v1436_pathlib_control_rename/bounded_io.py','experiments/v1436_pathlib_control_rename/writer_budget.py']:values[n]=sha(R/n)
 assert all(sha(R/n)==h for n,h in values.items()),'WORKER_SOURCE_OR_DEPENDENCY_CHANGED'
 return values

def validate_authority(authority,*,mode,source_manifest_sha256,now_unix,now_monotonic,boot_id):
 assert authority['mode']==mode and mode in {'IO_TARGET','OPTIMIZER'}
 assert authority['models_authorized']is False and authority['boot_id']==boot_id,'WORKER_SCOPE_BOOT_OR_MODEL_AUTHORITY'
 assert authority['source_manifest_sha256']==source_manifest_sha256,'WORKER_SOURCE_MANIFEST_CHANGED'
 assert now_unix<authority['absolute_deadline_unix']<=1795395600 and now_monotonic<authority['hard_stop_monotonic'],'WORKER_CLOCK_OR_ROOT_EXPIRED'
 if mode=='OPTIMIZER':assert authority['scope']=='PRIEST_OPTIMIZER_ONLY'
 return True
