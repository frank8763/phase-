"""Finite PSF then PCBF original-vehicle components, with complete close barriers."""
from pathlib import Path
import fcntl,json,os,signal,subprocess,time,traceback
from context import R,C,SOURCE as S,read,put,sha,predecessors_closed

def gone(i):
 p=Path('/proc',str(i['pid']),'stat');return not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
def decision(ready,time_available,user_stop):return'USER_STOP'if user_stop else'DEADLINE_STOP'if not time_available else'RUN'if ready else'WAIT'
def ready():
 prior=R/'runs/v2127_filter_grant_headroom'
 if not(prior/'DISPATCH_RESULT.json').exists():return False
 if not gone(read(prior/'LAUNCH_IDENTITY.json')):return False
 return predecessors_closed()
def process(label,argv,cap,*,method=None):
 folder=S/'workers';folder.mkdir(exist_ok=True);path=folder/(label+'.console');assert not path.exists()
 with path.open('xb')as log:
  p=subprocess.Popen(['taskset','-c','5','nice','-n','19','ionice','-c','3',*argv],cwd=R,env=dict(os.environ,PHASE_REPO=str(R),PHASE_FILTER_METHOD=method or'PSF',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1'),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  i=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],boot_id=BOOT,method=method);put(folder/(label+'.IDENTITY.json'),i);start=time.monotonic()
  try:
   while p.poll()is None:
    assert time.monotonic()-start<cap and time.time()<END-5 and time.monotonic()<MONO_END-5 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT
    assert path.stat().st_size<=4*1024**2 and not(S/'STOP').exists();time.sleep(.5)
   return p.returncode
  finally:
   if p.poll()is None:
    assert not gone(i);os.killpg(i['pgid'],signal.SIGTERM)
    try:p.wait(timeout=20)
    except subprocess.TimeoutExpired:os.killpg(i['pgid'],signal.SIGKILL);p.wait(timeout=5)
   if method is not None:
    owned=S/'components'/method/'OWNED_CHILD.json'
    if owned.exists():
     child=read(owned)
     if not gone(child):
      assert child['boot_id']==BOOT and os.getpgid(child['pid'])==child['pgid'];os.killpg(child['pgid'],signal.SIGTERM);until=time.monotonic()+20
      while not gone(child)and time.monotonic()<until:time.sleep(.2)
      if not gone(child):os.killpg(child['pgid'],signal.SIGKILL)
def actual_bytes(folder):return sum(p.stat().st_blocks*512 for p in folder.rglob('*')if p.is_file()and not p.is_symlink())
def runtime_review(method):
 O=S/'components'/method;m=read(O/'COMPLETION.json');assert m['closed']and m['all_source_SHA_after_child']and m['actual_native']>0 and m['actual_native']==m['own_replay_native']and m['independent_audit']['passed']and not m['machine_secondary_errors']
 error=m['machine_first_error'];allowed=['FILTER_CURRENT_NUMERICAL_OR_HARD_GEOMETRY_REFUSED','FILTER_CURRENT_CYCLE_COMPLETE_STOP_REFUSED','FILTER_CURRENT_5_PLUS2200_REFUSED','FILTER_CURRENT_MEASURED_COMPLETE_STOP_REFUSED','NOMINAL_']
 if not m['passed']:assert error and any(x in error['error']for x in allowed),'TECHNICAL_COMPONENT_FAILURE_NO_NEXT_MODEL'
 return m

def main():
 global END,MONO_END,BOOT
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));lock=(S/'dispatcher.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not(S/'DISPATCH_ONCE.json').exists()and read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed'];files=read(S/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items())
 auth=read(S/'AUTHORIZATION.json');END=auth['absolute_end_unix'];BOOT=Path('/proc/sys/kernel/random/boot_id').read_text().strip();MONO_END=time.monotonic()+END-time.time();put(S/'DISPATCH_ONCE.json',dict(pid=os.getpid(),unix=time.time(),boot_id=BOOT,models_authorized=False,maximum_component_attempts=2,fixed_order=auth['fixed_order']))
 result=dict(closed=False,new_formal_tasks=0,components=[],original_active_sources_unchanged=True);last=0.
 try:
  while True:
   assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT and time.monotonic()<MONO_END
   state=decision(ready(),min(END-time.time(),MONO_END-time.monotonic())>auth['required_reserve_before_new_component_s'],(S/'STOP').exists())
   if time.monotonic()-last>=900:put(S/'RUNNING_CHECKPOINT.json',dict(stage=state,unix=time.time(),models_authorized=False,waiting_for='PRIEST_COMPLETE_EVIDENCE_AND_QUIESCENCE',fixed_order=auth['fixed_order']));last=time.monotonic()
   if state!='WAIT':break
   time.sleep(2.)
  assert state=='RUN',state
  b=read(S/'BASELINE_DRAFT.json');closed_bytes=0
  for method in auth['fixed_order']:
   assert min(END-time.time(),MONO_END-time.monotonic())>auth['required_reserve_before_new_component_s']and not(S/'STOP').exists()
   assert closed_bytes<=b['retained_future_closed_bytes'],'FILTER_RETAINED_EVIDENCE_UPPER_EXHAUSTED'
   assert all(sha(R/n)==h for n,h in files.items());O=S/'components'/method
   assert all(not(O/n).exists()for n in['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','COMPLETION.json','actual/RESULT.json'])
   assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
   for n in['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
    with(R/n).open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
   measured=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')],timeout=20).split()[0]);assert measured<=b['all_prior_evidence_upper_bytes']+b['preparation_bytes']+b['metadata_bytes']+closed_bytes,'QUIESCENT_PRIOR_STORAGE_UPPER_EXCEEDED'
   put(S/('PRECLAIM_'+method+'.json'),dict(passed=True,allruns_bytes=measured,closed_filter_evidence_bytes=closed_bytes,method=method,source_freeze_sha256=sha(S/'SOURCE_FREEZE.json'),unix=time.time()))
   process(method+'_owner',['/usr/bin/python3','-B',str(C/'owner.py')],5425,method=method)
   # Even failures get their original close record and remote recovery before deciding whether to advance.
   m=read(O/'COMPLETION.json');assert m['closed']
   for label,args,cap in[(method+'_archive',['archive',method],120),(method+'_ref',['ref',method],15),(method+'_delivery',['deliver',method],620)]:assert process(label,['/usr/bin/python3','-B',str(C/'evidence.py'),*args],cap,method=method)==0,label
   T=S/'runtime_archives'/method;assert read(T/'FULL_REMOTE_VERIFIED.json')['passed']and read(T/'TRANSPORT_CLEANUP.json')['passed']
   put(O/'POST_COMPONENT_STORAGE_BARRIER.json',dict(passed=True,component_passed=m['passed'],whole_navigation_passed=False,formal_tasks=0,runtime_proof_sha256=sha(T/'FULL_REMOTE_VERIFIED.json'),source_commit=read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['source_commit']))
   result['components'].append(dict(method=method,passed=m['passed'],actual_native=m.get('actual_native'),own_replay_native=m.get('own_replay_native'),evidence_closed=True));put(S/'RUNNING_CHECKPOINT.json',dict(stage='COMPONENT_CLOSED',unix=time.time(),components=result['components'],whole_navigation_passed=False))
   runtime_review(method);closed_bytes+=actual_bytes(O/'actual')
  result['finite_queue_completed']=True
 except BaseException as x:result.update(error=repr(x),traceback=traceback.format_exc(),finite_queue_completed=False)
 result.update(closed=True,unix=time.time(),models_authorized=False);put(S/'DISPATCH_RESULT.json',result);print(json.dumps(result))
if __name__=='__main__':main()
