"""One shared-condition TEB actual and exact evidence closure, no successors."""
from pathlib import Path
import fcntl,hashlib,json,os,selectors,signal,subprocess,sys,time,traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name;O=R/'runs/v1834_teb_common_entry_gate';ROOT=R/'runs/v1805_common_algorithm_registry';BOOT=Path('/proc/sys/kernel/random/boot_id').read_text().strip();START=time.monotonic()
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');t.replace(p)
def alive(i):
 p=Path('/proc')/str(i['pid'])/'stat'
 return Path('/proc/sys/kernel/random/boot_id').read_text().strip()==i['boot_id']and p.exists()and p.read_text().split()[21]==i['start_ticks']
def stop(i):
 if alive(i):
  os.killpg(i['pgid'],signal.SIGTERM);end=time.monotonic()+8
  while alive(i)and time.monotonic()<end:time.sleep(.05)
  if alive(i):os.killpg(i['pgid'],signal.SIGKILL)
def stage(name,args,timeout,allow_failure=False):
 assert time.monotonic()<START+7200 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT
 live=D/'live_io';live.mkdir(exist_ok=True);start=time.monotonic();wall=time.time();data=bytearray();last_checkpoint=0.
 p=subprocess.Popen([sys.executable,*args],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
 identity=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split()[21],boot_id=BOOT,command=args,timeout_s=timeout);put(live/(name+'_OWNED.json'),identity)
 print(json.dumps(dict(stage=name,started=True,pid=p.pid)),flush=True)
 try:
  selector=selectors.DefaultSelector();selector.register(p.stdout,selectors.EVENT_READ)
  while selector.get_map():
   assert time.monotonic()<start+timeout and time.time()<wall+timeout and time.monotonic()<START+7200 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT,'BACKGROUND_STAGE_DUAL_CLOCK_STOP'
   if time.monotonic()-last_checkpoint>10:
    progress=None
    if(O/'actual/ACTUAL_PROGRESS.json').exists():
     item=read(O/'actual/ACTUAL_PROGRESS.json');progress={k:item.get(k)for k in ['native','phase']}
    put(live/'BACKGROUND_PROGRESS.json',dict(unix=time.time(),stage=name,stage_elapsed_s=time.monotonic()-start,owned_process_identity=identity,actual_progress=progress,partial_not_scientific_pass=True));last_checkpoint=time.monotonic()
   for key,_ in selector.select(.2):
    block=os.read(key.fileobj.fileno(),16384)
    if not block:selector.unregister(key.fileobj);continue
    assert len(data)+len(block)<=1024**2,'BACKGROUND_CONSOLE_1MIB';data.extend(block)
  p.wait(timeout=5)
 finally:
  if p.poll()is None:
   if name=='owner'and(O/'OWNED_CHILD.json').exists():stop(read(O/'OWNED_CHILD.json'))
   stop(identity)
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:pass
  (live/(name+'.console')).write_bytes(data)
  put(live/(name+'_EXIT.json'),dict(returncode=p.poll(),wall_s=time.monotonic()-start,pid=p.pid,stage=name))
 assert allow_failure or p.returncode==0,'BACKGROUND_STAGE_FAILED:'+name
 return identity

