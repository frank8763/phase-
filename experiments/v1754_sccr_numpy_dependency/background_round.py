"""Detached single original SCCR fixed-input query and evidence closure; no successor."""
import fcntl,json,os,signal,subprocess,sys,time,traceback
from round_common import *
BOOT=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
BEGIN=time.monotonic();WALL=time.time();CHILD=None

def guard():
 assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT and time.monotonic()<BEGIN+5400 and time.time()<WALL+5400,'ROUND_BOOT_DUAL_CLOCK'
def run(label,args,timeout):
 global CHILD
 guard();path=O/(label+'.console');assert not path.exists()
 with path.open('xb')as f:
  CHILD=subprocess.Popen(['taskset','-c','5','nice','-n','19',sys.executable,*args],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'),stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True)
  identity=dict(pid=CHILD.pid,pgid=os.getpgid(CHILD.pid),start_ticks=Path('/proc',str(CHILD.pid),'stat').read_text().split()[21],boot_id=BOOT)
  put(O/(label+'_OWNED_CHILD.json'),identity);start=time.monotonic()
  while CHILD.poll() is None:
   guard();assert time.monotonic()<start+timeout,'STAGE_WALL_CAP:'+label
   assert path.stat().st_size<=512*1024,'STAGE_CONSOLE_CAP'
   put(O/'RUNNING_CHECKPOINT.json',dict(stage=label,unix=time.time(),pid=CHILD.pid,models=0,physical_native=0,original_query_counts_pending=True,automatic_next_round=False));time.sleep(.5)
  code=CHILD.returncode;put(O/(label+'_WORKER_EXIT.json'),dict(returncode=code,identity=identity,observed_unix=time.time()))
  CHILD=None;assert code==0,'STAGE_FAILED:'+label
 guard()
def helper(version,kind,name):return str(R/f'experiments/v{version}_sccr_query_{kind}_recovery'/name)
def chain():
 D=R/'runs/v1755_sccr_query_source_recovery';prior=R/'runs/v1751_sccr_original_query';frozen=read(O/'SOURCE_FREEZE.json')['files'];old=read(prior/'SOURCE_FREEZE.json')['files'];idx=read(D/'ARCHIVE_INDEX.json');members={v['path']:v.get('sha256')for v in idx['files']};delta={n:h for n,h in frozen.items()if old.get(n)!=h};missing=[n for n,h in delta.items()if members.get(n)!=h];assert not missing and read(D/'FULL_REMOTE_VERIFIED.json')['passed']and read(D/'TRANSPORT_CLEANUP.json')['passed']and all(sha(R/n)==h for n,h in frozen.items())
 put(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json',dict(passed=True,all_frozen_members_remote_chain_covered=True,source_members=len(frozen),inherited_members=len(frozen)-len(delta),new_delta_members=len(delta),uncovered_members=missing,source_commit=read(D/'SOURCE_SYNC_RESULT.json')['head'],proof_paths_SHA256={str(p.relative_to(R)):sha(p)for p in [D/'ARCHIVE_INDEX.json',D/'FULL_REMOTE_VERIFIED.json',D/'TRANSPORT_CLEANUP.json',prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json']},late_outside_source_archive=True,physical_admission=False))
def close_runtime():
 D=R/'runs/v1756_sccr_query_runtime_recovery';src=R/'runs/v1755_sccr_query_source_recovery'
 run('runtime_archive',[helper(1756,'runtime','finalize.py')],180)
 put(D/'SOURCE_SYNC_RESULT.json',dict(head=read(src/'SOURCE_SYNC_RESULT.json')['head'],remote_verified=True,reused_exact_original_source_sync=True,original_source_proof_path=str((src/'SOURCE_SYNC_RESULT.json').relative_to(R)),original_source_proof_sha256=sha(src/'SOURCE_SYNC_RESULT.json'),push_executed=False,ref_executed=False,models=0))
 run('runtime_delivery',[helper(1756,'runtime','deliver.py')],630)
 assert read(D/'FULL_REMOTE_VERIFIED.json')['passed']and read(D/'TRANSPORT_CLEANUP.json')['passed']
 paths=[O/'QUERY_RESULT.json',O/'QUERY_OUTER_CLOSED.json',O/'CURRENT_SOURCE_REMOTE_RECOVERY.json',D/'FULL_REMOTE_VERIFIED.json',D/'TRANSPORT_CLEANUP.json',O/'runtime_delivery_WORKER_EXIT.json']
 put(O/'POST_ROUND_STORAGE_BARRIER.json',dict(passed=True,models_authorized=False,all_originals_retained=True,no_automatic_next_round=True,original_review=True,proof_paths_SHA256={str(p.relative_to(R)):sha(p)for p in paths},late_outside_archive=True))
