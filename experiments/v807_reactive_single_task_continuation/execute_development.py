"""Frozen three-route sequential global development. No source/fixture retries."""
import datetime,fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/v807_reactive_single_task_continuation';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
 p.parent.mkdir(exist_ok=True,parents=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n');tmp.replace(p)
freeze=read(own/'CANDIDATE_FREEZE.json');fsha=sha(own/'CANDIDATE_FREEZE.json')
def unchanged():assert sha(own/'CANDIDATE_FREEZE.json')==fsha and all(sha(repo/n)==h for n,h in freeze['files'].items()),'FROZEN_SOURCE_CHANGED'
unchanged();assert(repo/'REVIEW_PENDING').exists();assert read(root/'pre_navigation/RESULT.json')['status']=='REACTIVE_ZERO_MODEL_QUALIFICATION_PASS';assert not(root/'ROUND_WINDOW.json').exists()
with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
master_lock=(root/'window.lock').open('a+');fcntl.flock(master_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
guard=(repo/'REVIEW_PENDING').read_bytes();(root/'REVIEW_PENDING.before').write_bytes(guard);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
day=read(repo/'RPCCR_SENSOR_ACTIVATED_LEDGER_20261104.json');assert day['candidate_versions']==1 and day['nav_started']==0;authorization=read(repo/'RPCCR_SENSOR_ACTIVATED_AUTHORIZATION_20261104.json')
started=time.time();deadline=min(started+7200,authorization['absolute_deadline_unix']);assert deadline-started>=6000,'INSUFFICIENT_GLOBAL_BUDGET';tasks=read(own/'DEVELOPMENT_TASKS.json');window=root/'development01';window.mkdir(exist_ok=False);records=[];preflights=[];process=None
ledger=dict(started_unix=started,absolute_deadline_unix=deadline,limit_s=deadline-started,pid=os.getpid(),round_closed=False,attempted_navigation=0,training_updates=0,stage_access=0,real_robot=0,tasks=tasks)
dump(root/'ROUND_WINDOW.json',ledger);dump(window/'LOCKED_TASK_LIST.json',tasks);dump(window/'SOURCE_FREEZE.json',{p.name:sha(p)for p in own.glob('*.py')});dump(window/'DOCUMENT_FREEZE.json',{p.name:sha(p)for p in own.glob('*.md')})
model=repo/'runs/v690_visible_eight_meter/training_8m/proposer.json';env=os.environ.copy();env.update(PHASE_RECOVERY_ABLATION='FULL',PHASE_PROPOSAL_MODEL=str(model))
def execute(script,args,log,cap):
 global process
 args=list(map(str,args));unchanged();assert time.time()+cap+3<deadline,'ABSOLUTE_BUDGET_INSUFFICIENT';dump(window/'ACTIVE.json',dict(script=script,args=args,started_unix=time.time(),cap_s=cap,deadline=deadline))
 with log.open('x')as stream:
  process=subprocess.Popen([str(repo/'run_phase.sh'),str(own.relative_to(repo)/script),*args],cwd=repo,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
  try:return process.wait(timeout=min(cap,deadline-time.time()))
  finally:
   if process.poll()is None:
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=2)
    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
   process=None
def set_task(t):env.update(PHASE_COURSE_DISTANCE=str(t['course_distance_m']),PHASE_FIELD_CASE=t['case_id'],PHASE_COURSE_PHASE=str(t['phase']))
def exact_repeat(base,pair,base_record,record):
 import numpy as np
 sys.path.insert(0,str(own));from contact_fingerprint import compare_contacts
 aa=[json.loads(s)for s in(base/'geometry_memory/v648_execution.jsonl').read_text().splitlines()];bb=[json.loads(s)for s in(pair/'geometry_memory/v648_execution.jsonl').read_text().splitlines()];errors={k:float(np.max(abs(np.asarray([x[k]for x in aa])-np.asarray([x[k]for x in bb]))))if len(aa)==len(bb)else None for k in['qpos_full','qvel_full','ctrl','mocap_pos']};contact=compare_contacts(base,pair)
 checks=dict(state_ctrl=all(v is not None and v<=1e-8 for v in errors.values()),model=sha(base/'scene_model.mjb')==sha(pair/'scene_model.mjb'),initial=base_record['result']['normalized_initial_state_hash']==record['result']['normalized_initial_state_hash'],contacts=contact['passed'],discovery=read(base/'geometry_memory/FIRST_DISCOVERY.json')==read(pair/'geometry_memory/FIRST_DISCOVERY.json'));dump(pair/'EXACT_REPEAT_AUDIT.json',dict(checks=checks,errors=errors,passed=all(checks.values())));assert all(checks.values()),'EXACT_REPEAT_ANOMALY'
status='RUNNING'
signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(TimeoutError('V806_OUTER_TERMINATED')))
try:
 (repo/'REVIEW_PENDING').unlink()
 # Reuse the unchanged zero-integration t0; never repeat initialization.
 preflights=read(repo/'runs/v806_sensor_activated_dynamic/development01/PREFLIGHTS.json')
 assert [x['task']for x in preflights]==tasks
 dump(window/'PREFLIGHTS.json',preflights)
 assert execute('audit_field_preflight.py',[window],window/'noise_audit.console',60)==0,'T0_SENSOR_NOISE_FAILED'
 for role in ['MAIN_DEVELOPMENT','SUCCESS_CONDITIONAL_REPEAT']:
  for t in tasks:
   set_task(t);name=('main'if role=='MAIN_DEVELOPMENT'else'repeat')+f"_slot{t['slot']:02d}";pair=root/name/'paired';record=dict(name=name,task=t,role=role,run=str(pair.relative_to(repo)),physical_passed=False,functional_passed=False,audits={});records.append(record);ledger['attempted_navigation']+=1;dump(root/'ROUND_WINDOW.json',ledger);dump(window/'RESULTS.json',records)
   code=execute('run_static.py',['--name',name,'--seed',t['seed'],'--wall-seconds',1500,'--max-steps',1200,'--initial-observation-steps',0],window/(name+'.console'),1505);record['runner_exit']=code;record['result']=read(pair/'geometry_memory/result.json')if(pair/'geometry_memory/result.json').exists()else None;record['interrupted']=read(pair/'geometry_memory/interrupted.json')if(pair/'geometry_memory/interrupted.json').exists()else None;dump(window/'RESULTS.json',records)
   if record['result']is not None or(record['interrupted']or{}).get('public_steps',0)>0:record['replay_exit']=execute('replay_native_audit.py',[pair],pair/'replay.console',60);dump(window/'RESULTS.json',records)
   assert code==0 and record['result']is not None,'NAVIGATION_INCOMPLETE'
   for script,cap in [('audit_run.py',120),('audit_forward_controller.py',60),('audit_route_commitment.py',60),('audit_projection_learning.py',60),('audit_all_tail_geometry.py',150),('audit_shadow_mode.py',60),('audit_reentry.py',240),('audit_complete_joint.py',60),('audit_nominal_layers.py',240),('audit_reactive.py',300)]:
    args=[pair]
    if script=='audit_run.py':args+=['--window',window]
    if script=='audit_projection_learning.py':args+=['--model',model]
    code=execute(script,args,pair/(script+'.console'),cap);record['audits'][script]=code;dump(window/'RESULTS.json',records);assert code==0,script+'_FAILED'
   code=execute('audit_field_discovery.py',[pair,'--output-dir',pair/'discovery_audit'],pair/'discovery_audit.console',240);cp=pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json';assert cp.exists(),'DISCOVERY_AUDIT_CRASH';chain=read(cp);failed=[k for k,v in chain['checks'].items()if not v];record['functional_failed_checks']=failed
   assert not(set(failed)-{'moving_before_discovery','new_causal_route_after_stop','actually_continued_after_replanning','strict_arrival'}),'CAUSAL_EVIDENCE_ANOMALY';assert(code==0)==(chain['status']=='PASS');record.update(physical_passed=True,functional_passed=bool(chain['status']=='PASS'and record['result']['strict_safe_arrival']));dump(window/'RESULTS.json',records)
   if not record['functional_passed']:status='GLOBAL_DEVELOPMENT_FUNCTIONAL_NOT_PASSED';raise StopIteration('FUNCTIONAL_NOT_PASSED_NO_MORE_TASKS')
   if role=='SUCCESS_CONDITIONAL_REPEAT':
    base_record=next(x for x in records if x['role']=='MAIN_DEVELOPMENT'and x['task']['slot']==t['slot']);exact_repeat(repo/base_record['run'],pair,base_record,record)
 status='ONE_REACTIVE_MAIN_AND_REPEAT_PASSED';unchanged()
except StopIteration:pass
except BaseException as e:status='STOPPED_EXCEPTION';dump(window/'ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
finally:
 (repo/'REVIEW_PENDING').write_bytes(guard);ledger.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump(root/'ROUND_WINDOW.json',ledger);dump(window/'COMPLETION.json',dict(status=status,records=records,automatic_additional_navigation=False));dump(window/'ACTIVE.json',dict(status=status,completed=True))
print(json.dumps(dict(status=status,records=len(records))))
