"""Frozen science, three preregistered t0, and main/repeat per route; first failure stops."""
import fcntl,json,os,shutil,signal,subprocess,sys,time,traceback
from pathlib import Path
from common import *
from repeat import compare

def wait_bounded(process,cap,models,deadline):
 until=time.monotonic()+cap
 while True:
  remaining=until-time.monotonic()
  if models:remaining=min(remaining,deadline-time.time())
  if remaining<=0:raise TimeoutError('ABSOLUTE_PROCESS_OR_MODEL_DEADLINE_NO_EXTENSION')
  assert shutil.disk_usage(ROOT).free>=25*1024**3,'EVIDENCE_DISK_LOW_STOP_NO_DELETE'
  try:return process.wait(timeout=min(10.,remaining))
  except subprocess.TimeoutExpired:pass

class Stage:
 def __init__(self,deadline,phase=PHASE,raw=RAW):
  self.deadline=deadline;self.phase=phase;self.raw=raw;self.rows=[];self.pre=[];self.extras=['runs/v850_progress_consistent_return/saved_qualification','runs/v850_progress_consistent_return/qualification','runs/v850_progress_consistent_return/component01','runs/v850_progress_consistent_return/AUTHORIZATION.json','runs/v842_staged_long_navigation/long_main08','runs/v827_goal_route_validation/repeat_slot02','runs/v827_goal_route_validation/main_slot01','runs/v827_goal_route_validation/main_slot03','runs/v827_goal_route_validation/t0_slot02','runs/v827_goal_route_validation/t0_slot01','runs/v827_goal_route_validation/t0_slot03'];self.process=None
  self.env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PHASE_RECOVERY_ABLATION='FULL',PHASE_PROPOSAL_MODEL=str(R/'runs/v690_visible_eight_meter/training_8m/proposer.json'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PHASE_MODEL_ABSOLUTE_DEADLINE=str(deadline),PHASE_PRIVATE_NATIVE_CAP='100000000',PHASE_NAV_SOFT_WALL_S='5400')
 def save(self):dump(self.phase/'RESULTS.json',self.rows);dump(self.phase/'PREFLIGHTS.json',self.pre);dump(self.phase/'ARCHIVE_EXTRA_PATHS.json',self.extras)
 def execute(self,script,args,log,cap,models=False,on_launch=None):
  unchanged();assert shutil.disk_usage(ROOT).free>=25*1024**3,'EVIDENCE_DISK_LOW_STOP_NO_DELETE'
  if models:assert model_fits(self.deadline,time.time(),cap),'INSUFFICIENT_ABSOLUTE_MODEL_BUDGET'
  dump(self.phase/'ACTIVE.json',dict(script=script,args=list(map(str,args)),model_operation=models,started_unix=time.time(),cap_s=cap,absolute_model_deadline=self.deadline));held=None
  try:
   if script!='run_static.py':held=(R/'runs/v648_static_unknown/execution.lock').open('rb');fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
   command=[str(R/'run_phase.sh')]
   if script=='run_static.py':command+=[str(W.relative_to(R)/script)]
   elif script=='replay_native_audit.py':command+=[str(Path('experiments/staged_90_then12_20261106/worker_entry.py')),W.name,script]
   else:
    command+=[str(C.relative_to(R)/'audit_entry.py'),'--write-root',str(args[0])]
    if script=='audit_run.py':command+=['--model-deadline',str(self.deadline)]
    command+=[script]
   with log.open('x')as stream:
    self.process=subprocess.Popen([*command,*map(str,args)],cwd=R,env=self.env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
    if on_launch:on_launch(self.process.pid)
    try:return wait_bounded(self.process,cap,models,self.deadline)
    finally:
     if self.process.poll()is None:
      os.killpg(self.process.pid,signal.SIGTERM)
      try:self.process.wait(timeout=2)
      except subprocess.TimeoutExpired:os.killpg(self.process.pid,signal.SIGKILL);self.process.wait()
     self.process=None
  finally:
   if held is not None:held.close()
 def set_task(self,t):self.env.update(PHASE_COURSE_DISTANCE=str(t['course_distance_m']),PHASE_FIELD_CASE=t['case_id'],PHASE_COURSE_PHASE=str(t['phase']))
 def t0(self,t):
  self.set_task(t);name=f'v850_t0_slot{t["slot"]:02d}';pair=self.raw/name/'paired';self.extras.append(str(pair.parent.relative_to(R)));self.save()
  assert self.execute('run_static.py',['--name',name,'--seed',t['seed'],'--wall-seconds',120,'--max-steps',1200,'--initial-observation-steps',0,'--feasibility-only'],self.phase/(name+'.console'),125,True)==0,'T0_FAILED'
  assert self.execute('audit_field_discovery.py',[pair,'--preflight','--output-dir',pair/'field_preflight'],self.phase/(name+'_causal.console'),90)==0,'T0_CAUSAL_FAILED'
  self.pre.append(dict(task=t,run=str(pair.relative_to(R)),causal_audit=str((pair/'field_preflight/INITIAL_UNSEEN_AUDIT_V699.json').relative_to(R))));self.save()
 def unit(self,t,role,base=None):
  self.set_task(t);assert model_fits(self.deadline,time.time(),2400),'NO_MINIMUM_COMPLETE_NAVIGATION_REPLAY_BUDGET'
  name=f'v850_{role.lower()}_slot{t["slot"]:02d}';pair=self.raw/name/'paired';self.extras.append(str(pair.parent.relative_to(R)));row=dict(name=name,task=t,role=role,run=str(pair.relative_to(R)),base=None if base is None else base['run'],navigation_started=False,limits=dict(soft=5400,hard=5700,outer=5705,public_steps=1200,private_native=100000000),audits={},physical_passed=False,functional_passed=False);self.rows.append(row);self.save()
  def launched(pid):row.update(navigation_started=True,navigation_pid=pid,navigation_started_unix=time.time());self.save()
  soft=min(5400,int(self.deadline-time.time())-180);hard=soft+30;outer=hard+5
  assert soft>=2200
  self.env['PHASE_NAV_SOFT_WALL_S']=str(soft);row['limits'].update(soft=soft,hard=hard,outer=outer);self.save()
  code=self.execute('run_static.py',['--name',name,'--seed',t['seed'],'--wall-seconds',hard,'--max-steps',1200,'--initial-observation-steps',0],self.phase/(name+'.console'),outer,True,launched);row['runner_exit']=code
  for filename,key in [('result.json','result'),('interrupted.json','interrupted')]:row[key]=read(pair/'geometry_memory'/filename)if(pair/'geometry_memory'/filename).exists()else None
  self.save()
  if row['result']is not None or(row['interrupted']or{}).get('public_steps',0)>0:row['replay_exit']=self.execute('replay_native_audit.py',[pair],pair/'replay.console',60,True);self.save()
  assert code==0 and row['result']is not None,'NAVIGATION_INTERRUPTED_NO_RETRY';assert row.get('replay_exit')==0,'FULL_NATIVE_REPLAY_FAILED'
  expected=read(ROOT/'QUALIFICATION.json')['expected_audit_statuses']
  for script,filename,cap in AUDITS:
   args=[pair]
   if script=='audit_run.py':args+=['--window',self.phase]
   if script=='audit_projection_learning.py':args+=['--model',R/'runs/v690_visible_eight_meter/training_8m/proposer.json']
   row['audits'][script]=self.execute(script,args,pair/(script+'.console'),cap,script=='audit_run.py');self.save();assert row['audits'][script]==0,script+'_FAILED'
   data=read(pair/filename);assert data['status']==expected[script]and all(data.get('checks',{}).values()),script+'_INDEPENDENT_CHECK_FAILED'
  code=self.execute('audit_field_discovery.py',[pair,'--output-dir',pair/'discovery_audit'],pair/'discovery_audit.console',300);chain=read(pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json');failed=[k for k,v in chain['checks'].items()if not v];assert not(set(failed)-FUNCTIONAL_CHECKS),'DISCOVERY_SAFETY_OR_CAUSAL_ANOMALY';assert(code==0)==(chain['status']=='PASS')
  row.update(physical_passed=True,functional_passed=chain['status']=='PASS'and row['result']['strict_safe_arrival'],functional_failed_checks=failed);self.save()
  if base is not None:
   repeat=compare(R/base['run'],pair);dump(pair/'EXACT_REPEAT_AUDIT.json',repeat);row['repeat_passed']=repeat['passed'];self.save();assert repeat['passed'],'COMPLETE_NATIVE_REPEAT_MISMATCH'
  if not row['functional_passed']:raise StopIteration('FUNCTIONAL_NOT_PASSED_STOP')
  return row
 def run_steps(self):
  dump(self.phase/'LOCKED_T0_TASK_LIST.json',tasks())
  for t in tasks():self.t0(t)
  assert self.execute('audit_field_preflight.py',[self.phase],self.phase/'preflight_audit.console',60)==0,'THREE_T0_AUDIT_FAILED'
  for t in tasks():
   main=self.unit(t,'MAIN');self.unit(t,'REPEAT',main)
 def run(self):
  self.phase.mkdir(exist_ok=False);self.lock=(self.phase/'driver.lock').open('a');fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard=(R/'REVIEW_PENDING').read_bytes();(self.phase/'REVIEW_PENDING.before').write_bytes(guard);started=time.time();window=dict(started_unix=started,absolute_deadline_unix=self.deadline,pid=os.getpid(),round_closed=False);dump(self.phase/'ROUND_WINDOW.json',window)
  dump(self.phase/'SOURCE_FREEZE.json',{p.name:sha(p)for p in W.glob('*.py')});dump(self.phase/'DOCUMENT_FREEZE.json',{p.name:sha(p)for p in W.glob('*.md')});dump(self.phase/'LOCKED_PLAN.json',dict(tasks=tasks(),navigation_order=names(),new24=0));status='RUNNING'
  try:
   unchanged();(R/'REVIEW_PENDING').unlink();self.run_steps();assert complete_gate(self.rows);status='FROZEN_STAGE_COMPLETED'
  except StopIteration as e:status=str(e)
  except BaseException as e:status='STOPPED_EXCEPTION';dump(self.phase/'ERROR.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()))
  finally:
   (R/'REVIEW_PENDING').write_bytes(guard);window.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump(self.phase/'ROUND_WINDOW.json',window);self.save();dump(self.phase/'COMPLETION.json',dict(status=status,records=self.rows,new24=0,retries=0));dump(self.phase/'ACTIVE.json',dict(completed=True,status=status))
  return dict(status=status,records=self.rows)
