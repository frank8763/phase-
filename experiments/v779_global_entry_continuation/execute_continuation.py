"""One isolated global main and success-only exact repeat, finite immutable window."""
import datetime,fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
repo=Path(__file__).resolve().parents[2];entry=Path(__file__).parent;own=repo/'experiments/v778_global_retained_reentry';root=repo/'runs/v779_global_entry_continuation';outputs=repo/'runs/v778_global_retained_reentry';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
 p.parent.mkdir(exist_ok=True,parents=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n');tmp.replace(p)
freeze=read(entry/'CANDIDATE_FREEZE.json');fsha=sha(entry/'CANDIDATE_FREEZE.json')
def unchanged():
 assert sha(entry/'CANDIDATE_FREEZE.json')==fsha and all(sha(repo/n)==h for n,h in freeze['files'].items()),'FROZEN_SOURCE_CHANGED'
unchanged();assert (repo/'REVIEW_PENDING').exists();root.mkdir(exist_ok=False)
with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});guard=(repo/'REVIEW_PENDING').read_bytes();(root/'REVIEW_PENDING.before').write_bytes(guard)
window=root/'development01';window.mkdir();started=time.time();original_window=read(outputs/'ROUND_WINDOW.json');deadline=original_window['absolute_deadline_unix'];assert original_window['round_closed'] and original_window['attempted_navigation']==0;assert not read(outputs/'development01/COMPLETION.json')['records'];task=read(own/'PILOT_TASKS.json')[0];model=repo/'runs/v690_visible_eight_meter/training_8m/proposer.json';records=[];process=None
ledger=dict(started_unix=started,absolute_deadline_unix=deadline,limit_s=deadline-started,original_started_unix=original_window['started_unix'],original_absolute_deadline_unchanged=True,pid=os.getpid(),round_closed=False,attempted_navigation=0,training_updates=0,stage_access=0,real_robot=0,task=task)
dump(root/'ROUND_WINDOW.json',ledger);dump(window/'LOCKED_TASK_LIST.json',[task]);dump(window/'SOURCE_FREEZE.json',{p.name:sha(p)for p in own.glob('*.py')});dump(window/'DOCUMENT_FREEZE.json',{p.name:sha(p)for p in own.glob('*.md')})
env=os.environ.copy();env.update(PHASE_RECOVERY_ABLATION='FULL',PHASE_COURSE_DISTANCE=str(task['course_distance_m']),PHASE_FIELD_CASE=task['case_id'],PHASE_COURSE_PHASE=str(task['phase']),PHASE_PROPOSAL_MODEL=str(model))
def execute(script,args,log,cap):
 global process
 args=list(map(str,args))
 unchanged();assert time.time()+cap+3<deadline,'ABSOLUTE_BUDGET_INSUFFICIENT';dump(window/'ACTIVE.json',dict(script=script,args=args,started_unix=time.time(),cap_s=cap,deadline=deadline))
 with log.open('x')as stream:
  process=subprocess.Popen([str(repo/'run_phase.sh'),str(own.relative_to(repo)/script),*map(str,args)],cwd=repo,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
  try:return process.wait(timeout=min(cap,deadline-time.time()))
  finally:
   if process.poll()is None:
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=2)
    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
   process=None
