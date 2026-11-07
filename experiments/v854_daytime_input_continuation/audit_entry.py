"""Actual original auditor callsite: saved-only guards or one bounded real MJB metadata read."""
import argparse,ast,builtins,hashlib,importlib.abc,io,json,os,sys,time,types
from pathlib import Path
from common import R,C,W,read,sha
from registration import transform,ANCHORS
ap=argparse.ArgumentParser();ap.add_argument('--write-root',type=Path,required=True);ap.add_argument('--model-deadline',type=float);ap.add_argument('--metadata-proxy',action='store_true');ap.add_argument('script');ap.add_argument('arguments',nargs=argparse.REMAINDER);a=ap.parse_args()
assert a.script.endswith('.py')and'/'not in a.script
allowed=a.write_root.resolve();assert allowed.is_relative_to(R/'runs')
for path in [R/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1',R/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1',W]:sys.path.insert(0,str(path))
os.environ['PHASE_REPO']=str(R);model_reads=[]
if a.script=='audit_run.py'and not a.metadata_proxy:
 assert a.model_deadline is not None and time.time()+5<a.model_deadline
 import mujoco
 real_load=mujoco.MjModel.from_binary_path
 def metadata(path):
  assert time.time()+2<a.model_deadline
  started=time.time();model=real_load(path);assert time.time()<a.model_deadline
  model_reads.append(dict(path=str(path),sha256=sha(path),started_unix=started,completed_unix=time.time(),actuator_ctrlrange=model.actuator_ctrlrange.tolist()))
  print(json.dumps(dict(event='ACTUAL_MJB_METADATA_READ',**model_reads[-1])),flush=True);return model
 mujoco.MjModel=types.SimpleNamespace(from_binary_path=metadata)
 def denied(*args,**kwargs):raise RuntimeError('AUDITOR_INTEGRATION_FORBIDDEN')
 mujoco.mj_step=mujoco.mj_step1=mujoco.mj_step2=denied
else:
 class NoModels(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name=='mujoco'or name.startswith('mujoco.'):raise RuntimeError('SAVED_AUDITOR_FORBIDS_MODELS')
 sys.meta_path.insert(0,NoModels())
 if a.metadata_proxy:
  assert a.script=='audit_run.py'
  import numpy as np
  pair=Path(a.arguments[0]);contract=read(pair/'geometry_memory/ACTUATOR_COMMAND_CONTRACT.json')
  def saved_metadata(path):
   assert Path(path)==pair/'scene_model.mjb';ranges=np.zeros((max(contract['ids'])+1,2));ranges[contract['ids']]=contract['limits'];return types.SimpleNamespace(actuator_ctrlrange=ranges)
  module=types.ModuleType('mujoco');module.MjModel=types.SimpleNamespace(from_binary_path=saved_metadata);sys.modules['mujoco']=module
real_open=builtins.open;real_io_open=io.open
def guarded(original,path,mode='r',*args,**kwargs):
 if isinstance(path,(str,bytes,os.PathLike))and any(c in mode for c in 'wax+'):
  assert Path(path).resolve().is_relative_to(allowed),'AUDITOR_ATTEMPTED_INPUT_WRITE'
 return original(path,mode,*args,**kwargs)
builtins.open=lambda path,mode='r',*args,**kwargs:guarded(real_open,path,mode,*args,**kwargs)
io.open=lambda path,mode='r',*args,**kwargs:guarded(real_io_open,path,mode,*args,**kwargs)
cache={};hashes={};calls=0
def cached_early_lines(path):
 global calls
 calls+=1;path=Path(path)
 if path not in cache:
  raw=path.read_bytes();hashes[path]=hashlib.sha256(raw).hexdigest();cache[path]=[json.loads(s)for s in raw.decode().splitlines()]
 return cache[path]
script=W/a.script;original=script.read_text();source,patches=transform(a.script,original);sys.argv=[str(script),*a.arguments];started=time.monotonic();passed=False
try:
 exec(compile(source,str(script),'exec'),dict(__name__='__main__',__file__=str(script),cached_early_lines=cached_early_lines,REGISTERED_TASKS_PATH=C/'REGISTERED_TASKS.json',REGISTERED_PREFIX_ANCHORS=ANCHORS))
 passed=True
finally:
 assert sha(script)==hashlib.sha256(original.encode()).hexdigest();assert all(sha(path)==h for path,h in hashes.items()),'CACHED_EVIDENCE_CHANGED'
 record=dict(script=a.script,passed=passed,elapsed_s=time.monotonic()-started,original_auditor_sha256=sha(script),patches=[before for before,_ in patches],original_assertions_preserved=True,metadata_proxy_import_only=a.metadata_proxy,actual_model_metadata_reads=model_reads,integrations=0,cache_calls=calls,full_log_parses=len(cache))
 (allowed/(a.script+'.execution.json')).write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(dict(event='AUDITOR_COMPLETED',**record)),flush=True)
