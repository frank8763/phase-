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
 assert time.monotonic()<START+9000 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT
 live=D/'live_io';live.mkdir(exist_ok=True);start=time.monotonic();wall=time.time();data=bytearray();last_checkpoint=0.
 p=subprocess.Popen([sys.executable,*args],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
 identity=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split()[21],boot_id=BOOT,command=args,timeout_s=timeout);put(live/(name+'_OWNED.json'),identity)
 print(json.dumps(dict(stage=name,started=True,pid=p.pid)),flush=True)
 try:
  selector=selectors.DefaultSelector();selector.register(p.stdout,selectors.EVENT_READ)
  while selector.get_map():
   assert time.monotonic()<start+timeout and time.time()<wall+timeout and time.monotonic()<START+9000 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT,'BACKGROUND_STAGE_DUAL_CLOCK_STOP'
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
   if name=='source'and(O/'SOURCE_OWNED_CHILD.json').exists():stop(read(O/'SOURCE_OWNED_CHILD.json'))
   if name=='owner'and(O/'OWNED_CHILD.json').exists():stop(read(O/'OWNED_CHILD.json'))
   stop(identity)
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:pass
  (live/(name+'.console')).write_bytes(data)
  put(live/(name+'_EXIT.json'),dict(returncode=p.poll(),wall_s=time.monotonic()-start,pid=p.pid,stage=name))
 assert allow_failure or p.returncode==0,'BACKGROUND_STAGE_FAILED:'+name
 return identity

def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 assert not(D/'LAUNCH_ONCE_CLAIM.json').exists()and not(O/'SOURCE_QUALIFICATION.json').exists()and not(O/'PILOT_ONCE_CLAIM.json').exists()
 current=read(R/'CURRENT_EXPERIMENT.json');assert current['active_round']is None and not current['models_now_authorized']
 assert read(R/'runs/v1829_teb_common_exact_bridge/POST_ROUND_STORAGE_BARRIER.json')['passed']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 stat=Path('/proc',str(os.getpid()),'stat').read_text().split(') ',1)[1].split()
 put(D/'LAUNCH_ONCE_CLAIM.json',dict(pid=os.getpid(),pgid=os.getpgid(0),start_ticks=stat[19],boot_id=BOOT,unix=time.time(),maximum_pipeline_s=9000,models_now_authorized=False,one_common_task_only=True,no_chat_supervision=True,no_automatic_repairs_or_successor=True))
 result=dict(closed=False,passed=False,actual_launched=False,source_passed=False,first_error=None,no_automatic_successor=True)
 try:
  stage('source',[str(R/'experiments/v1834_teb_common_entry_gate/source_owner.py')],200)
  assert read(O/'SOURCE_QUALIFICATION.json')['passed']and read(O/'SOURCE_OUTER_CLOSED.json')['passed'];result['source_passed']=True
  stage('archive',[str(R/'experiments/v1835_teb_common_source_recovery/finalize.py')],180)
  assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R).strip(),'PREEXISTING_STAGING_NOT_TOUCHED'
  paths=['experiments/v1834_teb_common_entry_gate','experiments/v1835_teb_common_source_recovery','experiments/v1836_teb_common_runtime_recovery','experiments/v1837_teb_common_single','experiments/v1838_teb_background_launch','docs/TEB_COMMON_PHASE_V1834_REPORT.md']
  subprocess.run(['git','add',*paths],cwd=R,check=True,timeout=30)
  metadata=[str((O/n).relative_to(R))for n in ['SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','ROUND_AUTHORIZATION.json']]
  subprocess.run(['git','add','-f',*metadata],cwd=R,check=True,timeout=30)
  commit=subprocess.run(['git','commit','-m','Bind original TEB common01 persistent current worker with authority-first entry'],cwd=R,capture_output=True,text=True,timeout=30)
  put(D/'SOURCE_COMMIT_RESULT.json',dict(returncode=commit.returncode,stdout=commit.stdout,stderr=commit.stderr));assert commit.returncode==0
  stage('source_sync',[str(R/'experiments/v1835_teb_common_source_recovery/deliver.py'),'--source-sync'],45)
  assert read(R/'runs/v1835_teb_common_source_recovery/SOURCE_SYNC_RESULT.json')['remote_verified']
  stage('source_deliver',[str(R/'experiments/v1835_teb_common_source_recovery/deliver.py')],650)
  stage('source_chain',[str(R/'experiments/v1835_teb_common_source_recovery/chain.py')],120)
  assert read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
  stage('single_actual_wrapper',[str(R/'experiments/v1837_teb_common_single/background.py')],7300,allow_failure=True)
  wrapper=read(R/'runs/v1837_teb_common_single/BACKGROUND_RESULT.json');result.update(actual_launched=(O/'PILOT_ONCE_CLAIM.json').exists(),actual_pipeline=wrapper,passed=bool(wrapper['pipeline_passed']))
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc(),all_originals_retained=True)
 finally:
  result.update(closed=True,wall_s=time.monotonic()-START,unix=time.time(),actual_launched=(O/'PILOT_ONCE_CLAIM.json').exists());put(D/'LAUNCH_RESULT.json',result)
  current=read(R/'CURRENT_EXPERIMENT.json');current.update(latest_launch_pipeline_result=str((D/'LAUNCH_RESULT.json').relative_to(R)),background_preparation_active=False)
  if not result['actual_launched']:current.update(status='TEB_BACKGROUND_SOURCE_PIPELINE_CLOSED_BEFORE_ACTUAL',models_now_authorized=False,active_round=None)
  put(R/'CURRENT_EXPERIMENT.json',current)
 print(json.dumps(result),flush=True);return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