status='RUNNING'
try:
 (repo/'REVIEW_PENDING').unlink()
 name='t0_slot01';pair=outputs/name/'paired';assert read(pair/'completion.json')['status']=='PREFLIGHT_COMPLETE','ORIGINAL_T0_NOT_COMPLETE'
 assert execute('audit_field_discovery.py',[pair,'--preflight','--output-dir',pair/'field_preflight'],window/'t0_audit.console',60)==0,'T0_CAUSAL_INDEPENDENT_AUDIT_FAILED'
 dump(window/'PREFLIGHTS.json',[dict(task=task,run=str(pair.relative_to(repo)))])
 assert execute('audit_field_preflight.py',[window],window/'noise_audit.console',45)==0,'T0_ORIGINAL_SENSOR_NOISE_FAILED'
 for name in ['main01','repeat01']:
  if name=='repeat01':assert records[0]['functional_passed'] and records[0]['physical_passed']
  pair=outputs/('v779_'+name)/'paired';record=dict(name=name,role='MAIN_DEVELOPMENT'if name=='main01'else'SUCCESS_CONDITIONAL_REPEAT',run=str(pair.relative_to(repo)),physical_passed=False,functional_passed=False,audits={});records.append(record);ledger['attempted_navigation']+=1;dump(root/'ROUND_WINDOW.json',ledger);dump(window/'RESULTS.json',records)
  code=execute('run_static.py',['--name','v779_'+name,'--seed',task['seed'],'--wall-seconds',900,'--max-steps',1200,'--initial-observation-steps',0],window/(name+'.console'),905);record['runner_exit']=code;record['result']=read(pair/'geometry_memory/result.json')if(pair/'geometry_memory/result.json').exists()else None;record['interrupted']=read(pair/'geometry_memory/interrupted.json')if(pair/'geometry_memory/interrupted.json').exists()else None;dump(window/'RESULTS.json',records)
  if record['result']is not None or(record['interrupted']or{}).get('public_steps',0)>0:
   record['replay_exit']=execute('replay_native_audit.py',[pair],pair/'replay.console',35);dump(window/'RESULTS.json',records)
  assert code==0 and record['result']is not None,'NAVIGATION_INCOMPLETE'
  for script,cap in [('audit_run.py',90),('audit_early_scan.py',60),('audit_route_commitment.py',60),('audit_projection_learning.py',60),('audit_all_tail_geometry.py',90),('audit_shadow_mode.py',40),('audit_reentry.py',180)]:
   args=[pair]
   if script=='audit_run.py':args+=['--window',window]
   if script=='audit_projection_learning.py':args+=['--model',model]
   code=execute(script,args,pair/(script+'.console'),cap);record['audits'][script]=code;dump(window/'RESULTS.json',records);assert code==0,script+'_FAILED'
  code=execute('audit_field_discovery.py',[pair,'--output-dir',pair/'discovery_audit'],pair/'discovery_audit.console',180);cp=pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json';assert cp.exists(),'DISCOVERY_AUDIT_CRASH';chain=read(cp);failed=[k for k,v in chain['checks'].items()if not v];record['functional_failed_checks']=failed;dump(window/'RESULTS.json',records)
  assert not(set(failed)-{'moving_before_discovery','new_causal_route_after_stop','actually_continued_after_replanning','strict_arrival'}),'CAUSAL_CHAIN_EVIDENCE_ANOMALY'
  assert(code==0)==(chain['status']=='PASS');record.update(physical_passed=True,functional_passed=bool(chain['status']=='PASS'and record['result']['strict_safe_arrival']));dump(window/'RESULTS.json',records)
  if not record['functional_passed']:status='GLOBAL_DEVELOPMENT_FUNCTIONAL_NOT_PASSED';break
  if name=='repeat01':
   import numpy as np
   from contact_fingerprint import compare_contacts
   base=outputs/'v779_main01/paired';aa=[json.loads(s)for s in(base/'geometry_memory/v648_execution.jsonl').read_text().splitlines()];bb=[json.loads(s)for s in(pair/'geometry_memory/v648_execution.jsonl').read_text().splitlines()];errors={k:float(np.max(abs(np.asarray([x[k]for x in aa])-np.asarray([x[k]for x in bb]))))if len(aa)==len(bb)else None for k in['qpos_full','qvel_full','ctrl','mocap_pos']};contact=compare_contacts(base,pair)
   checks=dict(state_ctrl=all(v is not None and v<=1e-8 for v in errors.values()),model=sha(base/'scene_model.mjb')==sha(pair/'scene_model.mjb'),initial=records[0]['result']['normalized_initial_state_hash']==record['result']['normalized_initial_state_hash'],contacts=contact['passed'],discovery=read(base/'geometry_memory/FIRST_DISCOVERY.json')==read(pair/'geometry_memory/FIRST_DISCOVERY.json'));dump(pair/'EXACT_REPEAT_AUDIT.json',dict(checks=checks,errors=errors,passed=all(checks.values())));assert all(checks.values()),'EXACT_REPEAT_ANOMALY';status='GLOBAL_SINGLE_TASK_MAIN_AND_REPEAT_PASSED'
 unchanged()
except BaseException as e:
 status='STOPPED_EXCEPTION';dump(window/'ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
finally:
 (repo/'REVIEW_PENDING').write_bytes(guard);ledger.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump(root/'ROUND_WINDOW.json',ledger);dump(window/'COMPLETION.json',dict(status=status,records=records,automatic_additional_navigation=False));dump(window/'ACTIVE.json',dict(status=status,completed=True))
print(json.dumps(dict(status=status,results=len(records))))
