"""Five prelocked no-actor full-path navigation rounds, sequential and bounded."""
import datetime,fcntl,hashlib,json,os,signal,subprocess,time,traceback
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/v805_static_five_continuation';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n');tmp.replace(p)
assert(repo/'REVIEW_PENDING').exists()and not(root/'ROUND_WINDOW.json').exists();root.mkdir(exist_ok=True)
freeze=read(own/'CANDIDATE_FREEZE.json');fsha=sha(own/'CANDIDATE_FREEZE.json')
def unchanged():assert sha(own/'CANDIDATE_FREEZE.json')==fsha and all(sha(repo/p)==h for p,h in freeze['files'].items()),'FROZEN_SOURCE_CHANGED'
unchanged()
with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
guard=(repo/'REVIEW_PENDING').read_bytes();(root/'REVIEW_PENDING.before').write_bytes(guard);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
auth=read(repo/'RPCCR_NO_DYNAMIC_FIVE_AUTHORIZATION_20261104.json');start=time.time();deadline=auth['absolute_deadline_unix'];assert deadline-start>8000;tasks=read(own/'TASKS.json');assert len(tasks)==5;records=[];process=None;status='RUNNING'
window=root/'five01';window.mkdir();ledger=dict(started_unix=start,absolute_deadline_unix=deadline,pid=os.getpid(),round_closed=False,tasks=tasks,training_updates=0,stage_access=0,real_robot=0)
dump(root/'ROUND_WINDOW.json',ledger);dump(window/'LOCKED_TASKS.json',tasks);dump(window/'SOURCE_FREEZE.json',{p.name:sha(p)for p in own.glob('*.py')});dump(window/'DOCUMENT_FREEZE.json',{p.name:sha(p)for p in own.glob('*.md')});env=os.environ.copy();model=repo/'runs/v690_visible_eight_meter/training_8m/proposer.json';env.update(PHASE_PROPOSAL_MODEL=str(model),PHASE_RECOVERY_ABLATION='FULL',PHASE_FIELD_CASE='WEST_EAST',PHASE_COURSE_DISTANCE='8.0',PHASE_COURSE_PHASE='0.0')
def execute(script,args,log,cap):
 global process
 unchanged();assert time.time()+cap+3<deadline,'INSUFFICIENT_ABSOLUTE_BUDGET';dump(window/'ACTIVE.json',dict(script=script,args=list(map(str,args)),started_unix=time.time(),cap_s=cap,deadline=deadline))
 with log.open('x')as stream:
  process=subprocess.Popen([str(repo/'run_phase.sh'),str(own.relative_to(repo)/script),*map(str,args)],cwd=repo,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
  try:return process.wait(timeout=min(cap,deadline-time.time()))
  finally:
   if process.poll()is None:
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=2)
    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
   process=None
signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(TimeoutError('FIVE_OUTER_TERMINATED')))
try:
 (repo/'REVIEW_PENDING').unlink()
 # Revalidate the already executed first round without re-running its physics.
 prior=read(repo/'runs/v804_no_dynamic_static_contact/five01/RESULTS.json')[0]
 first=dict(prior);first['audits']={};first['is_prior_physical_navigation']=True;first['original_failed_audit_preserved']='runs/v804_no_dynamic_static_contact/five01/ERROR.json';first['audit_pair']='runs/v805_static_five_continuation/prior_round01_audit_view/paired';records.append(first)
 assert first['result']['strict_safe_arrival'] and first['static_audit']['status']=='PASS' and first['replay_exit']==0
 view=repo/first['audit_pair']
 for script,cap in [('audit_forward_controller.py',60),('audit_route_commitment.py',60),('audit_projection_learning.py',60),('audit_all_tail_geometry.py',120),('audit_shadow_mode.py',60),('audit_reentry.py',120),('audit_complete_joint.py',60),('audit_nominal_layers.py',180)]:
  args=[view]
  if script=='audit_projection_learning.py':args+=['--model',model]
  first['audits'][script]=execute(script,args,window/('prior01_'+script+'.console'),cap);dump(window/'RESULTS.json',records);assert first['audits'][script]==0,'PRIOR_SAVED_'+script+'_FAILED'
 links=read(root/'PRIOR_VIEW_INPUTS.json');assert all(sha(repo/x['source'])==sha(repo/x['view'])==x['sha256']for x in links),'PRIOR_SOURCE_OR_VIEW_CHANGED'
 first['strict_success']=True;dump(window/'PRIOR_SAVED_AUDIT.json',dict(status='PASS',original_error_and_closed_window_preserved=True,original_source_and_view_SHA_exact=True,new_integrations=0));dump(window/'RESULTS.json',records)
 for task in tasks[1:]:
  name=f"round{task['slot']:02d}";pair=root/name/'paired';row=dict(name=name,task=task,run=str(pair.relative_to(repo)),audits={},result=None);records.append(row);dump(window/'RESULTS.json',records)
  code=execute('run_static.py',['--name',name,'--seed',task['seed'],'--wall-seconds',1500,'--max-steps',1200,'--initial-observation-steps',0],window/(name+'.console'),1505);row['runner_exit']=code;row['result']=read(pair/'geometry_memory/result.json')if(pair/'geometry_memory/result.json').exists()else None;row['interrupted']=read(pair/'geometry_memory/interrupted.json')if(pair/'geometry_memory/interrupted.json').exists()else None;dump(window/'RESULTS.json',records)
  if row['result']is not None or(row['interrupted']or{}).get('physics_steps',0):
   row['replay_exit']=execute('replay_native_audit.py',[pair],pair/'replay.console',125);dump(window/'RESULTS.json',records)
  assert code==0 and row['result']is not None and row.get('replay_exit')==0,'INCOMPLETE_NAVIGATION_OR_REPLAY'
  assert execute('audit_static_run.py',[pair,'--window',window],pair/'static_audit.console',120)==0,'STATIC_PHYSICAL_OR_SOURCE_AUDIT_FAILED';row['static_audit']=read(pair/'STATIC_RUN_AUDIT.json');dump(window/'RESULTS.json',records)
  for script,cap in [('audit_forward_controller.py',60),('audit_route_commitment.py',60),('audit_projection_learning.py',60),('audit_all_tail_geometry.py',120),('audit_shadow_mode.py',60),('audit_reentry.py',120),('audit_complete_joint.py',60),('audit_nominal_layers.py',180)]:
   args=[pair]
   if script=='audit_projection_learning.py':args+=['--model',model]
   row['audits'][script]=execute(script,args,pair/(script+'.console'),cap);dump(window/'RESULTS.json',records);assert row['audits'][script]==0,script+'_FAILED'
  if len(records)>1:
   first=repo/records[0]['run'];assert sha(pair/'scene_model.mjb')==sha(first/'scene_model.mjb'),'VEHICLE_STATIC_MODEL_CHANGED_BETWEEN_NOISE_TASKS';assert read(pair/'STATIC_PROTOCOL.json')['start_qpos']==read(first/'STATIC_PROTOCOL.json')['start_qpos'],'INITIAL_VEHICLE_STATE_CHANGED'
  row['strict_success']=bool(row['static_audit']['strict_static_arrival']);dump(window/'RESULTS.json',records)
 status='FIVE_STATIC_DIAGNOSTIC_ROUNDS_COMPLETE';unchanged()
except BaseException as e:
 status='STOPPED_EXCEPTION';dump(window/'ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
finally:
 (repo/'REVIEW_PENDING').write_bytes(guard);ledger.update(round_closed=True,status=status,elapsed_s=time.time()-start,completed_navigation=sum(r['result']is not None for r in records));dump(root/'ROUND_WINDOW.json',ledger);dump(window/'COMPLETION.json',dict(status=status,records=records,unexecuted=5-len(records),not_dynamic_acceptance=True));dump(window/'ACTIVE.json',dict(status=status,completed=True))
print(json.dumps(dict(status=status,records=len(records))))
