"""Bounded wait for the current queue, then exactly one new component."""
from pathlib import Path
import fcntl,json,os,signal,subprocess,time,traceback
from context import R,C,SOURCE as S,O,read,put,sha,predecessors_closed
def gone(i):
 p=Path('/proc',str(i['pid']),'stat');return not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
def decision(ready,time_available,user_stop):
 return'USER_STOP'if user_stop else'DEADLINE_STOP'if not time_available else'RUN'if ready else'WAIT'
def ready():
 p=R/'runs/v2116_svg_remaining_five_source_boundary/QUEUE_RESULT.json'
 if not p.exists():return False
 assert read(p)['finite_queue_completed'],'PRIOR_QUEUE_INCOMPLETE_NO_NEW_COMPONENT'
 for root in [R/'runs/v2116_svg_remaining_five_source_boundary',R/'runs/v2119_parallel_components_release_scope']:
  identity=root/'LAUNCH_IDENTITY.json'
  if not identity.exists()or not gone(read(identity)):return False
 return predecessors_closed()
def process(label,argv,cap,*,env=None):
 folder=S/'workers';folder.mkdir(exist_ok=True);path=folder/(label+'.console');assert not path.exists()
 with path.open('xb')as log:
  p=subprocess.Popen(['taskset','-c','5','nice','-n','19','ionice','-c','3',*argv],cwd=R,env=dict(os.environ,PHASE_REPO=str(R),CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',**(env or{})),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  i=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],boot_id=BOOT);put(folder/(label+'.IDENTITY.json'),i);start=time.monotonic()
  try:
   while p.poll()is None:
    assert time.monotonic()-start<cap and time.time()<END-5 and time.monotonic()<MONO_END-5 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT,'COMPONENT_STAGE_CLOCK_STOP'
    assert path.stat().st_size<=4*1024**2 and not(S/'STOP').exists(),'COMPONENT_USER_OR_OUTPUT_STOP';time.sleep(.5)
   return p.returncode
  finally:
   if p.poll()is None:
    assert not gone(i);os.killpg(i['pgid'],signal.SIGTERM)
    try:p.wait(timeout=20)
    except subprocess.TimeoutExpired:os.killpg(i['pgid'],signal.SIGKILL);p.wait(timeout=5)
   if label=='vehicle_owner'and(O/'OWNED_CHILD.json').exists():
    c=read(O/'OWNED_CHILD.json')
    if not gone(c):
     assert c['boot_id']==BOOT and os.getpgid(c['pid'])==c['pgid'];os.killpg(c['pgid'],signal.SIGTERM);until=time.monotonic()+20
     while not gone(c)and time.monotonic()<until:time.sleep(.2)
     if not gone(c):os.killpg(c['pgid'],signal.SIGKILL)
def main():
 global END,MONO_END,BOOT
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));f=(S/'dispatcher.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not(S/'DISPATCH_ONCE.json').exists()and read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed'];files=read(S/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items())
 auth=read(S/'AUTHORIZATION.json');END=auth['absolute_end_unix'];BOOT=Path('/proc/sys/kernel/random/boot_id').read_text().strip();MONO_END=time.monotonic()+END-time.time();put(S/'DISPATCH_ONCE.json',dict(pid=os.getpid(),unix=time.time(),boot_id=BOOT,models_authorized=False,maximum_component_attempts=1))
 result=dict(closed=False,models_started=None,new_formal_tasks=0,original_SVG_queue_not_modified=True);last=0.
 try:
  while True:
   assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT and time.monotonic()<MONO_END
   state=decision(ready(),time.time()<auth['latest_component_start_unix']and min(END-time.time(),MONO_END-time.monotonic())>6900,(S/'STOP').exists())
   if time.monotonic()-last>=900:
    put(S/'RUNNING_CHECKPOINT.json',dict(stage=state,unix=time.time(),models_authorized=False,waiting_for='V2116_finite_queue_and_storage_barriers',latest_start_unix=auth['latest_component_start_unix']));last=time.monotonic()
   if state!='WAIT':break
   time.sleep(2.)
  assert state=='RUN',state
  assert all(sha(R/n)==h for n,h in files.items())and all(not(O/n).exists()for n in ['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','COMPLETION.json','actual/RESULT.json'])
  assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
  for name in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
   with(R/name).open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  b=read(S/'BASELINE_DRAFT.json');measured=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')],timeout=20).split()[0]);assert measured<=b['all_prior_evidence_upper_bytes']+b['preparation_bytes']+b['metadata_bytes'],'QUIESCENT_PRIOR_STORAGE_UPPER_EXCEEDED'
  put(S/'ACTUAL_START_PRECHECK.json',dict(passed=True,allruns_bytes=measured,prior_queue_result_sha256=sha(R/'runs/v2116_svg_remaining_five_source_boundary/QUEUE_RESULT.json'),source_freeze_sha256=sha(S/'SOURCE_FREEZE.json'),unix=time.time(),no_duplicate_prior=True))
  process('vehicle_owner',['/usr/bin/python3','-B',str(C/'owner.py')],5425)
  m=read(O/'COMPLETION.json');assert m['closed'];result.update(models_started=m.get('canonical_vehicle_initializations'),actual_native=m.get('actual_native'),own_replay_native=m.get('own_replay_native'),vehicle_component_passed=m['passed'],whole_navigation_passed=False)
  put(S/'COMPLETION.json',dict(closed=True,passed=m['passed'],vehicle_result_path=str((O/'COMPLETION.json').relative_to(R)),vehicle_result_sha256=sha(O/'COMPLETION.json'),new_formal_tasks=0))
  for label,args,cap in [('runtime_archive',['archive','priest_vehicle'],120),('runtime_ref',['ref','priest_vehicle'],15),('runtime_delivery',['deliver','priest_vehicle'],620)]:assert process(label,['/usr/bin/python3','-B',str(C/'evidence.py'),*args],cap)==0,label
  T=S/'runtime_archives/priest_vehicle';assert read(T/'FULL_REMOTE_VERIFIED.json')['passed']and read(T/'TRANSPORT_CLEANUP.json')['passed']
  put(S/'POST_COMPONENT_STORAGE_BARRIER.json',dict(passed=True,component_passed=m['passed'],whole_navigation_passed=False,new_formal_tasks=0,source_commit=read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['source_commit'],runtime_proof_sha256=sha(T/'FULL_REMOTE_VERIFIED.json'),models_authorized=False));result.update(remote_and_cleanup_closed=True)
 except BaseException as x:result.update(error=repr(x),traceback=traceback.format_exc())
 result.update(closed=True,unix=time.time(),models_authorized=False);put(S/'DISPATCH_RESULT.json',result);print(json.dumps(result))
if __name__=='__main__':main()
