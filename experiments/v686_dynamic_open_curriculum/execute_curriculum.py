"""Bounded host orchestration. Every physical child uses the isolated entry."""
import os,json,time,subprocess,signal,hashlib,traceback,fcntl
from pathlib import Path
src=Path(__file__).resolve().parent;repo=src.parents[1];root=repo/'runs/v686_dynamic_open_curriculum'
root.mkdir(exist_ok=True);lock=(root/'window.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
window=root/'development01';window.mkdir();started=time.time();deadline=started+1800
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def read(p):return json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sources={p.name:sha(p) for p in src.glob('*.py')};docs={p.name:sha(p)for p in src.glob('*.md')}
dump(window/'SOURCE_FREEZE.json',sources);dump(window/'DOCUMENT_FREEZE.json',docs)
ledger={'started_unix':started,'absolute_deadline_unix':deadline,'limit_s':1800,'pid':os.getpid(),'round_closed':False,'navigation_attempts':0,'conditional_repeats':0,'preflight_attempts':0,'training_updates':0,'new_geometry_tasks':1,'independent_confirmation':0,'single_cpu_sequential':True}
dump(root/'ROUND_WINDOW.json',ledger)
def execute(args,log,cap):
 assert time.time()+cap+3<deadline,'WINDOW_BUDGET'
 assert all(sha(src/n)==h for n,h in {**sources,**docs}.items()),'SOURCE_CHANGED'
 dump(window/'ACTIVE.json',{'command':args,'started_unix':time.time()})
 with log.open('w')as f:
  child=subprocess.Popen([str(repo/'run_phase.sh'),*args],cwd=repo,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:return child.wait(timeout=cap)
  except BaseException:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=2)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
   raise
def run(name,preflight=False):
 if preflight:ledger['preflight_attempts']+=1
 else:ledger['navigation_attempts']+=1
 dump(root/'ROUND_WINDOW.json',ledger)
 args=[str(src.relative_to(repo)/'run_static.py'),'--name',name,'--seed','95000011','--max-steps','600','--wall-seconds',str(45 if preflight else 600),'--initial-observation-steps','32']
 if preflight:args.append('--feasibility-only')
 code=execute(args,window/(name+'.console'),50 if preflight else 605);pair=root/name/'paired'
 assert code==0,'CHILD_FAILED_'+name
 return pair
def audit(pair):
 assert execute([str(src.relative_to(repo)/'replay_native_audit.py'),str(pair)],pair/'native_replay.console',35)==0,'REPLAY'
 assert execute([str(src.relative_to(repo)/'audit_run.py'),str(pair),'--window',str(window)],pair/'independent.console',45)==0,'INDEPENDENT_AUDIT'
 assert execute([str(src.relative_to(repo)/'layer_metrics.py'),str(pair)],pair/'layer_metrics.console',35)==0,'LAYER_METRICS'
 return read(pair/'geometry_memory/result.json')
results=[];status='RUNNING'
try:
 pair=run('preflight01',True)
 assert read(pair/'TASK_FEASIBILITY.json')['eligible'],'SCENE_PREFLIGHT_FAILED'
 pair=run('open01');r=audit(pair);results.append({'pair':str(pair.relative_to(repo)),'result':r})
 if not r['strict_safe_arrival']:status='CLOSED_OPEN_ARENA_NON_ARRIVAL'
 else:
  ledger['conditional_repeats']=1;dump(root/'ROUND_WINDOW.json',ledger)
  again=run('open01_repeat');r2=audit(again);results.append({'pair':str(again.relative_to(repo)),'result':r2})
  # Full recorded state/control equality; raw contact-path differences are not erased.
  a=[json.loads(s)for s in(pair/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
  b=[json.loads(s)for s in(again/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
  import numpy as np
  errors={k:float(np.max(abs(np.asarray([x[k]for x in a])-np.asarray([x[k]for x in b]))))if len(a)==len(b)else None for k in ['qpos_full','qvel_full','ctrl','mocap_pos']}
  dump(window/'REPEAT_AUDIT.json',{'errors':errors,'same_model':sha(pair/'scene_model.mjb')==sha(again/'scene_model.mjb'),'repeat_is_not_independent':True})
  assert r2['strict_safe_arrival'] and all(v is not None and v<=1e-8 for v in errors.values()),'REPEAT_FAILED'
  status='SAME_OPEN_DEVELOPMENT_ARRIVAL_REPEAT'
except BaseException as e:
 status='STOPPED_EXCEPTION';dump(window/'ERROR.json',{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()})
finally:
 ledger.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump(root/'ROUND_WINDOW.json',ledger)
 dump(window/'RESULTS.json',results);dump(window/'COMPLETION.json',{'status':status,'round_closed':True,'elapsed_s':time.time()-started,'results':results,'dynamic_stability_acceptance':False,'training_updates':0,'automatic_additional_simulation':False})
 dump(window/'ACTIVE.json',{'status':status,'completed':True});print(status,flush=True)
