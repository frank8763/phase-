"""Host controller for a single finite C0 curriculum window."""
import os,sys,time,signal,subprocess,fcntl,json,hashlib,traceback
from pathlib import Path
src=Path(__file__).resolve().parent;repo=src.parents[1];root=repo/'runs/v687_control_curriculum';root.mkdir(exist_ok=True)
lock=(root/'window.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});window=root/'development01_retry02';window.mkdir()
started=time.time();original=json.loads((root/'ROUND_WINDOW.json').read_text());deadline=original['absolute_deadline_unix'];assert original['round_closed'] and original['status']=='STOPPED_EXCEPTION'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
paths=[*src.glob('*.py'),*src.glob('*.md'),*(repo/'experiments/v680_dynamic_later_stop_reserve').glob('*.py'),repo/'runs/v686_dynamic_open_curriculum/open01/paired/geometry_memory/planning_0032.json']
freeze={str(p.relative_to(repo)):sha(p)for p in paths};dump(window/'SOURCE_FREEZE.json',freeze)
ledger={'started_unix':started,'absolute_deadline_unix':deadline,'limit_s':2400,'round_closed':False,'pid':os.getpid(),'navigation_attempts':0,'repeat_attempts':0,'original_driver_and_failure_preserved':True,'original_fixture_native_steps':0,'original_fixture_private_steps':0,'original_started_unix':original['started_unix'],'algorithm_revisions':0,'training_updates':0,'dynamic_obstacles':0,'stage_access':0,'single_cpu_sequential':True}
dump(root/'RECOVERY_LEDGER.json',ledger)
def execute(args,log,cap):
 assert time.time()+cap+3<deadline,'NO_WINDOW_RENEWAL'
 assert all(sha(repo/k)==v for k,v in freeze.items()),'FROZEN_INPUT_CHANGED'
 dump(window/'ACTIVE.json',{'command':args,'started_unix':time.time()})
 with log.open('w')as f:
  child=subprocess.Popen([str(repo/'run_phase.sh'),*args],cwd=repo,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:return child.wait(timeout=cap)
  except BaseException:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=2)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
   raise
results=[];status='RUNNING'
def run(course,name,steps):
 ledger['navigation_attempts']+=1;dump(root/'RECOVERY_LEDGER.json',ledger)
 code=execute([str(src.relative_to(repo)/'run_course_retry02.py'),'--course',course,'--name',name,'--max-steps',str(steps)],window/(name+'.console'),455)
 pair=root/name/'paired';completion=read(pair/'completion.json')
 results.append({'course':course,'name':name,'run':str(pair.relative_to(repo)),'result':completion.get('result'),'runner_code':code});dump(window/'RESULTS.json',results)
 assert code==0 and completion['status']=='COMPLETE','COURSE_RUNNER_FAILED'
 code=execute([str(src.relative_to(repo)/'replay_and_audit.py'),str(pair),'--window',str(window)],pair/'audit.console',50)
 results[-1]['audit']=read(pair/'C0_AUDIT.json');dump(window/'RESULTS.json',results)
 assert code==0 and results[-1]['audit']['status']=='ALL_C0_AUDITS_PASS','COURSE_PHYSICAL_AUDIT_FAILED'
 # The common helper is zero-integration; hashes are captured separately here.
 helper=repo/'experiments/v649_static_stability/audit_later_stop_certificate_geometry.py'
 dump(pair/'TAIL_AUDITOR_SOURCE.json',{'path':str(helper.relative_to(repo)),'sha256':sha(helper)})
 assert execute([str(helper.relative_to(repo)),str(pair)],pair/'tail_audit.console',35)==0,'TAIL_GEOMETRY_FAILED'
 results[-1]['tail_audit']=read(pair/'SAVED_TAIL_GEOMETRY_AUDIT.json');dump(window/'RESULTS.json',results)
 return pair
try:
 for course,steps in [('straight',400),('turn',500),('bypass',600)]:run(course,course+'01_retry02',steps)
 if all(x['result']['strict_safe_arrival']for x in results):
  ledger['repeat_attempts']=1;dump(root/'RECOVERY_LEDGER.json',ledger);pair=run('bypass','bypass01_repeat_retry02',600)
  import numpy as np
  sys.path.insert(0,str(repo/'experiments/v680_dynamic_later_stop_reserve'));from contact_fingerprint import compare_contacts
  base=root/'bypass01_retry02/paired'
  a=[json.loads(s)for s in(base/'geometry_memory/v648_execution.jsonl').read_text().splitlines()];b=[json.loads(s)for s in(pair/'geometry_memory/v648_execution.jsonl').read_text().splitlines()]
  errors={k:float(np.max(abs(np.asarray([x[k]for x in a])-np.asarray([x[k]for x in b]))))if len(a)==len(b)else None for k in ['qpos_full','qvel_full','ctrl']}
  contacts=compare_contacts(base,pair);repeat={'errors':errors,'same_model':sha(base/'scene_model.mjb')==sha(pair/'scene_model.mjb'),'contact_comparison':contacts,'not_independent':True};dump(window/'REPEAT_AUDIT.json',repeat)
  assert results[-1]['result']['strict_safe_arrival']and repeat['same_model']and contacts['passed']and all(v is not None and v<=1e-8 for v in errors.values()),'COMPLETE_REPEAT_FAILED'
  status='THREE_C0_ROUTES_AND_FULL_REPEAT_PASS'
 else:status='CLOSED_C0_ROUTE_NON_ARRIVAL'
except BaseException as e:
 status='STOPPED_EXCEPTION';dump(window/'ERROR.json',{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()})
finally:
 ledger.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump(root/'RECOVERY_LEDGER.json',ledger)
 dump(window/'COMPLETION.json',{'status':status,'round_closed':True,'results':results,'elapsed_s':time.time()-started,'dynamic_success':False,'training_updates':0,'automatic_additional_simulation':False})
 dump(window/'ACTIVE.json',{'status':status,'completed':True});print(status,flush=True)
