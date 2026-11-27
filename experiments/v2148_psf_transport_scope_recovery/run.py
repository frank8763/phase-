"""One original qualified V2147 owner, then own exact evidence transport."""
from transport import R,C,S,OLD,ROOT,D,read,put,sha
import os,sys,fcntl,subprocess,time,signal,traceback
from pathlib import Path
BOOT=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
def gone(i):
 p=Path('/proc',str(i['pid']),'stat');return not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
def process(label,argv,cap,owner=False):
 folder=S/'workers';folder.mkdir(exist_ok=True);path=folder/(label+'.console');assert not path.exists()
 with path.open('xb')as log:
  p=subprocess.Popen(['taskset','-c','5','nice','-n','19','ionice','-c','3',*argv],cwd=R,env=dict(os.environ,PHASE_REPO=str(R),PHASE_FILTER_METHOD='PSF',PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  i=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],boot_id=BOOT,scope=label);put(folder/(label+'.IDENTITY.json'),i);start=time.monotonic();last=start
  try:
   while p.poll()is None:
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT and time.monotonic()-start<cap and time.time()<END-5 and time.monotonic()<MONO_END-5 and not(S/'STOP').exists()and path.stat().st_size<4*1024**2,'BOUNDED_OWNER_OR_IO_STOP'
    if time.monotonic()-last>=900:put(S/'RUNNING_CHECKPOINT.json',dict(stage=label,unix=time.time(),child=i,scientific_passed=None));last=time.monotonic()
    time.sleep(.5)
   return p.returncode
  finally:
   if p.poll()is None:
    assert not gone(i);os.killpg(i['pgid'],signal.SIGTERM)
    try:p.wait(timeout=20)
    except subprocess.TimeoutExpired:os.killpg(i['pgid'],signal.SIGKILL);p.wait(timeout=5)
   if owner and(ROOT/'components/PSF/OWNED_CHILD.json').exists():
    child=read(ROOT/'components/PSF/OWNED_CHILD.json')
    if not gone(child):
     assert child['boot_id']==BOOT and os.getpgid(child['pid'])==child['pgid'];os.killpg(child['pgid'],signal.SIGTERM);stop=time.monotonic()+20
     while not gone(child)and time.monotonic()<stop:time.sleep(.2)
     if not gone(child):os.killpg(child['pgid'],signal.SIGKILL)
def current(active):
 p=R/'CURRENT_EXPERIMENT.json';v=read(p);v.update(active_round='v2147_psf_full_route_development'if active else None,models_now_authorized=active,current_original_vehicle_model_jobs=1 if active else 0,status='PSF_FULL_ROUTE_DEVELOPMENT_RUNNING'if active else'PSF_FULL_ROUTE_OWNER_CLOSED_EVIDENCE_CLOSURE',latest_psf_fullroute_checkpoint=str((S/'RUNNING_CHECKPOINT.json').relative_to(R)));put(p,v)
def main():
 global END,MONO_END
 assert os.sched_getaffinity(0)=={5};lock=(S/'dispatcher.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not(S/'DISPATCH_ONCE.json').exists()and read(S/'SOURCE_CHAIN_CLOSED.json')['passed']and read(ROOT/'POST_SOURCE_STORAGE_BARRIER.json')['passed']
 index={r['path']:r for r in read(D/'ARCHIVE_INDEX.json')['files']}
 for p in C.iterdir():
  if p.is_file():assert index[str(p.relative_to(R))]['sha256']==sha(p),'LATE_HELPER_NOT_RECOVERED'
 files=read(ROOT/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items())
 import context
 assert context.C==OLD;context.predecessors_closed()
 from reserved_census import admission
 admission();auth=read(ROOT/'AUTHORIZATION.json');END=auth['absolute_end_unix'];MONO_END=time.monotonic()+END-time.time();assert END-time.time()>6900
 o=ROOT/'components/PSF';assert all(not(o/n).exists()for n in ['PILOT_ONCE_CLAIM.json','OWNED_CHILD.json','COMPLETION.json','actual/RESULT.json'])
 for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  with(R/n).open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 b=read(ROOT/'BASELINE_DRAFT.json');measured=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')],timeout=20).split()[0]);assert measured<=b['all_prior_evidence_upper_bytes']+b['preparation_bytes']+b['metadata_bytes']
 put(S/'DISPATCH_ONCE.json',dict(pid=os.getpid(),unix=time.time(),models_authorized=False,fixed_order=['PSF'],original_owner_entry_unchanged=True,allruns_preclaim_bytes=measured));v=dict(closed=False,passed=False,formal_tasks=0,components=[])
 try:
  current(True);code=process('PSF_owner',['/usr/bin/python3','-B',str(OLD/'owner.py')],5425,True)
  current(False);m=read(o/'COMPLETION.json');assert m['closed']
  for label,args,cap in [('runtime_archive',['archive','PSF'],150),('runtime_ref',['ref','PSF'],15),('runtime_deliver',['deliver','PSF'],620)]:assert process(label,['/usr/bin/python3','-B',str(C/'transport.py'),*args],cap)==0,label
  d=S/'runtime_archives/PSF';assert read(d/'FULL_REMOTE_VERIFIED.json')['passed']and read(d/'TRANSPORT_CLEANUP.json')['passed']
  put(o/'POST_COMPONENT_STORAGE_BARRIER.json',dict(passed=True,component_passed=m['passed'],whole_navigation_passed=m['whole_navigation_passed'],formal_tasks=0,runtime_proof_path=str((d/'FULL_REMOTE_VERIFIED.json').relative_to(R)),runtime_proof_sha256=sha(d/'FULL_REMOTE_VERIFIED.json'),source_commit=read(ROOT/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['source_commit']))
  v.update(passed=True,finite_queue_completed=True,model_case_passed=m['passed'],whole_navigation_passed=m['whole_navigation_passed'],actual_native=m['actual_native'],own_replay_native=m['own_replay_native'],components=[dict(method='PSF',passed=m['passed'],evidence_closed=True)],owner_returncode=code)
 except BaseException as e:v.update(error=repr(e),traceback=traceback.format_exc(),finite_queue_completed=False)
 finally:current(False)
 v.update(closed=True,finished_unix=time.time(),models_authorized=False);put(S/'DISPATCH_RESULT.json',v);print(__import__('json').dumps(v))
if __name__=='__main__':main()
