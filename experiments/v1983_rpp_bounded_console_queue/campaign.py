"""Finite detached RPP common02..12; model/transport closure before successor."""
import hashlib,json,os,signal,subprocess,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;ROOT=R/'runs'/C.name;H=R/'experiments/v1986_rpp_night_runtime_recovery'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 raw=json.dumps(v,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<=2*1024**2;t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def can_continue(review):return bool(review.get('closed')and (review.get('qualified_whole_navigation_passed')or review.get('valid_finite_method_negative'))and not review.get('secondary_errors')and not review.get('outer_first_error'))
def attach(row):
 S=R/row['output_root'];assert not(S/'PILOT_ONCE_CLAIM.json').exists()and not(S/'OWNED_CHILD.json').exists()and not(S/'COMPLETION.json').exists()and not(S/'actual/RESULT.json').exists()
 for name in ['SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','SOURCE_INHERITED_CHAINS.json','AUTHORIZATION.json','PRIOR_CLOSED_BARRIERS.json','LIMITS_DRAFT.json','NATIVE_DEPENDENCIES.json']:
  assert not(S/name).exists();os.link(ROOT/name,S/name);assert sha(S/name)==sha(ROOT/name)
 D=ROOT/'runtime_archives'/row['round_id'];D.mkdir(exist_ok=False);return S
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));assert not(ROOT/'CAMPAIGN_ONCE_CLAIM.json').exists();barrier=read(ROOT/'POST_SOURCE_STORAGE_BARRIER.json');assert barrier['passed']and all(sha(R/n)==h for n,h in barrier['proof_paths_SHA256'].items());plan=read(ROOT/'PLAN_LOCKED.json')['assignments'];assert len(plan)==11 and [x['round_id']for x in plan]==[f'common_{i:02d}__RPP'for i in range(2,13)]
 started=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();stat=Path('/proc/self/stat').read_text().split(') ',1)[1].split();claim=dict(pid=os.getpid(),pgid=os.getpgid(0),start_ticks=stat[19],boot_id=boot,started_unix=time.time(),max_campaign_s=79200,fixed_assignments=11,no_calendar_deadline=True,no_heartbeat=True)
 with(ROOT/'CAMPAIGN_ONCE_CLAIM.json').open('x')as f:json.dump(claim,f)
 result=dict(closed=False,pipeline_passed=False,scientific_successes=0,completed_rounds=[],unexecuted=11,first_error=None);process=None;S=None;next_checkpoint=started+900
 def guard(*a):raise TimeoutError('FINITE_NIGHT_CAMPAIGN_79200S_TECHNICAL_STOP')
 signal.signal(signal.SIGALRM,guard);signal.signal(signal.SIGTERM,guard);signal.setitimer(signal.ITIMER_REAL,79200)
 try:
  for row in plan:
   assert not(ROOT/'STOP_REQUEST.json').exists(),'HUMAN_STOP_REQUESTED'
   assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.monotonic()-started<79200
   S=attach(row);env=dict(os.environ,PHASE_RPP_ASSIGNMENT=row['round_id'],PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='');round_start=time.monotonic()
   stages=[('OWNER',C/'owner.py',[]),('REVIEW',H/'review.py',[]),('ARCHIVE',H/'finalize.py',[]),('REF_ONLY',H/'deliver.py',['--source-sync']),('REMOTE',H/'deliver.py',[]),('LOCAL_CACHE',H/'cache_cleanup.py',[]),('BARRIER',H/'review.py',['--barrier'])]
   for stage,path,args in stages:
    with(S/('pipeline_'+stage.lower()+'.console')).open('xb')as log:
     process=subprocess.Popen(['/usr/bin/python3','-B',str(path),*args],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
     put(ROOT/'CAMPAIGN_PROGRESS.json',dict(active=row['round_id'],stage=stage,stage_pid=process.pid,closed=len(result['completed_rounds']),unexecuted=11-len(result['completed_rounds'])-1,whole_navigation_passed=None,unix=time.time()))
     while process.poll()is None:
      assert time.monotonic()-round_start<7200,'ROUND_PIPELINE_7200S_TECHNICAL_STOP'
      if time.monotonic()>=next_checkpoint:
       progress=S/'actual/NAVIGATION_PROGRESS.json';put(ROOT/'RUNNING_CHECKPOINT.json',dict(unix=time.time(),active=row['round_id'],stage=stage,process_pid=process.pid,progress=read(progress)if progress.exists()else None,completed_rounds=result['completed_rounds'],scientific_navigation_passed=None));next_checkpoint=time.monotonic()+900
      time.sleep(.5)
    code=process.returncode;process=None
    if stage=='OWNER':assert read(S/'COMPLETION.json')['closed']and read(S/'COMPLETION.json')['review_restored']and read(S/'COMPLETION.json')['lock_idle']
    else:assert code==0,'PIPELINE_STAGE_FAILED:'+stage
   review=read(S/'RUNTIME_CLOSED_REVIEW.json');assert read(S/'POST_ROUND_STORAGE_BARRIER.json')['passed'];result['completed_rounds'].append(dict(round_id=row['round_id'],classification=review['classification'],actual_native=review['actual_native'],own_replay_native=review['own_replay_native'],barrier_sha256=sha(S/'POST_ROUND_STORAGE_BARRIER.json')));result['unexecuted']=11-len(result['completed_rounds']);result['scientific_successes']+=int(review['qualified_whole_navigation_passed']);put(ROOT/'CAMPAIGN_CHECKPOINT.json',result)
   assert can_continue(review),'CLOSED_TECHNICAL_SAFETY_OR_UNQUALIFIED_EVIDENCE_STOP'
  result['pipeline_passed']=True
 except BaseException as e:
  result['first_error']=dict(error=repr(e),traceback=traceback.format_exc())
  if S is not None and(S/'OWNED_CHILD.json').exists():
   identity=read(S/'OWNED_CHILD.json');p=Path('/proc',str(identity['pid']),'stat')
   if p.exists()and identity['boot_id']==boot and p.read_text().split(') ',1)[1].split()[19]==identity['start_ticks']:os.killpg(identity['pgid'],signal.SIGTERM)
  if process is not None and process.poll()is None:
   try:process.wait(timeout=45)
   except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=5)
 finally:
  signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,wall_s=time.monotonic()-started);put(ROOT/'CAMPAIGN_RESULT.json',result)
 print(json.dumps(result),flush=True);return 0 if result['pipeline_passed']else 1
if __name__=='__main__':raise SystemExit(main())