def cleanup_owned(original):
 global CHILD
 if CHILD is not None and CHILD.poll() is None:
  os.killpg(CHILD.pid,signal.SIGTERM)
  try:CHILD.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(CHILD.pid,signal.SIGKILL);CHILD.wait(timeout=5)
 for stage in ['SOURCE','QUERY']:
  p=O/(stage+'_OWNED_CHILD.json')
  if p.exists():
   x=read(p);s=Path('/proc',str(x['pid']),'stat')
   if s.exists()and x['boot_id']==BOOT and s.read_text().split()[21]==x['start_ticks']:
    os.killpg(x['pgid'],signal.SIGTERM);end=time.monotonic()+5
    while s.exists()and time.monotonic()<end:time.sleep(.05)
    if s.exists()and s.read_text().split()[21]==x['start_ticks']:os.killpg(x['pgid'],signal.SIGKILL)
 with (R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 (R/'REVIEW_PENDING').write_bytes(original)
def main():
 os.sched_setaffinity(0,{5});assert not(O/'BACKGROUND_ONCE_CLAIM.json').exists()
 current=read(R/'CURRENT_EXPERIMENT.json');assert current['active_round']is None and not current['models_now_authorized']and current.get('active_source_round')is None
 original=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 prior_barrier=read(R/'runs/v1751_sccr_original_query/POST_ROUND_STORAGE_BARRIER.json');assert prior_barrier['passed'] and all(sha(R/n)==h for n,h in prior_barrier['proof_paths_SHA256'].items())
 usage=load('v1751_existing_usage',R/'experiments/v1518_compact_parent_control/common.py').usage();assert usage+(4+8+240+32+512)*1024**2<15*1024**3
 put(O/'BACKGROUND_ONCE_CLAIM.json',dict(pid=os.getpid(),pgid=os.getpgid(0),start_ticks=Path('/proc/self/stat').read_text().split()[21],boot_id=BOOT,started_unix=WALL,started_monotonic=BEGIN,root_deadline_unix=WALL+5400,normal_deadline_unix=WALL+4200,root_deadline_monotonic=BEGIN+5400,allruns_bytes=usage,maximum_reserved_peak_bytes=usage+(4+8+240+32+512)*1024**2,one_fixed_synthetic_query=True,next_round_requires_new_user_command=True))
 current.update(status='BACKGROUND_SCCR_FIXED_INPUT_QUERY',active_source_round=C.name,models_now_authorized=False,automatic_next_round=False,manual_review_after_every_round=True,next_step='One synthetic original SCCR geometric query; wait user review after closure. No whole navigation or successor.');put(R/'CURRENT_EXPERIMENT.json',current)
 result=dict(passed=False,closed=False,models=0,physical_native=0,replay_native=0,whole_navigation_passed=None,synthetic_software_fixture=True,real_measured_receipt=False,automatic_next_round=False)
 try:
  run('source_owner',[str(C/'owner.py')],180)
  run('source_archive',[helper(1755,'source','finalize.py')],180)
  run('source_sync',[helper(1755,'source','deliver.py'),'--source-sync'],45)
  run('source_delivery',[helper(1755,'source','deliver.py')],630);chain()
  guard();put(O/'CURRENT_QUERY_ADMISSION.json',dict(query_authorized=True,physical_admission=False,source_freeze_sha256=sha(O/'SOURCE_FREEZE.json'),boot_id=BOOT,deadline_unix=min(time.time()+150,WALL+4200),deadline_monotonic=min(time.monotonic()+150,BEGIN+4200),synthetic_fixture_only=True,maximum_original_queries=1))
  try:run('query_owner',[str(C/'owner.py'),'--query'],180)
  except BaseException as error:result['query_owner_error']=repr(error)
  assert read(O/'QUERY_OUTER_CLOSED.json')['closed']and read(O/'QUERY_RESULT.json')['closed'],'QUERY_MACHINE_RECORD_MISSING'
  result['query_result']=read(O/'QUERY_RESULT.json');result['query_outer_closed']=read(O/'QUERY_OUTER_CLOSED.json')
  report=R/'docs/SCCR_NUMPY_DEPENDENCY_V1754_REPORT.md'
  report.write_text('# SCCR single fixed-input original query V1751\n\n'+json.dumps(result['query_result'],indent=2)+'\n\nArtificial software fixture only: not measured data, navigation, independent task or benchmark score. Original geometric core and parameters unchanged. No plant/model/physics/replay/SAC. No retry or successor; all original result and failure evidence retained. Source and runtime remote recovery are separate; late closure/barrier metadata outside archives.\n')
  close_runtime();result.update(passed=bool(result['query_result']['passed']and result['query_outer_closed']['passed']),pipeline_complete=True,remote_evidence_closed=True)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  try:cleanup_owned(original);result['review_restored']=sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
  except BaseException as error:result['safety_close_error']=repr(error)
  result.update(closed=True,wall_s=time.monotonic()-BEGIN);put(O/'BACKGROUND_RESULT.json',result)
  current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='WAITING_USER_REVIEW_AFTER_SCCR_FIXED_QUERY',active_source_round=None,models_now_authorized=False,automatic_next_round=False,latest_background_result=str((O/'BACKGROUND_RESULT.json').relative_to(R)),next_step='Wait user review and new command; original SCCR whole navigation remains unqualified.');put(R/'CURRENT_EXPERIMENT.json',current)
  with (R/'RESEARCH_STATUS.md').open('a')as f:f.write('\nV1754 NumPy dependency single synthetic original SCCR query closed: pipeline='+str(result.get('pipeline_complete',False))+'; interface_pass='+str(result['passed'])+'; see '+str((O/'BACKGROUND_RESULT.json').relative_to(R))+'. Artificial software fixture, not measured navigation/benchmark;0plant-physics-replay;no auto successor.\n')
 print(json.dumps(dict(passed=result['passed'],closed=True,pipeline=result.get('pipeline_complete',False))));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
