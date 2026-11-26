"""Original numerical MPPI10–12 owners with qualified bounded dual-route IO."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,signal,subprocess,sys,time,traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name;S=R/'runs/v2045_remaining_parallel_source';NET=R/'experiments/v2062_bounded_dual_route_transport';H=R/'experiments/v2045_remaining_parallel_source/evidence.py'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);raw=json.dumps(v,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<128*1024;t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def one(old,row):
 O=R/row['root'];B=D/row['round_id'];B.mkdir();start=time.monotonic();value=dict(closed=False,pipeline_passed=False,round_id=row['round_id'],first_error=None)
 try:
  value['owner_returncode']=old.command(row,'owner',['/usr/bin/python3','-B',str(R/'experiments/v2069_closed_metadata_reservation/entry.py')],5500);assert read(O/'COMPLETION.json')['closed'];v=old.review(row)
  for stage,cap in [('archive',240),('ref',15)]:assert old.command(row,stage,['/usr/bin/python3','-B',str(H),stage,row['round_id']],min(cap,7200-(time.monotonic()-start)))==0,'PIPELINE_STAGE_FAILED:'+stage
  for episode in [1,2]:
   code=old.command(row,'remote_dualroute_'+str(episode),['/usr/bin/python3','-B',str(NET/'recover.py'),row['round_id'],str(episode)],min(620,7200-(time.monotonic()-start)))
   if code==0:break
   assert episode==1,'BOTH_BOUNDED_DUAL_ROUTE_IO_EPISODES_FAILED'
  assert old.command(row,'barrier',['/usr/bin/python3','-B',str(NET/'recover.py'),'barrier',row['round_id']],20)==0,'REMOTE_BARRIER_FAILED'
  value.update(pipeline_passed=True,whole_navigation_passed=v['whole_navigation_passed'],valid_finite_method_refusal=v['valid_finite_method_refusal'],technical_censor=v['technical_censor'],actual_native=v['actual_native'],own_replay_native=v['own_replay_native'])
 except BaseException as e:value.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:value.update(closed=True,wall_s=time.monotonic()-start);put(B/'RESULT.json',value)
 return value
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));assert not(D/'ONCE.json').exists();plan=read(D/'PLAN_LOCKED.json');assert sha(S/'PLAN_LOCKED.json')==plan['original_plan_sha256']and plan['assignments']==read(S/'PLAN_LOCKED.json')['methods']['MPPI'][8:];assert read(S/'rounds/common_09__MPPI/POST_ROUND_STORAGE_BARRIER.json')['passed']and read(S/'rounds/common_10__MPPI/POST_ROUND_STORAGE_BARRIER.json')['passed']and read(R/'runs/v2062_bounded_dual_route_transport/SOFTWARE_RESULT.json')['passed']
 metadata=read(D/'HELPER_SOURCE_BINDING.json');assert all(sha(R/n)==h for n,h in metadata['files'].items())and sha(R/'runs/v2062_bounded_dual_route_transport/SOFTWARE_RESULT.json')==metadata['software_result_sha256'],'LATE_METADATA_SOURCE_CHANGED'
 source=load('exact_frozen_original_numerical_source',H);assert all(source.sha(R/n)==h for n,h in source.read(S/'SOURCE_FREEZE.json')['files'].items())
 storage=load('exact_existing_quiescent_storage',R/'experiments/v2050_closed_queue_retention_recovery/storage.py');locks=storage.idle();del locks
 for row in plan['assignments']:
  O=R/row['root'];assert all(not(O/n).exists()for n in ['PILOT_ONCE_CLAIM.json','FORMAL_REGISTERED.json','OWNED_CHILD.json','COMPLETION.json','actual'])
 put(D/'ONCE.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19],unix=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),finite_remaining2=True,technical_max_s=2*7200,original_source_commit='0ec97a32f5ebdf380792f4766f383c804f67b202',no_old_formal_retry=True));result=dict(closed=False,completed=[],unexecuted=2,pipeline_passed=False,first_error=None);start=time.monotonic()
 def expired(*args):raise TimeoutError('FINITE_TWO_CASE_14400_TECHNICAL_STOP')
 signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,2*7200);old=load('same_original_owner_review_archive_functions',R/'experiments/v2048_remaining_parallel_dispatch/run.py');old.D=D
 try:
  for row in plan['assignments']:
   assert all(sha(R/n)==h for n,h in metadata['files'].items()),'LATE_METADATA_SOURCE_CHANGED'
   assert time.monotonic()-start+7200<=2*7200,'NO_COMPLETE_PIPELINE_TECHNICAL_WINDOW';O=R/row['root'];late=O/'LATE_FINAL_TWO_SHARED_METADATA';late.mkdir();manifest={}
   for folder in [C,NET,R/'experiments/v2069_closed_metadata_reservation',R/'runs/v2062_bounded_dual_route_transport']:
    for p in folder.iterdir():
     if p.is_file()and p.suffix in{'.py','.md','.json'}:
      assert p.stat().st_size<128*1024;target=late/(folder.name+'__'+p.name);target.write_bytes(p.read_bytes());manifest[str(p.relative_to(R))]=dict(sha256=sha(p),runtime_member=str(target.relative_to(R)))
   put(late/'PROVENANCE.json',dict(exact_late_runtime_members=manifest,not_in_original_0ec97Git=True,models=0,original_numerical_owner_source_unchanged=True))
   put(D/'PROGRESS.json',dict(active=row['round_id'],stage='OWNER',closed=len(result['completed']),unclaimed_after_active=1-len(result['completed']),unix=time.time()));value=one(old,row);result['completed'].append(value);result['unexecuted']=sum(not(R/x['root']/'FORMAL_REGISTERED.json').exists()for x in plan['assignments']);put(D/'CHECKPOINT.json',result)
   assert value.get('pipeline_passed')and not value.get('technical_censor')and(value.get('whole_navigation_passed')or value.get('valid_finite_method_refusal')),'TECHNICAL_SAFETY_OR_UNKNOWN_EVIDENCE_STOP'
   a=storage.cleanup(row['round_id']);b=storage.rebalance(row['round_id']);put(D/row['round_id']/'QUIESCENT_STORAGE_CLOSED.json',dict(passed=True,cleanup=a,retention=b))
  result['pipeline_passed']=True
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,wall_s=time.monotonic()-start);put(D/'RESULT.json',result)
 print(json.dumps(result));return 0 if result['pipeline_passed']else 1
if __name__=='__main__':raise SystemExit(main())
