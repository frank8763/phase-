"""Five original unclaimed tasks with compiled premutation-only I/O recovery."""
from pathlib import Path
import fcntl,os,subprocess,signal,time,json,traceback
import evidence as e
R=e.R;C=e.C;S=e.ROOT;STUDY=R/'runs/v2095_svg_common_full_route'
def gone(i):
 p=Path('/proc',str(i['pid']),'stat');return not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
def stop(p,i):
 if p.poll()is not None:return
 assert not gone(i);os.killpg(i['pgid'],signal.SIGTERM)
 try:p.wait(timeout=20)
 except subprocess.TimeoutExpired:os.killpg(i['pgid'],signal.SIGKILL);p.wait(timeout=5)
def checkpoint(stage,rid=None):
 p=STUDY/'rounds'/rid/'actual/NAVIGATION_PROGRESS.json'if rid else None
 e.put(S/'RUNNING_CHECKPOINT.json',dict(unix=time.time(),stage=stage,assignment=rid,deadline_unix=END,actual_partial=e.read(p)if p and p.exists()else None,whole_navigation_passed=None,not_a_scientific_PASS=True))
def run_process(label,argv,cap,*,env=None,cpu=5,rid=None):
 folder=S/'workers';folder.mkdir(exist_ok=True);path=folder/(label+'.console');assert not path.exists();p=None;i=None;start=time.monotonic();last=start
 try:
  with path.open('xb')as log:
   p=subprocess.Popen(['taskset','-c',str(cpu),'nice','-n','19','ionice','-c','3',*argv],cwd=R,env=dict(os.environ,PHASE_REPO=str(R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',**(env or{})),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   i=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],label=label,CPU=cpu,unix=time.time());e.put(folder/(label+'.IDENTITY.json'),i)
   while p.poll()is None:
    assert time.monotonic()-start<cap and time.time()<END-5 and time.monotonic()<MONO_END-5 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT,'FINITE_QUEUE_OR_STAGE_STOP'
    assert path.stat().st_size<=4*1024**2,'CONSOLE_4MIB_STOP'
    if time.monotonic()-last>=900:checkpoint(label,rid);last=time.monotonic()
    if(S/'STOP').exists():raise RuntimeError('USER_STOP')
    time.sleep(.5)
   return p.returncode
 finally:
  if p is not None:stop(p,i)
  if rid:
   child=STUDY/'rounds'/rid/'OWNED_CHILD.json'
   if child.exists():
    j=e.read(child)
    if not gone(j):
     assert j['boot_id']==BOOT and os.getpgid(j['pid'])==j['pgid'];os.killpg(j['pgid'],signal.SIGTERM);until=time.monotonic()+20
     while not gone(j)and time.monotonic()<until:time.sleep(.2)
     if not gone(j):os.killpg(j['pgid'],signal.SIGKILL)
def premutation_failed(folder):
 p=folder/'RESULT.json'
 if not p.exists():return False
 d=e.read(p);receipts=[e.read(p)for p in(folder/'http_receipts').glob('*.json')]
 return d.get('closed')and not d.get('passed')and len(receipts)==6 and all(x['call']==1 and x['method']=='GET'and not x['passed']for x in receipts)
def backoff(seconds,rid):
 end=time.monotonic()+seconds;checkpoint('PREMUTATION_METADATA_BACKOFF',rid)
 while time.monotonic()<end:
  assert time.time()<END-620 and time.monotonic()<MONO_END-620 and not(S/'STOP').exists(),'BOUNDED_METADATA_WAIT_STOP'
  time.sleep(min(.5,end-time.monotonic()))
def close_case(rid):
 O=STUDY/'rounds'/rid;T=S/'runtime_archives'/rid;report=S/'round_reports'/rid;report.mkdir(parents=True,exist_ok=True)
 m=e.read(O/'COMPLETION.json');e.put(report/'BEFORE_ARCHIVE.json',dict(formal_task_passed=m['passed'],scientific_primary=m.get('machine_first_error'),scientific_secondary=m.get('machine_secondary_errors'),formal_tasks=1))
 for stage,args,cap in [('archive',['archive',rid],120),('ref',['ref',rid],15)]:
  assert run_process(rid+'_'+stage,['/usr/bin/python3','-B',str(C/'evidence.py'),*args],cap)==0,'ARCHIVE_OR_REF_FAILED:'+stage
 code=1
 for episode,delay in enumerate([0,30,120]):
  if episode:
   previous=T/('remote_delivery'if episode==1 else'remote_delivery_retry_1')
   assert premutation_failed(previous),'NO_RETRY_AFTER_UNCERTAIN_OR_LATER_STAGE_MUTATION'
   backoff(delay,rid)
  code=run_process(rid+'_remote_'+str(episode),['/usr/bin/python3','-B',str(C/'evidence.py'),'deliver',rid],620,env=dict(PHASE_TRANSFER_EPISODE=str(episode)))
  if code==0:break
 assert code==0 and e.read(T/'FULL_REMOTE_VERIFIED.json')['passed']and e.read(T/'TRANSPORT_CLEANUP.json')['passed'],'RUNTIME_FULL_REMOTE_BARRIER_FAILED'
 paths=[O/'COMPLETION.json',O/'actual/RESULT.json',O/'FORMAL_CLOSED_EVENT.json',T/'ARCHIVE_INDEX.json',T/'FULL_REMOTE_VERIFIED.json',T/'TRANSPORT_CLEANUP.json']
 e.put(O/'POST_ROUND_STORAGE_BARRIER.json',dict(passed=True,formal_task_passed=m['passed'],whole_navigation_passed=m['whole_navigation_passed'],formal_common_tasks=1,all_originals_remote_verified_before_cache_cleanup=True,models_authorized=False,proof_paths_SHA256={str(p.relative_to(R)):e.sha(p)for p in paths},runtime_source_root=str(S.relative_to(R))))
 import closed_cache
 cache=closed_cache.retire(rid);event=e.read(O/'FORMAL_CLOSED_EVENT.json');e.put(report/'AFTER_CLOSE.json',dict(closed=True,method_result=m['passed'],closed_event=event,cache=cache));return event
def summary(results,why):
 registry=R/'runs/v1805_common_algorithm_registry';base=e.read(registry/'LEDGER.json');slots={(x['task_id'],x['method']):dict(x)for x in base['slots']}
 for kind in ['REGISTERED','CLOSED']:
  for p in(registry/'PARALLEL_METHOD_EVENTS').glob('*.'+kind+'.json'):
   ev=e.read(p);slots[ev['task_id'],ev['method']].update(ev)
 totals=dict(denominator=120,registered=sum(bool(x.get('registered'))for x in slots.values()),closed=sum(bool(x.get('closed'))for x in slots.values()),whole=sum(bool(x.get('qualified_success'))for x in slots.values()),unexecuted=sum(not x.get('registered')for x in slots.values()))
 e.put(S/'QUEUE_RESULT.json',dict(closed=True,stop_reason=why,transport_closed_cases=results,totals=totals,finite_queue_completed=len(results)==5,models_authorized=False,original_night_failure_retained=True,unix=time.time()))
def main():
 global END,MONO_END,BOOT
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));f=(S/'owner.lock').open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 auth=e.read(S/'AUTHORIZATION.json');END=auth['absolute_end_unix'];MONO_END=time.monotonic()+min(auth['maximum_campaign_s'],END-time.time());BOOT=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert not(S/'ONCE.json').exists()and e.read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and time.time()<END-7630
 files=e.read(S/'SOURCE_FREEZE.json')['files'];assert all(e.sha(R/n)==h for n,h in files.items())
 e.put(S/'ONCE.json',dict(pid=os.getpid(),unix=time.time(),boot_id=BOOT,deadline_unix=END,maximum_campaign_s=auth['maximum_campaign_s'],formal_maximum=5,no_repeats=True))
 results=[];why='FINITE_QUEUE_COMPLETE'
 try:
  for rid in auth['finite_formal_assignments']:
   if min(END-time.time(),MONO_END-time.monotonic())<7630:why='COMPLETE_WINDOW_AND_TRANSPORT_RESERVE_UNAVAILABLE';break
   if(S/'STOP').exists():why='USER_STOP';break
   checkpoint('PRECLAIM',rid);O=STUDY/'rounds'/rid
   assert all(not(O/n).exists()for n in ['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','COMPLETION.json','actual/RESULT.json']),'NO_DUPLICATE_CLAIM'
   assert all(e.sha(R/n)==h for n,h in files.items())
   run_process(rid+'_owner',['/usr/bin/python3','-B',str(C/'owner.py')],5425,env=dict(PHASE_COMMON_ASSIGNMENT=rid),rid=rid)
   assert e.read(O/'COMPLETION.json')['closed'],'OWNER_CLOSED_EVIDENCE_REQUIRED'
   event=close_case(rid);results.append(event);checkpoint('CASE_CLOSED',rid)
   if event['technical_censor']:why='TECHNICAL_CENSOR_AFFECTED_NUMERIC_LINE_STOPPED';break
   if not(event['qualified_success']or event['valid_finite_method_refusal']or event.get('applicability_censor')):why='UNKNOWN_SCIENTIFIC_EVENT_STOP';break
 except BaseException as error:why=repr(error);e.put(S/'CAMPAIGN_ERROR.json',dict(error=repr(error),traceback=traceback.format_exc(),new_models_authorized=False,original_evidence_retained=True))
 summary(results,why);print(json.dumps(dict(closed=True,transport_closed_cases=len(results),reason=why)))
if __name__=='__main__':main()
