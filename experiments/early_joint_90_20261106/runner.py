"""Five fixed development navigations, then a gated original24 confirmation."""
import fcntl,os,signal,subprocess,sys,time,traceback,shutil
from pathlib import Path
from evidence_rules import AUDITS,FUNCTIONAL_CHECKS,dump,main_gate,read,repeat_check,sha

def run(own):
 repo=own.parents[1];config=read(own/'BATCH.json');root=repo/config['output'];common=Path(__file__).parent
 master=(root/'driver.lock').open('a+');fcntl.flock(master,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not(root/'ROUND_WINDOW.json').exists(),'ALREADY_STARTED_NO_RETRY'
 freeze=read(own/'CANDIDATE_FREEZE.json');freeze_hash=sha(own/'CANDIDATE_FREEZE.json')
 assert freeze_hash==read(repo/'runs/early_joint_90_20261106/PREPARED.json')['source_freezes'][own.name],'FREEZE_MANIFEST_CHANGED'
 def unchanged():assert sha(own/'CANDIDATE_FREEZE.json')==freeze_hash and all(sha(repo/p)==h for p,h in freeze['files'].items()),'FROZEN_INPUT_CHANGED'
 unchanged();assert read(repo/'runs/early_joint_90_20261106/ZERO_MODEL_QUALIFICATION.json')['passed']
 if config['confirmation']:
  dep=read(repo/config['dependency']/'FINALIZED.json');assert dep['combined_three_route_development_passed']and dep['source_and_decompressed_sha_verified']
 assert(repo/'REVIEW_PENDING').exists();execution_lock=repo/'runs/v648_static_unknown/execution.lock'
 with execution_lock.open('rb')as probe:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
 started=time.time();deadline=min(config['absolute_deadline_unix'],started+config['batch_cap_s']);assert deadline-started>=config['minimum_start_budget_s']-1,'INSUFFICIENT_START_BUDGET'
 guard=(repo/'REVIEW_PENDING').read_bytes();(root/'REVIEW_PENDING.before').write_bytes(guard)
 os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});window=root/config['window'];window.mkdir(exist_ok=False);tasks=read(own/'TASK_LIST.json');records=[];preflights=[];process=None
 ledger=dict(started_unix=started,absolute_deadline_unix=deadline,campaign_deadline_unix=config['absolute_deadline_unix'],pid=os.getpid(),round_closed=False,attempted_navigation=0,tasks=tasks,training_updates=0,stage_access=0,real_robot=0)
 dump(root/'ROUND_WINDOW.json',ledger);dump(window/'LOCKED_TASK_LIST.json',tasks);dump(window/'SOURCE_FREEZE.json',{p.name:sha(p)for p in own.glob('*.py')});dump(window/'DOCUMENT_FREEZE.json',{p.name:sha(p)for p in own.glob('*.md')})
 model=repo/'runs/v690_visible_eight_meter/training_8m/proposer.json';env=dict(os.environ,PHASE_RECOVERY_ABLATION='FULL',PHASE_PROPOSAL_MODEL=str(model),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PHASE_MODEL_ABSOLUTE_DEADLINE=str(deadline),PHASE_PRIVATE_NATIVE_CAP='30000000')
 def execute(script,args,log,cap):
  nonlocal process
  unchanged();assert time.time()+cap+3<deadline,'ABSOLUTE_BUDGET_INSUFFICIENT'
  assert shutil.disk_usage(root).free>=20*1024**3,'INSUFFICIENT_RAW_EVIDENCE_DISK_STOP'
  args=list(map(str,args));dump(window/'ACTIVE.json',dict(script=script,args=args,started_unix=time.time(),cap_s=cap,absolute_deadline_unix=deadline));stage_lock=None
  try:
   if script!='run_static.py':
    stage_lock=execution_lock.open('rb');fcntl.flock(stage_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   command=[str(repo/'run_phase.sh')]
   if script=='run_static.py':command+=[str(own.relative_to(repo)/script)]
   else:command+=[str(common.relative_to(repo)/'worker_entry.py'),own.name,script]
   with log.open('x')as stream:
    process=subprocess.Popen([*command,*args],cwd=repo,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
    try:return process.wait(timeout=max(.01,min(cap,deadline-time.time())))
    finally:
     if process.poll()is None:
      os.killpg(process.pid,signal.SIGTERM)
      try:process.wait(timeout=2)
      except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
     process=None
  finally:
   if stage_lock is not None:stage_lock.close()
 def set_task(t):env.update(PHASE_COURSE_DISTANCE=str(t['course_distance_m']),PHASE_FIELD_CASE=t['case_id'],PHASE_COURSE_PHASE=str(t['phase']))
 status='RUNNING';signal.signal(signal.SIGTERM,lambda *_:(_ for _ in()).throw(TimeoutError('OUTER_TERMINATED')))
 try:
  (repo/'REVIEW_PENDING').unlink()
  for t in tasks:
   set_task(t);name=f"t0_slot{t['slot']:02d}";pair=root/name/'paired'
   assert execute('run_static.py',['--name',name,'--seed',t['seed'],'--wall-seconds',120,'--max-steps',1200,'--initial-observation-steps',0,'--feasibility-only'],window/(name+'.console'),125)==0,'T0_INITIALIZATION_FAILED'
   assert execute('audit_field_discovery.py',[pair,'--preflight','--output-dir',pair/'field_preflight'],window/(name+'_audit.console'),90)==0,'T0_CAUSAL_FAILED'
   preflights.append(dict(task=t,run=str(pair.relative_to(repo)),causal_audit=str((pair/'field_preflight/INITIAL_UNSEEN_AUDIT_V699.json').relative_to(repo))));dump(window/'PREFLIGHTS.json',preflights)
  assert execute('audit_field_preflight.py',[window],window/'noise_audit.console',60)==0,'T0_NOISE_FAILED'
  by={t['slot']:t for t in tasks}
  if config['confirmation']:plan=[('MAIN',t)for t in tasks]+[('REPEAT',by[s])for s in config['repeat_slots']]
  else:plan=[(role,t)for t in tasks for role in ['MAIN','REPEAT']]
  for role,t in plan:
   if config['confirmation']and role=='REPEAT':assert main_gate(tasks,records,True)['passed'],'CONFIRMATION_DENOMINATOR_GATE_FAILED'
   base=None
   if role=='REPEAT':
    base=next(x for x in records if x['role']=='MAIN'and x['task']['slot']==t['slot'])
    assert base['functional_passed'],'FIXED_REPEAT_BASE_FAILED_NO_SUBSTITUTE'
   set_task(t);name=role.lower()+f"_slot{t['slot']:02d}";pair=root/name/'paired'
   row=dict(name=name,task=t,role=role,run=str(pair.relative_to(repo)),physical_passed=False,functional_passed=False,audits={});records.append(row);ledger['attempted_navigation']+=1;dump(root/'ROUND_WINDOW.json',ledger);dump(window/'RESULTS.json',records)
   code=execute('run_static.py',['--name',name,'--seed',t['seed'],'--wall-seconds',1500,'--max-steps',1200,'--initial-observation-steps',0],window/(name+'.console'),1505);row['runner_exit']=code;row['result']=read(pair/'geometry_memory/result.json')if(pair/'geometry_memory/result.json').exists()else None;row['interrupted']=read(pair/'geometry_memory/interrupted.json')if(pair/'geometry_memory/interrupted.json').exists()else None;dump(window/'RESULTS.json',records)
   if row['result']is not None or(row['interrupted']or{}).get('public_steps',0)>0:row['replay_exit']=execute('replay_native_audit.py',[pair],pair/'replay.console',60);dump(window/'RESULTS.json',records)
   assert code==0 and row['result']is not None,'NAVIGATION_INCOMPLETE';assert row.get('replay_exit')==0,'NATIVE_REPLAY_FAILED'
   for script,_,cap in AUDITS:
    args=[pair]
    if script=='audit_run.py':args+=['--window',window]
    if script=='audit_projection_learning.py':args+=['--model',model]
    code=execute(script,args,pair/(script+'.console'),cap);row['audits'][script]=code;dump(window/'RESULTS.json',records);assert code==0,script+'_FAILED'
   code=execute('audit_field_discovery.py',[pair,'--output-dir',pair/'discovery_audit'],pair/'discovery_audit.console',240)
   cp=pair/'discovery_audit/DISCOVERY_CHAIN_AUDIT_V699.json';assert cp.exists(),'DISCOVERY_AUDIT_CRASH';chain=read(cp);failed=[k for k,v in chain['checks'].items()if not v]
   assert not(set(failed)-FUNCTIONAL_CHECKS),'CAUSAL_EVIDENCE_ANOMALY';assert(code==0)==(chain['status']=='PASS'),'DISCOVERY_EXIT_INCONSISTENT'
   row.update(physical_passed=True,functional_passed=bool(chain['status']=='PASS'and row['result']['strict_safe_arrival']),functional_failed_checks=failed);dump(window/'RESULTS.json',records)
   if role=='REPEAT':
    assert row['functional_passed'],'REPEAT_FUNCTIONAL_FAILURE';sys.path.insert(0,str(own));from contact_fingerprint import compare_contacts
    exact=repeat_check(repo/base['run'],pair,base['result'],row['result'],compare_contacts);dump(pair/'EXACT_REPEAT_AUDIT.json',exact);assert exact['passed'],'EXACT_REPEAT_ANOMALY'
   elif not row['functional_passed']:
    failures=sum(x['role']=='MAIN'and x['physical_passed']and not x['functional_passed']for x in records)
    if not config['confirmation']or failures>=2:status='FUNCTIONAL_NOT_PASSED_STOP';raise StopIteration(status)
  unchanged();status='FROZEN_TASKS_AND_REPEATS_COMPLETED'
 except StopIteration:pass
 except BaseException as error:
  status='STOPPED_EXCEPTION';dump(window/'ERROR.json',dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
 finally:
  (repo/'REVIEW_PENDING').write_bytes(guard);ledger.update(round_closed=True,status=status,elapsed_s=time.time()-started);dump(root/'ROUND_WINDOW.json',ledger);dump(window/'COMPLETION.json',dict(status=status,records=records,automatic_additional_navigation=False));dump(window/'ACTIVE.json',dict(completed=True,status=status))
 with(root/'finalize.console').open('x')as stream:p=subprocess.run([sys.executable,'-B',str(own/'finalize.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,timeout=1800)
 assert p.returncode==0,'ZERO_MODEL_FINALIZER_FAILED'
 return read(root/'FINALIZED.json')
