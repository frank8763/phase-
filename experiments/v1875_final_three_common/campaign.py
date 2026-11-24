"""Finite detached fixed-order evening campaign. No automatic source repair."""
from pathlib import Path
import fcntl,hashlib,json,os,selectors,signal,subprocess,sys,time,traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
BOOT=Path('/proc/sys/kernel/random/boot_id').read_text().strip();START=time.monotonic();WALL=time.time()
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');t.replace(p)
def alive(i):
 p=Path('/proc',str(i['pid']),'stat')
 return i.get('boot_id',BOOT)==BOOT and p.exists()and ('start_ticks'not in i or p.read_text().split(') ',1)[1].split()[19]==i['start_ticks'])
def kill(i):
 if alive(i):
  os.killpg(i.get('pgid',i['pid']),signal.SIGTERM);end=time.monotonic()+8
  while alive(i)and time.monotonic()<end:time.sleep(.05)
  if alive(i):os.killpg(i.get('pgid',i['pid']),signal.SIGKILL)
def stage(name,args,timeout,rid=None,allow_failure=False):
 auth=read(O/'AUTHORIZATION.json');rootmono=START+auth['deadline_unix']-WALL;wall=time.time();mono=time.monotonic();raw=bytearray();last=0
 assert wall<auth['deadline_unix']and mono<rootmono
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
 if rid:env['PHASE_EVENING_ASSIGNMENT']=rid
 else:env.pop('PHASE_EVENING_ASSIGNMENT',None)
 p=subprocess.Popen([sys.executable,'-B',*args],cwd=R,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
 st=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split();identity=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=st[19],boot_id=BOOT,command=args)
 folder=O/'live_io'/(rid or 'source');put(folder/(name+'_OWNED.json'),identity);print(json.dumps(dict(stage=name,round=rid,started=True,pid=p.pid)),flush=True)
 try:
  sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ)
  while sel.get_map():
   assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT and time.time()<min(wall+timeout,auth['deadline_unix'])and time.monotonic()<min(mono+timeout,rootmono),'STAGE_OR_2100_DUAL_CLOCK_STOP'
   if time.monotonic()-last>=15:
    progress=None;path=O/'rounds'/rid/'actual/ACTUAL_PROGRESS.json'if rid else None
    if path is not None and path.exists():progress=read(path)
    put(O/'RUNNING_CHECKPOINT.json',dict(stage=name,round_id=rid,owned=identity,stage_elapsed_s=time.monotonic()-mono,actual_partial=progress,partial_not_scientific_pass=True,unix=time.time(),deadline_local=auth['deadline_local']));last=time.monotonic()
   for key,_ in sel.select(.2):
    block=os.read(key.fileobj.fileno(),16384)
    if not block:sel.unregister(key.fileobj);continue
    used=sum(x.stat().st_size for x in folder.glob('*.console'))
    assert used+len(raw)+len(block)<=4*1024**2,'CAMPAIGN_ROUND_CONSOLE_4MIB';raw.extend(block)
  p.wait(timeout=5)
 finally:
  if p.poll()is None:
   if rid:
    base=O/'rounds'/rid
    for path in [base/'actual/TEB_NATIVE_OWNED_CHILD.json',base/'OWNED_CHILD.json']:
     if path.exists():kill(read(path))
   elif(O/'SOURCE_OWNED_CHILD.json').exists():kill(read(O/'SOURCE_OWNED_CHILD.json'))
   kill(identity)
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:pass
  (folder/(name+'.console')).write_bytes(raw);put(folder/(name+'_EXIT.json'),dict(returncode=p.poll(),wall_s=time.monotonic()-mono,closed=True,owned=identity))
 assert allow_failure or p.returncode==0,'STAGE_FAILED:'+name
 return p.returncode
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 assert not(O/'CAMPAIGN_ONCE_CLAIM.json').exists()
 auth=read(O/'AUTHORIZATION.json');assert auth['boot_id']==BOOT and WALL+7200<auth['deadline_unix']
 cur=read(R/'CURRENT_EXPERIMENT.json');assert cur['active_round']is None and not cur['models_now_authorized']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 studylock=(R/'runs/v1643_formal_parent_metadata/OWNER.lock').open();fcntl.flock(studylock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 put(O/'CAMPAIGN_ONCE_CLAIM.json',dict(pid=os.getpid(),pgid=os.getpgid(0),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],boot_id=BOOT,started_unix=WALL,deadline_unix=auth['deadline_unix'],hard_stop_monotonic=START+auth['deadline_unix']-WALL,maximum_assignments=3,no_chat_supervision=True,no_source_repair_or_seed_rescue=True))
 done=[];result=dict(closed=False,pipeline_passed=False,scientific_successes=0,completed_rounds=done,registered_plan=3,first_error=None)
 try:
  from_prior=read(O/'PRIOR_CLOSED_BARRIERS.json');assert from_prior['passed']
  for path,h in from_prior['proof_paths_SHA256'].items():assert sha(R/path)==h
  if not(O/'SOURCE_QUALIFICATION.json').exists():stage('source',[str(C/'source_owner.py')],200)
  else:
   assert read(O/'SOURCE_QUALIFICATION.json')['passed']and read(O/'SOURCE_OUTER_CLOSED.json')['passed']
   assert all(sha(R/n)==h for n,h in read(O/'SOURCE_FREEZE.json')['files'].items())
  assert read(O/'SOURCE_QUALIFICATION.json')['passed']and read(O/'SOURCE_OUTER_CLOSED.json')['passed']
  stage('source_archive',[str(R/'experiments/v1876_final_three_source_recovery/finalize.py')],180)
  assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R).strip(),'UNRELATED_STAGED_CHANGES'
  paths=['experiments/'+x for x in ['v1874_capture_before_nplus1','v1875_final_three_common','v1876_final_three_source_recovery','v1877_final_three_runtime_recovery']]+['docs/FINAL_THREE_CAPTURE_CLOSURE_20261124.md']
  subprocess.run(['git','add',*paths],cwd=R,check=True,timeout=30)
  subprocess.run(['git','add','-f',*[str((O/n).relative_to(R))for n in ['AUTHORIZATION.json','PLAN_LOCKED.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json']]],cwd=R,check=True,timeout=30)
  commit=subprocess.run(['git','commit','-m','Freeze capture-before-Nplus1 closure for remaining three common EW tasks'],cwd=R,capture_output=True,text=True,timeout=30);put(O/'SOURCE_COMMIT_RESULT.json',dict(returncode=commit.returncode,stdout=commit.stdout,stderr=commit.stderr));assert commit.returncode==0
  stage('source_sync',[str(R/'experiments/v1876_final_three_source_recovery/deliver.py'),'--source-sync'],45)
  assert read(R/'runs/v1876_final_three_source_recovery/SOURCE_SYNC_RESULT.json')['remote_verified']
  stage('source_deliver',[str(R/'experiments/v1876_final_three_source_recovery/deliver.py')],650)
  stage('source_chain',[str(R/'experiments/v1876_final_three_source_recovery/chain.py')],120)
  plan=read(O/'PLAN_LOCKED.json')['assignments']
  for row in plan:
   if time.time()+7200>=auth['deadline_unix']:result['stopped_for_complete_window']=True;break
   rid=row['round_id'];base=O/'rounds'/rid;assert not(base/'PILOT_ONCE_CLAIM.json').exists()and not(base/'COMPLETION.json').exists()
   frozen=read(O/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
   usage=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert usage+1015*1024**2<15*1024**3,'FRESH_FULL_SCOPE_15GIB_CAP'
   for n in ['SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','CURRENT_SOURCE_REMOTE_RECOVERY.json']:
    target=base/n;assert not target.exists();target.symlink_to(Path('../..')/n);assert sha(target)==sha(O/n)
   ledgerpath=R/'runs/v1805_common_algorithm_registry/LEDGER.json';ledger=read(ledgerpath);slot=next(x for x in ledger['slots']if x['method']==row['method']and x['task_id']==row['common_task']);assert not slot['registered']and not slot['closed']
   slot.update(registered=True,status='ACTIVE_ONCE_REGISTERED_FULL_TASK_ATTEMPT',source_version=str(O.relative_to(R)),source_freeze_sha256=sha(O/'SOURCE_FREEZE.json'));ledger.update(registered=sum(bool(x['registered'])for x in ledger['slots']),unexecuted=sum(not x['registered']for x in ledger['slots']));put(ledgerpath,ledger)
   stage('owner',[str(R/'experiments'/row['production']/'owner.py')],5500,rid,True)
   assert read(base/'COMPLETION.json')['closed']
   stage('review',[str(C/'review.py')],120,rid)
   outcome=read(base/'RUNTIME_CLOSED_REVIEW.json')
   stage('archive',[str(R/'experiments/v1877_final_three_runtime_recovery/finalize.py')],180,rid)
   stage('source_proof',[str(R/'experiments/v1877_final_three_runtime_recovery/deliver.py'),'--source-sync'],30,rid)
   delivered=stage('deliver',[str(R/'experiments/v1877_final_three_runtime_recovery/deliver.py')],650,rid,True)
   if delivered!=0:stage('transport_resume',[str(C/'transport_resume.py')],650,rid)
   stage('barrier',[str(C/'review.py'),'--barrier'],120,rid)
   assert read(base/'POST_ROUND_STORAGE_BARRIER.json')['passed']
   done.append(dict(round_id=rid,method=row['method'],classification=outcome['classification'],actual_native=outcome['actual_native'],own_replay_native=outcome['own_replay_native'],remote_closed=True));result['scientific_successes']+=int(outcome['qualified_whole_navigation_passed'])
   put(O/'COMPLETED_PROGRESS.json',dict(done=done,unexecuted_remaining=3-len(done),unix=time.time()))
   cur=read(R/'CURRENT_EXPERIMENT.json');cur.update(evening_completed_assignments=16+len(done),evening_unexecuted_assignments=3-len(done));put(R/'CURRENT_EXPERIMENT.json',cur)
   if outcome['classification']=='TECHNICAL_OR_UNQUALIFIED_EVIDENCE_CENSOR':result['stopped_for_technical_or_evidence_failure']=True;break
  result['pipeline_passed']=True
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc(),all_originals_retained=True)
 finally:
  result.update(closed=True,wall_s=time.monotonic()-START,closed_unix=time.time(),unexecuted_remaining=3-len(done),no_more_models_started=True);put(O/'CAMPAIGN_RESULT.json',result)
  cur=read(R/'CURRENT_EXPERIMENT.json');cur.update(status='EVENING_COMMON_CAMPAIGN_CLOSED_REVIEW_REQUIRED',background_preparation_active=False,automatic_next_round=False,manual_review_after_every_round=False,latest_background_result=str((O/'CAMPAIGN_RESULT.json').relative_to(R)),next_experiment='Review fixed evening results; no automatic successor')
  if cur.get('active_round')is None:cur.update(models_now_authorized=False,evening_active_assignments=0)
  put(R/'CURRENT_EXPERIMENT.json',cur);studylock.close()
 print(json.dumps(result),flush=True);return 0 if result['pipeline_passed']else 1
if __name__=='__main__':raise SystemExit(main())
