"""Finite detached three-lane campaign, all closure complete by09:00+0800."""
from pathlib import Path
import concurrent.futures,fcntl,os,subprocess,signal,time,json,traceback
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
 p=STUDY/'rounds'/rid/'actual/ACTUAL_PROGRESS.json'if rid else None
 d=dict(unix=time.time(),stage=stage,assignment=rid,deadline_unix=e.read(S/'AUTHORIZATION.json')['absolute_end_unix'],actual_partial=e.read(p)if p and p.exists()else None,whole_navigation_passed=None,not_a_scientific_PASS=True)
 e.put(S/'RUNNING_CHECKPOINT.json',d)
def run_process(label,argv,cap,*,env=None,cpu=5,rid=None):
 folder=S/'workers';folder.mkdir(exist_ok=True);path=folder/(label+'.console');assert not path.exists();p=None;i=None;start=time.monotonic();last=start
 try:
  with path.open('xb')as log:
   p=subprocess.Popen(['taskset','-c',str(cpu),'nice','-n','19','ionice','-c','3',*argv],cwd=R,env=dict(os.environ,PHASE_REPO=str(R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',**(env or{})),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   i=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],label=label,CPU=cpu,unix=time.time());e.put(folder/(label+'.IDENTITY.json'),i)
   while p.poll()is None:
    assert time.monotonic()-start<cap and time.time()<END-5 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT,'FINITE_NIGHT_OR_STAGE_STOP'
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
def component(kind):
 out=S/('math'if kind=='MATH'else'evidence_lane');script=C/('math_worker.py'if kind=='MATH'else'evidence_worker.py');cpu=6 if kind=='MATH'else 4;cap=920 if kind=='MATH'else 120
 try:
  ns=e.load('own_only_nonmodel_namespace',C/'namespace.py');code=run_process(kind,ns.command(script,out),cap,cpu=cpu);path=out/'RESULT.json'
  return dict(closed=True,returncode=code,machine_path=str(path.relative_to(R)),result=e.read(path)if path.exists()else None)
 except BaseException as error:return dict(closed=True,passed=False,first_error=repr(error),traceback=traceback.format_exc())
def close_case(rid,component_results):
 O=STUDY/'rounds'/rid;T=S/'runtime_archives'/rid;report=S/'round_reports'/rid;report.mkdir(parents=True,exist_ok=True)
 m=e.read(O/'COMPLETION.json');e.put(report/'BEFORE_ARCHIVE.json',dict(component_results=component_results,formal_task_passed=m['passed'],scientific_primary=m.get('machine_first_error'),scientific_secondary=m.get('machine_secondary_errors'),formal_tasks=1))
 for stage,args,cap in [('archive',['archive',rid],120),('ref',['ref',rid],15)]:
  assert run_process(rid+'_'+stage,['/usr/bin/python3','-B',str(C/'evidence.py'),*args],cap)==0,'ARCHIVE_OR_REF_FAILED:'+stage
 code=run_process(rid+'_remote',['/usr/bin/python3','-B',str(C/'evidence.py'),'deliver',rid],620)
 if code!=0:
  # The only automatic I/O recovery is one already sealed same-archive
  # premutation metadata episode. Never retry an uncertain write blindly.
  code=run_process(rid+'_remote_recovery',['/usr/bin/python3','-B',str(C/'evidence.py'),'deliver',rid],620,env=dict(PHASE_TRANSFER_RECOVERY='1'))
 assert code==0 and e.read(T/'FULL_REMOTE_VERIFIED.json')['passed']and e.read(T/'TRANSPORT_CLEANUP.json')['passed'],'RUNTIME_FULL_REMOTE_BARRIER_FAILED'
 paths=[O/'COMPLETION.json',O/'actual/RESULT.json',O/'FORMAL_CLOSED_EVENT.json',T/'ARCHIVE_INDEX.json',T/'FULL_REMOTE_VERIFIED.json',T/'TRANSPORT_CLEANUP.json']
 e.put(O/'POST_ROUND_STORAGE_BARRIER.json',dict(passed=True,formal_task_passed=m['passed'],whole_navigation_passed=m['whole_navigation_passed'],formal_common_tasks=1,all_originals_remote_verified_before_cache_cleanup=True,models_authorized=False,proof_paths_SHA256={str(p.relative_to(R)):e.sha(p)for p in paths},runtime_source_root=str(S.relative_to(R))))
 import closed_cache
 cache=closed_cache.retire(rid);e.put(report/'AFTER_CLOSE.json',dict(closed=True,method_result=m['passed'],closed_event=e.read(O/'FORMAL_CLOSED_EVENT.json'),cache=cache))
 return e.read(O/'FORMAL_CLOSED_EVENT.json')
def summary(results,components,why):
 registry=R/'runs/v1805_common_algorithm_registry';base=e.read(registry/'LEDGER.json');slots=[dict(x)for x in base['slots']]
 for p in(registry/'PARALLEL_METHOD_EVENTS').glob('*.REGISTERED.json'):
  ev=e.read(p);slot=next(x for x in slots if x['method']==ev['method']and x['task_id']==ev['task_id']);assert not slot['registered'];slot.update(ev);q=p.with_name(p.name.replace('.REGISTERED.json','.CLOSED.json'))
  if q.exists():slot.update(e.read(q))
 totals=dict(denominator=120,registered=sum(bool(x['registered'])for x in slots),closed=sum(bool(x['closed'])for x in slots),unexecuted=sum(not x['registered']for x in slots),whole_arrivals=sum(bool(x.get('qualified_success'))for x in slots))
 e.put(S/'NIGHT_RESULT.json',dict(closed=True,stop_reason=why,formal_case_results=results,component_results=components,totals=totals,models_authorized=False,whole_arrivals_are_only_qualified_goal_and_fullstop=True,finite_queue_completed=len(results)==9,not_all_method_interfaces_qualified=True,unix=time.time()))
 text="# Phase overnight finite queue\n\nStop reason: "+why+"\n\nFormal tasks closed: "+str(len(results))+" / 9 planned.\nOriginal common study: "+str(totals)+"\n\n"
 for row in results:text+="- "+row['round_id']+": whole="+str(row.get('qualified_success'))+", valid refusal="+str(row.get('valid_finite_method_refusal'))+", technical="+str(row.get('technical_censor'))+"\n"
 text+="\nPSF/PCBF runs are explicit non-Phase numerical development; PRIEST readout is saved evidence only. No training, hardware, Stage access, new independent map generalization, or established mechanism gain.\n"
 assert len(text.encode())<16384;(S/'NIGHT_SUMMARY.md').write_text(text)
def main():
 global END,BOOT
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));f=(S/'owner.lock').open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 auth=e.read(S/'AUTHORIZATION.json');END=auth['absolute_end_unix'];BOOT=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 assert not(S/'ONCE.json').exists()and e.read(S/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and time.time()<END-6860
 files=e.read(S/'SOURCE_FREEZE.json')['files'];assert all(e.sha(R/n)==h for n,h in files.items())
 e.put(S/'ONCE.json',dict(pid=os.getpid(),unix=time.time(),boot_id=BOOT,deadline_unix=END,formal_maximum=9,no_repeats=True))
 now=time.time();mono=time.monotonic();e.put(S/'MATH_ADMISSION.json',dict(scope='FINITE_NON_PHASE_FILTER_DEVELOPMENT',models_authorized=False,source_freeze_sha256=e.sha(S/'SOURCE_FREEZE.json'),boot_id=BOOT,absolute_end_unix=min(now+900,END-120),hard_stop_monotonic=mono+min(900,END-120-now)))
 e.put(S/'EVIDENCE_ADMISSION.json',dict(models_authorized=False,source_freeze_sha256=e.sha(S/'SOURCE_FREEZE.json'),absolute_end_unix=min(now+100,END-120)))
 results=[];components={};why='FINITE_QUEUE_COMPLETE'
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
  pending={k:pool.submit(component,k)for k in ['MATH','EVIDENCE']}
  try:
   for rid in auth['finite_formal_assignments']:
    if time.time()>END-6860:why='CANNOT_START_NEXT_WITH_COMPLETE_ORIGINAL_WINDOW_AND_TRANSPORT_RESERVE';break
    if(S/'STOP').exists():why='USER_STOP';break
    checkpoint('PRECLAIM',rid)
    O=STUDY/'rounds'/rid
    assert not(O/'PILOT_ONCE_CLAIM.json').exists()and not(O/'OWNED_CHILD.json').exists()and not(O/'COMPLETION.json').exists()and not(O/'actual/RESULT.json').exists(),'NO_DUPLICATE_CLAIM'
    assert all(e.sha(R/n)==h for n,h in files.items())
    code=run_process(rid+'_owner',['/usr/bin/python3','-B',str(C/'owner.py')],5425,env=dict(PHASE_COMMON_ASSIGNMENT=rid),rid=rid)
    assert e.read(O/'COMPLETION.json')['closed'],'OWNER_CLOSED_EVIDENCE_REQUIRED'
    # Join bounded independent components before archiving their mutable outputs.
    if not components:components={k:v.result()for k,v in pending.items()};e.put(S/'COMPONENT_RESULTS.json',components)
    event=close_case(rid,components);results.append(event);checkpoint('CASE_CLOSED',rid)
    if event['technical_censor']:why='SVG_TECHNICAL_CENSOR_AFFECTED_LANE_STOPPED_COMPONENTS_RETAINED';break
    if not(event['qualified_success']or event['valid_finite_method_refusal']or event.get('applicability_censor')):why='UNKNOWN_SCIENTIFIC_EVENT_STOP';break
  except BaseException as error:
   why=repr(error);e.put(S/'CAMPAIGN_ERROR.json',dict(error=repr(error),traceback=traceback.format_exc(),new_models_authorized=False,original_evidence_retained=True))
  finally:
   if not components:components={k:v.result()for k,v in pending.items()};e.put(S/'COMPONENT_RESULTS.json',components)
 summary(results,components,why);print(json.dumps(dict(closed=True,formal_cases=len(results),reason=why)))
if __name__=='__main__':main()
