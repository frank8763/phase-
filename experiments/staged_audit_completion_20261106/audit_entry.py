"""Read-only original auditors, with one immutable JSONL parse cache only."""
import argparse, ast, builtins, gzip, hashlib, importlib.abc, io, json, os, runpy, sys, time
from pathlib import Path

R=Path(__file__).resolve().parents[2]
W=R/'experiments/v842_staged_long_navigation'
ap=argparse.ArgumentParser();ap.add_argument('--write-root',required=True);ap.add_argument('--model-deadline',type=float);ap.add_argument('script');ap.add_argument('arguments',nargs=argparse.REMAINDER);a=ap.parse_args()
assert a.script.endswith('.py') and '/' not in a.script
allowed=Path(a.write_root).resolve();assert allowed.is_relative_to(R/'runs')
for p in [R/'runtime/mk-mini/experiments/phase_rpccr_p0b76_online_gate_v1',R/'runtime/mk-mini/experiments/phase_rpccr_p0b68_v1',W]:sys.path.insert(0,str(p))
os.environ['PHASE_REPO']=str(R)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
model_reads=[]
if a.script=='audit_run.py':
 assert a.model_deadline is not None and time.time()+5<a.model_deadline
 import mujoco,types
 real_load=mujoco.MjModel.from_binary_path
 def metadata(path):
  assert time.time()+2<a.model_deadline,'MODEL_METADATA_DEADLINE'
  start=time.time();result=real_load(path)
  assert time.time()<a.model_deadline,'MODEL_METADATA_DEADLINE'
  model_reads.append(dict(path=str(path),sha256=sha(path),started_unix=start,completed_unix=time.time(),actuator_ctrlrange=result.actuator_ctrlrange.tolist()))
  print(json.dumps(dict(event='ACTUAL_MJB_METADATA_READ',**model_reads[-1])),flush=True)
  return result
 mujoco.MjModel=types.SimpleNamespace(from_binary_path=metadata)
 def denied(*args,**kwargs):raise RuntimeError('AUDITOR_INTEGRATION_FORBIDDEN')
 mujoco.mj_step=mujoco.mj_step1=mujoco.mj_step2=denied
else:
 class NoModels(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name=='mujoco' or name.startswith('mujoco.'):raise RuntimeError('SAVED_AUDITOR_FORBIDS_MODELS')
 sys.meta_path.insert(0,NoModels())

# Every output is new. Input links resolve outside allowed and cannot be written.
real_open=builtins.open;real_io_open=io.open
def guarded_open(original,path,mode='r',*args,**kwargs):
 if isinstance(path,(str,bytes,os.PathLike)) and any(c in mode for c in 'wax+'):
  assert Path(path).resolve().is_relative_to(allowed),'AUDITOR_ATTEMPTED_RAW_EVIDENCE_WRITE'
 return original(path,mode,*args,**kwargs)
builtins.open=lambda path,mode='r',*args,**kwargs:guarded_open(real_open,path,mode,*args,**kwargs)
io.open=lambda path,mode='r',*args,**kwargs:guarded_open(real_io_open,path,mode,*args,**kwargs)
script=W/a.script;source=script.read_text();original=source;cache={};cache_hash={};cache_calls=0
def cached_early_lines(path):
 global cache_calls
 cache_calls+=1;path=Path(path)
 if path not in cache:
  raw=path.read_bytes();cache_hash[path]=hashlib.sha256(raw).hexdigest();cache[path]=[json.loads(s)for s in raw.decode().splitlines()]
 return cache[path]
if a.script=='audit_run.py':
 before="event=next(e for e in lines(cell/'early_joint_decisions.jsonl')if e['step']==step)"
 after="event=next(e for e in cached_early_lines(cell/'early_joint_decisions.jsonl')if e['step']==step)"
 assert source.count(before)==1
 source=source.replace(before,after)
 assert source.replace(after,before)==original
 assert sum(isinstance(n,ast.Assert)for n in ast.walk(ast.parse(original)))==sum(isinstance(n,ast.Assert)for n in ast.walk(ast.parse(source)))
sys.argv=[str(script),*a.arguments];started=time.monotonic();ok=False
try:
 exec(compile(source,str(script),'exec'),dict(__name__='__main__',__file__=str(script),cached_early_lines=cached_early_lines))
 ok=True
finally:
 assert sha(script)==hashlib.sha256(original.encode()).hexdigest()
 assert all(sha(p)==h for p,h in cache_hash.items()),'IMMUTABLE_LOG_CHANGED'
 record=dict(script=a.script,passed=ok,elapsed_s=time.monotonic()-started,original_auditor_sha256=sha(script),cache_calls=cache_calls,full_early_log_parses=len(cache),cached_inputs={str(p):h for p,h in cache_hash.items()},actual_model_metadata_reads=model_reads,integrations=0,all_original_assertions_preserved=True)
 (allowed/(a.script+'.execution.json')).write_text(json.dumps(record,indent=2)+'\n')
 print(json.dumps(dict(event='AUDITOR_COMPLETED',**{k:v for k,v in record.items()if k not in ['actual_model_metadata_reads','cached_inputs']})),flush=True)