def main():
 os.sched_setaffinity(0,{5});assert not(D/'BACKGROUND_ONCE_CLAIM.json').exists()and not(O/'PILOT_ONCE_CLAIM.json').exists()and not(O/'COMPLETION.json').exists()
 cur=read(R/'CURRENT_EXPERIMENT.json');assert cur['active_round']is None and not cur['models_now_authorized'];assert read(R/'runs/v1820_final_three_ablation_rounds/CHAIN_RESULT.json')['closed']
 original=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 for p in [R/'runs/v648_static_unknown/execution.lock',R/'runs/v1643_formal_parent_metadata/OWNER.lock']:
  with p.open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for row in read(R/'runs/v1643_formal_parent_metadata/FORMAL_LEDGER.json')['rows']:
  if row.get('closed'):
   b=read(R/'runs/v1643_formal_parent_metadata/rounds'/row['assignment_id']/'POST_ROUND_STORAGE_BARRIER.json');assert b['passed']
   for a,h in [('closed_result_path','closed_result_sha256'),('remote_proof_path','remote_proof_sha256'),('cleanup_proof_path','cleanup_proof_sha256')]:assert sha(R/b[a])==b[h]
 frozen=read(O/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items());recovery=read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and not recovery['uncovered_members']
 assert sha(R/recovery['full_remote_proof_path'])==recovery['full_remote_proof_sha256']and sha(R/recovery['index_path'])==recovery['index_sha256']
 usage=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert usage+1015*1024**2<15*1024**3
 put(D/'BACKGROUND_ONCE_CLAIM.json',dict(pid=os.getpid(),started_unix=time.time(),source_members=len(frozen),source_freeze_sha256=sha(O/'SOURCE_FREEZE.json'),all_source_SHA_verified=True,source_recovery_verified=True,prior20barriers_verified=True,allruns_bytes=usage,full_peak_bytes=usage+1015*1024**2,common_method='TEB',task='common_01',one_assignment_only=True))
 ledger=read(ROOT/'LEDGER.json');slot=next(x for x in ledger['slots']if x['method']=='TEB'and x['task_id']=='common_01');assert not slot['registered'];slot.update(registered=True,status='ACTIVE_ONCE_REGISTERED_FULL_TASK_ATTEMPT',source_version=str(O.relative_to(R)),source_freeze_sha256=sha(O/'SOURCE_FREEZE.json'));ledger.update(registered=sum(bool(x['registered'])for x in ledger['slots']),unexecuted=120-sum(bool(x['registered'])for x in ledger['slots']));put(ROOT/'LEDGER.json',ledger)
 result=dict(closed=False,pipeline_passed=False,common_method='TEB',task='common_01',no_automatic_successor=True,scientific_navigation_passed=None)
 try:
  stage('owner',[str(R/'experiments/v1834_teb_common_entry_gate/owner.py')],5500,allow_failure=True);assert read(O/'COMPLETION.json')['closed']
  stage('review',[str(C/'review.py')],120)
  result['scientific_navigation_passed']=read(O/'RUNTIME_CLOSED_REVIEW.json')['qualified_whole_navigation_passed']
  # Exact late helper source copy is a member of this first runtime archive.
  H=R/'runs/v1836_teb_common_runtime_recovery/helper';H.mkdir()
  for p in C.iterdir():
   if p.is_file():(H/p.name).write_bytes(p.read_bytes())
  stage('archive',[str(R/'experiments/v1836_teb_common_runtime_recovery/finalize.py')],180)
  stage('source_proof',[str(R/'experiments/v1836_teb_common_runtime_recovery/deliver.py'),'--source-sync'],30)
  delivery=stage('deliver',[str(R/'experiments/v1836_teb_common_runtime_recovery/deliver.py')],650)
  stage('barrier',[str(C/'review.py'),'--barrier'],120)
  assert read(O/'POST_ROUND_STORAGE_BARRIER.json')['passed'];result['pipeline_passed']=True
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc(),all_unverified_originals_retained=True)
 finally:
  result.update(closed=True,wall_s=time.monotonic()-START,closed_unix=time.time());put(D/'BACKGROUND_RESULT.json',result)
  current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='COMMON_TEB_CLOSED_WAITING_USER_REVIEW',automatic_next_round=False,manual_review_after_every_round=True,latest_background_result=str((D/'BACKGROUND_RESULT.json').relative_to(R)),next_experiment='Review first shared TEB outcome and unresolved baseline adapters; no automatic task retry or successor');put(R/'CURRENT_EXPERIMENT.json',current)
 print(json.dumps(result));return 0 if result['pipeline_passed']else 1
if __name__=='__main__':raise SystemExit(main())
