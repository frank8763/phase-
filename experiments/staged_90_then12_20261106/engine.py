"""Sequential isolated models; one pilot then exactly three conditional development navigations."""
import fcntl,json,math,os,signal,subprocess,sys,time,traceback,shutil
from pathlib import Path
from evidence_rules import AUDITS,FUNCTIONAL_CHECKS,dump,read,sha,repeat_check
from limits import pilot_limits,model_fits
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;W=R/'experiments/v842_staged_long_navigation';O=R/'runs/v842_staged_long_navigation';ROOT=R/'runs/staged_90_then12_20261106'

def unchanged():
 frozen=read(W/'CANDIDATE_FREEZE.json');assert sha(W/'CANDIDATE_FREEZE.json')==read(ROOT/'PREPARED.json')['freeze_sha256']and all(sha(R/n)==h for n,h in frozen['files'].items()),'FROZEN_SOURCE_OR_INPUT_CHANGED'
 claim=ROOT/'DEVELOPMENT12_WINDOW_CLAIM.json'
 if claim.exists():
  c=read(claim);assert sha(ROOT/'PILOT_REFERENCE_FREEZE.json')==c['reference_freeze_sha256']and sha(O/'pilot90/FINALIZED.json')==c['pilot_finalized_sha256']and all(sha(R/n)==h for n,h in read(ROOT/'PILOT_REFERENCE_FREEZE.json')['files'].items()),'PILOT_REFERENCE_CHANGED'

