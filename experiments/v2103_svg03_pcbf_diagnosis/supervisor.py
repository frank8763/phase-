"""One next registered SVG task plus separate, bounded PCBF diagnostic."""
import concurrent.futures,fcntl,json,os,selectors,signal,subprocess,sys,time,traceback
from pathlib import Path
import evidence as e
R=e.R;C=e.C;S=e.ROOT;RID='common_03__SVGMPPI';CASE=R/'runs/v2095_svg_common_full_route/rounds'/RID
SCI=R/'runs/v2099_svg_direct_array_scope';SCIC=R/'experiments/v2099_svg_direct_array_scope'
def put(n,x):e.put(S/n,x)
def original_source():
 recovery=e.read(SCI/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and recovery['source_commit']=='f5f466a5150501a986feb0fdec25dee0d284c88f'
 files=e.read(SCI/'SOURCE_FREEZE.json')['files'];assert all(e.sha(R/n)==h for n,h in files.items())
 return files
def predecessor():
 for p,barrier in [(R/'runs/v2095_svg_common_full_route/rounds/common_02__SVGMPPI','POST_ROUND_STORAGE_BARRIER.json'),(R/'runs/v2101_parallel_priest_vehicle','POST_COMPONENT_STORAGE_BARRIER.json')]:
  assert e.read(p/'COMPLETION.json')['closed']and e.read(p/barrier)['passed']
 assert not(CASE/'PILOT_ONCE_CLAIM.json').exists()and not(CASE/'OWNED_CHILD.json').exists()and not(CASE/'COMPLETION.json').exists()and not(CASE/'actual/RESULT.json').exists()
def stop_owned(p,i):
 if p.poll()is not None:return
 f=Path('/proc',str(i['pid']),'stat');assert f.read_text().split(') ',1)[1].split()[19]==i['start_ticks']
 os.killpg(i['pgid'],signal.SIGTERM)
 try:p.wait(timeout=20)
 except subprocess.TimeoutExpired:os.killpg(i['pgid'],signal.SIGKILL);p.wait(timeout=5)
def run_job(kind):
 child=None;identity=None;start=time.monotonic();answer=dict(closed=False,passed=False,kind=kind)
 try:
  env=dict(os.environ,PHASE_REPO=str(R),PHASE_COMMON_ASSIGNMENT=RID,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
  if kind=='SVG':cmd=['/usr/bin/python3','-B',str(SCIC/'owner.py')];cpu=5;cap=5425;expected=CASE/'COMPLETION.json'
  else:
   ns=e.load('source_bound_filter_namespace',R/'experiments/v2101_parallel_priest_vehicle/filter_namespace.py')
   cmd=ns.command(C/'math_worker.py',S/'math');cpu=4;cap=100;expected=S/'math/RESULT.json'
  child=subprocess.Popen(['taskset','-c',str(cpu),'nice','-n','19','ionice','-c','3',*cmd],cwd=R,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
  identity=dict(pid=child.pid,pgid=os.getpgid(child.pid),start_ticks=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split()[19],CPU=cpu);put(kind+'_OWNED_CHILD.json',identity)
  sel=selectors.DefaultSelector();sel.register(child.stdout,selectors.EVENT_READ);total=0
  with(S/(kind+'.console')).open('xb')as log:
   while sel.get_map():
    assert time.monotonic()-start<cap,'NEXT_CASE_COMPONENT_TIME_CAP'
    for key,_ in sel.select(.2):
     data=os.read(key.fileobj.fileno(),16384)
     if not data:sel.unregister(key.fileobj);continue
     total+=len(data);assert total<=1024**2;log.write(data);log.flush()
  child.wait(timeout=5);m=e.read(expected);answer.update(closed=m['closed'],passed=child.returncode==0 and m['passed'],returncode=child.returncode,machine_path=str(expected.relative_to(R)),machine_sha256=e.sha(expected),diagnosis_complete=m.get('diagnosis_complete'),formal_trials=1 if kind=='SVG'else 0)
 except BaseException as error:answer.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  if child is not None:stop_owned(child,identity)
  # A vehicle entry has its own process group. Safely close that exact group
  # if a supervisor timeout killed its owner before normal source closure.
  if kind=='SVG'and(CASE/'OWNED_CHILD.json').exists():
   i=e.read(CASE/'OWNED_CHILD.json');f=Path('/proc',str(i['pid']),'stat')
   if f.exists()and f.read_text().split(') ',1)[1].split()[19]==i['start_ticks']:
    assert i['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and os.getpgid(i['pid'])==i['pgid'];os.killpg(i['pgid'],signal.SIGTERM)
    deadline=time.monotonic()+20
    while f.exists()and time.monotonic()<deadline:time.sleep(.1)
    if f.exists()and f.read_text().split(') ',1)[1].split()[19]==i['start_ticks']:os.killpg(i['pgid'],signal.SIGKILL)
  answer.update(closed=True,wall_s=time.monotonic()-start);put(kind+'_SUPERVISOR_RESULT.json',answer)
 return answer
def transport(stage,args,cap):
 put('PROGRESS.json',dict(stage=stage,unix=time.time()));p=None;i=None
 try:
  with(S/(stage+'.console')).open('xb')as f:
   p=subprocess.Popen(['taskset','-c','5','/usr/bin/python3','-B',str(C/'evidence.py'),*args],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=f,stderr=subprocess.STDOUT,start_new_session=True);i=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],stage=stage);put('ACTIVE_TRANSPORT.json',i);return p.wait(timeout=cap)
 finally:
  if p is not None:stop_owned(p,i)
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 f=(S/'owner.lock').open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not(S/'ONCE.json').exists()and e.read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed'];predecessor();original_source()
 assert e.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 source=e.read(S/'SOURCE_FREEZE.json')['files'];assert all(e.sha(R/n)==h for n,h in source.items())
 now=time.time();mono=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 put('ONCE.json',dict(pid=os.getpid(),unix=now,boot_id=boot,maximum_formal_tasks=1,maximum_math_NLP_calls=1,no_automatic_next_case=True))
 put('MATH_ADMISSION.json',dict(scope='ONE_EXPOSED_ORIGINAL_PCBF_AUXILIARY_DIAGNOSIS',models_authorized=False,source_freeze_sha256=e.sha(S/'SOURCE_FREEZE.json'),boot_id=boot,absolute_deadline_unix=now+90,hard_stop_monotonic=mono+90))
 result=dict(closed=False,pipeline_passed=False,whole_navigation_passed=False,formal_tasks=1,first_error=None)
 try:
  put('PROGRESS.json',dict(stage='PARALLEL_SVG_AND_PCBF',unix=now))
  with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
   jobs={k:pool.submit(run_job,k)for k in ['SVG','MATH']};results={k:v.result()for k,v in jobs.items()}
  result['jobs']=results;assert e.read(CASE/'COMPLETION.json')['closed']
  put('CLOSED_JOBS_BEFORE_ARCHIVE.json',dict(closed=True,jobs=results,formal_task_passed=e.read(CASE/'COMPLETION.json')['passed'],math_diagnostic_not_Phase=True))
  for stage,args,cap in [('archive',['archive',RID],120),('ref',['ref',RID],15),('remote',['deliver',RID],620)]:assert transport(stage,args,cap)==0,'NEXT_CASE_EVIDENCE_STAGE_FAILED:'+stage
  T=S/'runtime_archives'/RID;assert e.read(T/'FULL_REMOTE_VERIFIED.json')['passed']and e.read(T/'TRANSPORT_CLEANUP.json')['passed'];m=e.read(CASE/'COMPLETION.json')
  paths=[CASE/'COMPLETION.json',T/'ARCHIVE_INDEX.json',T/'FULL_REMOTE_VERIFIED.json',T/'TRANSPORT_CLEANUP.json',S/'math/RESULT.json']
  e.put(CASE/'POST_ROUND_STORAGE_BARRIER.json',dict(passed=True,formal_task_passed=m['passed'],whole_navigation_passed=m['whole_navigation_passed'],formal_common_tasks=1,proof_paths_SHA256={str(p.relative_to(R)):e.sha(p)for p in paths},all_originals_retained=True,models_authorized=False,scientific_source_root=str(SCI.relative_to(R)),transport_source_root=str(S.relative_to(R))))
  put('POST_COMPONENT_STORAGE_BARRIER.json',dict(passed=True,formal_barrier_path=str((CASE/'POST_ROUND_STORAGE_BARRIER.json').relative_to(R)),formal_barrier_sha256=e.sha(CASE/'POST_ROUND_STORAGE_BARRIER.json'),models_authorized=False))
  result.update(pipeline_passed=True,formal_task_passed=m['passed'],whole_navigation_passed=m['whole_navigation_passed'])
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:result.update(closed=True,wall_s=time.monotonic()-mono);put('RESULT.json',result)
 print(json.dumps(result));return 0 if result['pipeline_passed']else 1
if __name__=='__main__':raise SystemExit(main())