def stage_run(stage,deadline,pilot=None):
 phase=O/stage;phase.mkdir(exist_ok=False);lock=(phase/'driver.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard=(R/'REVIEW_PENDING').read_bytes();(phase/'REVIEW_PENDING.before').write_bytes(guard);tasks=read(W/'TASK_LIST.json');tasks_by={t['seed']:t for t in tasks};started=time.time();rows=[];pre=[];extras=[];process=None;status='RUNNING'
 window=dict(stage=stage,started_unix=started,absolute_deadline_unix=deadline,round_closed=False,pid=os.getpid(),training=0,stage_access=0)
 dump(phase/'ROUND_WINDOW.json',window);dump(phase/'SOURCE_FREEZE.json',{p.name:sha(p)for p in W.glob('*.py')});dump(phase/'DOCUMENT_FREEZE.json',{p.name:sha(p)for p in W.glob('*.md')});dump(phase/'LOCKED_PLAN.json',dict(tasks=tasks,stage=stage,navigation_order=['pilot_main02']if stage=='pilot90'else['long_repeat02','long_main08','long_repeat08']))
 model=R/'runs/v690_visible_eight_meter/training_8m/proposer.json';env=dict(os.environ,PHASE_RECOVERY_ABLATION='FULL',PHASE_PROPOSAL_MODEL=str(model),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PHASE_MODEL_ABSOLUTE_DEADLINE=str(deadline),PHASE_PRIVATE_NATIVE_CAP='100000000',PHASE_NAV_SOFT_WALL_S='120')
 def execute(script,args,log,cap,models=False):
  nonlocal process
  unchanged();assert shutil.disk_usage(O).free>=25*1024**3,'EVIDENCE_DISK_LOW_STOP_NO_DELETE'
  if models:assert model_fits(deadline,time.time(),cap),'MODEL_ABSOLUTE_BUDGET_INSUFFICIENT'
  dump(phase/'ACTIVE.json',dict(script=script,args=list(map(str,args)),model_operation=models,started_unix=time.time(),cap_s=cap,absolute_model_deadline=deadline));held=None
  try:
   if script!='run_static.py':held=(R/'runs/v648_static_unknown/execution.lock').open('rb');fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
   cmd=[str(R/'run_phase.sh')]
   if script=='run_static.py':cmd+=[str(W.relative_to(R)/script)]
   else:
    cmd+=[str(C.relative_to(R)/'worker_entry.py')]
    if not models:cmd+=['--saved-only']
    cmd+=[W.name,script]
   with log.open('x')as f:
    process=subprocess.Popen([*cmd,*map(str,args)],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
    try:return process.wait(timeout=cap)
    finally:
     if process.poll()is None:
      os.killpg(process.pid,signal.SIGTERM)
      try:process.wait(timeout=2)
      except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
     process=None
  finally:
   if held is not None:held.close()
 def set_task(t):env.update(PHASE_COURSE_DISTANCE=str(t['course_distance_m']),PHASE_FIELD_CASE=t['case_id'],PHASE_COURSE_PHASE=str(t['phase']))
 def t0(t,name):
  set_task(t);pair=O/name/'paired';extras.append(str(pair.parent.relative_to(R)))
  assert execute('run_static.py',['--name',name,'--seed',t['seed'],'--wall-seconds',120,'--max-steps',1200,'--initial-observation-steps',0,'--feasibility-only'],phase/(name+'.console'),125,True)==0,'T0_FAILED'
  assert execute('audit_field_discovery.py',[pair,'--preflight','--output-dir',pair/'field_preflight'],phase/(name+'_causal.console'),90)==0,'T0_CAUSAL_FAILED'
  return dict(task=t,run=str(pair.relative_to(R)),causal_audit=str((pair/'field_preflight/INITIAL_UNSEEN_AUDIT_V699.json').relative_to(R)))
 def save():dump(phase/'RESULTS.json',rows);dump(phase/'ARCHIVE_EXTRA_PATHS.json',extras)
 def unit(t,name,role,base=None):
  set_task(t);limits=pilot_limits(deadline,time.time())if stage=='pilot90'else dict(soft=5400,hard=5700,outer=5705);assert model_fits(deadline,time.time(),limits['outer']+180),'NO_FULL_NAV_REPLAY_METADATA_BUDGET'
  env['PHASE_NAV_SOFT_WALL_S']=str(limits['soft']);pair=O/name/'paired';extras.append(str(pair.parent.relative_to(R)));row=dict(name=name,role=role,task=t,run=str(pair.relative_to(R)),audits={},physical_passed=False,functional_passed=False,base=None if base is None else base['run'],limits=limits);rows.append(row);save()
  code=execute('run_static.py',['--name',name,'--seed',t['seed'],'--wall-seconds',limits['hard'],'--max-steps',1200,'--initial-observation-steps',0],phase/(name+'.console'),limits['outer'],True);row['runner_exit']=code;row['result']=read(pair/'geometry_memory/result.json')if(pair/'geometry_memory/result.json').exists()else None;row['interrupted']=read(pair/'geometry_memory/interrupted.json')if(pair/'geometry_memory/interrupted.json').exists()else None;save()
  if row['result']is not None or(row['interrupted']or{}).get('public_steps',0)>0:row['replay_exit']=execute('replay_native_audit.py',[pair],pair/'replay.console',60,True);save()
  assert code==0 and row['result']is not None,'NAVIGATION_INTERRUPTED_NO_RETRY';assert row.get('replay_exit')==0,'NATIVE_REPLAY_FAILED'
  # The only MJB metadata auditor is completed within the model window; all later audits forbid models.
  row['audits']['audit_run.py']=execute('audit_run.py',[pair,'--window',phase],pair/'audit_run.py.console',120,True);save();assert row['audits']['audit_run.py']==0,'CANONICAL_AUDIT_FAILED'
  for script,filename,cap in AUDITS:
   if script=='audit_run.py':continue
   args=[pair]
   if script=='audit_projection_learning.py':args+=['--model',model]
   row['audits'][script]=execute(script,args,pair/(script+'.console'),cap);save();assert row['audits'][script]==0,script+'_FAILED'
  code=execute('audit_field_discovery.py',[pair,'--output-dir',pair/'discovery_audit'],pair/'discovery_audit.console',240);path=pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json';assert path.exists(),'DISCOVERY_AUDIT_CRASH';chain=read(path);failed=[k for k,v in chain['checks'].items()if not v];assert not(set(failed)-FUNCTIONAL_CHECKS),'DISCOVERY_SAFETY_OR_CAUSAL_ANOMALY';assert(code==0)==(chain['status']=='PASS')
  row.update(physical_passed=True,functional_passed=bool(chain['status']=='PASS'and row['result']['strict_safe_arrival']),functional_failed_checks=failed);save()
  if base is not None:
   sys.path.insert(0,str(W));from contact_fingerprint import compare_contacts
   exact=repeat_check(R/base['run'],pair,read(R/base['run']/'geometry_memory/result.json'),row['result'],compare_contacts);dump(pair/'EXACT_REPEAT_AUDIT.json',exact);row['repeat_passed']=exact['passed'];save();assert exact['passed'],'COMPLETE_REPEAT_MISMATCH'
  if not row['functional_passed']:raise StopIteration('FUNCTIONAL_NOT_PASSED_STOP')
  return row
 try:
  unchanged();assert(R/'REVIEW_PENDING').exists();(R/'REVIEW_PENDING').unlink()
  if stage=='pilot90':
   pre=[t0(tasks_by[10060002],'pilot_t0_02')];dump(phase/'LOCKED_T0_TASK_LIST.json',[tasks_by[10060002]])
  else:
   assert pilot is not None;pre=[read(O/'pilot90/PREFLIGHTS.json')[0],t0(tasks_by[10060008],'long_t0_08')];dump(phase/'LOCKED_T0_TASK_LIST.json',tasks);dump(phase/'PILOT_REFERENCE.json',pilot);extras.extend([str((O/'pilot90/FINALIZED.json').relative_to(R)),str((O/'pilot90/FINAL_INDEPENDENT_AUDIT.json').relative_to(R))])
  dump(phase/'PREFLIGHTS.json',pre);assert execute('audit_field_preflight.py',[phase],phase/'preflight_audit.console',60)==0,'REGISTERED_T0_AUDIT_FAILED'
  if stage=='pilot90':unit(tasks_by[10060002],'pilot_main02','PILOT_MAIN')
  else:
   baseline=read(O/'pilot90/FINAL_INDEPENDENT_AUDIT.json')['records'][0];unit(tasks_by[10060002],'long_repeat02','REPEAT',baseline);main=unit(tasks_by[10060008],'long_main08','MAIN');unit(tasks_by[10060008],'long_repeat08','REPEAT',main)
  status='FROZEN_STAGE_COMPLETED'
 except StopIteration as e:status=str(e)
 except BaseException as e:status='STOPPED_EXCEPTION';dump(phase/'ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
 finally:
  (R/'REVIEW_PENDING').write_bytes(guard);window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump(phase/'ROUND_WINDOW.json',window);save();dump(phase/'COMPLETION.json',dict(status=status,records=rows,new_confirmation=0,retries=0));dump(phase/'ACTIVE.json',dict(completed=True,status=status))
 with(phase/'finalize.console').open('x')as f:p=subprocess.run([sys.executable,'-B',str(C/'finalize.py'),stage],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=2400)
 assert p.returncode==0 and(phase/'FINALIZED.json').exists(),'FINALIZER_FAILED_NO_RETRY'
 return read(phase/'FINALIZED.json')
