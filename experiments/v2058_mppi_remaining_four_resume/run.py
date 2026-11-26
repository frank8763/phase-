"""Original frozen numerical owners; bounded recovered metadata queue only."""
from pathlib import Path
import ast,hashlib,importlib.util,inspect,json,os,signal,subprocess,sys,time,traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name;S=R/'runs/v2045_remaining_parallel_source'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 raw=json.dumps(v,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<2*1024**2;p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
def transfer_recovery(row):
 O=R/row['root'];T=S/'runtime_archives'/row['round_id'];B=D/row['round_id'];assert not(T/'FULL_REMOTE_VERIFIED.json').exists()and not(T/'remote_delivery_resume_2058').exists()
 helper=load('original_same_archive_evidence',R/'experiments/v2045_remaining_parallel_source/evidence.py');text=inspect.getsource(helper.deliver);needle='text=target.read_text()';assert text.count(needle)==1
 old="assert not alias.exists();alias.write_bytes((D/'ARCHIVE_INDEX.json').read_bytes())";new="assert not alias.exists()or sha(alias)==sha(D/'ARCHIVE_INDEX.json');\n        if not alias.exists():alias.write_bytes((D/'ARCHIVE_INDEX.json').read_bytes())"
 injection=';text=text.replace("O=D/\'remote_delivery\';", "O=D/\'remote_delivery_resume_2058\';");text=text.replace('+repr(old)+','+repr(new)+')';text=text.replace(needle,needle+injection);ast.parse(text)
 index=helper.read(T/'ARCHIVE_INDEX.json')
 for rowpart in index['parts']:
  p=T/'archive'/rowpart['name'];assert p.stat().st_size==rowpart['bytes']and helper.sha(p)==rowpart['sha256']
 put(B/'SAME_ARCHIVE_RECOVERY_PATCH.json',dict(original_helper_sha256=sha(Path(helper.__file__)),archive_index_sha256=sha(T/'ARCHIVE_INDEX.json'),old_failed_result_sha256=sha(T/'remote_delivery/RESULT.json'),transport_worker_directory_and_exact_index_alias_only=True,patched_function_AST_sha256=hashlib.sha256(ast.dump(ast.parse(text)).encode()).hexdigest(),models=0,no_push_ref_reseal=True));space=dict(helper.__dict__);exec(compile(text,str(helper.__file__),'exec'),space);return space['deliver'](row['round_id'])
def finalize_barrier(row):
 O=R/row['root'];T=S/'runtime_archives'/row['round_id'];v=read(O/'RUNTIME_CLOSED_REVIEW.json');assert read(T/'FULL_REMOTE_VERIFIED.json')['passed']and read(T/'TRANSPORT_CLEANUP.json')['passed'];i=read(T/'remote_delivery_resume_2058/CLAIM.json');assert not Path('/proc',str(i['pid'])).exists();paths=[O/'COMPLETION.json',O/'RUNTIME_CLOSED_REVIEW.json',O/'FORMAL_REGISTERED.json',O/'FORMAL_CLOSED_EVENT.json',T/'ARCHIVE_INDEX.json',T/'FULL_REMOTE_VERIFIED.json',T/'TRANSPORT_CLEANUP.json',D/row['round_id']/'SAME_ARCHIVE_RECOVERY_PATCH.json'];assert not(O/'POST_ROUND_STORAGE_BARRIER.json').exists();put(O/'POST_ROUND_STORAGE_BARRIER.json',dict(passed=True,whole_navigation_passed=v['whole_navigation_passed'],valid_finite_method_refusal=v['valid_finite_method_refusal'],technical_censor=v['technical_censor'],proof_paths_SHA256={str(p.relative_to(R)):sha(p)for p in paths},all_original_physical_raw_retained=True,old_transport_failure_retained=True,models_authorized=False))
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));assert not(D/'ONCE.json').exists();plan=read(D/'PLAN_LOCKED.json');assert sha(S/'PLAN_LOCKED.json')==plan['original_plan_sha256']and plan['assignments']==read(S/'PLAN_LOCKED.json')['methods']['MPPI'][6:]
 source=load('original_frozen_source_read',R/'experiments/v2045_remaining_parallel_source/evidence.py');assert all(source.sha(R/n)==h for n,h in source.read(S/'SOURCE_FREEZE.json')['files'].items())
 for row in plan['assignments']:
  O=R/row['root'];assert all(not(O/n).exists()for n in ['PILOT_ONCE_CLAIM.json','FORMAL_REGISTERED.json','OWNED_CHILD.json','COMPLETION.json','actual'])
 storage=load('quiescent_retained_storage',R/'experiments/v2050_closed_queue_retention_recovery/storage.py');locks=storage.idle();del locks
 put(D/'ONCE.json',dict(pid=os.getpid(),unix=time.time(),finite_remaining4=True,technical_max_s=4*7200,original_source_commit='0ec97a32f5ebdf380792f4766f383c804f67b202',no_old_formal_case_retry=True));result=dict(closed=False,completed=[],unexecuted=4,pipeline_passed=False,first_error=None);start=time.monotonic()
 def expired(*args):raise TimeoutError('FINITE_FOUR_CASE_28800_TECHNICAL_STOP')
 signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,4*7200)
 old=load('frozen_original_pipeline_functions',R/'experiments/v2048_remaining_parallel_dispatch/run.py');old.D=D
 try:
  for row in plan['assignments']:
   assert time.monotonic()-start+7200<=4*7200,'NO_COMPLETE_PIPELINE_TECHNICAL_WINDOW';O=R/row['root'];put(D/'PROGRESS.json',dict(active=row['round_id'],stage='OWNER',closed=len(result['completed']),remaining_not_yet_claimed=4-len(result['completed']),unix=time.time()));rs=time.monotonic()
   late=O/'LATE_RECOVERY_QUEUE_METADATA';late.mkdir();manifest={}
   folders=[C,R/'experiments/v2057_mppi08_same_archive_recovery',R/'runs/v2057_mppi08_same_archive_recovery']
   for folder in folders:
    for item in folder.iterdir():
     if item.is_file()and item.suffix in{'.py','.md','.json'}:
      assert item.stat().st_size<128*1024;target=late/(folder.name+'__'+item.name);target.write_bytes(item.read_bytes());manifest[str(item.relative_to(R))]=dict(sha256=sha(item),runtime_member_path=str(target.relative_to(R)))
   put(late/'LATE_PROVENANCE.json',dict(source_commit_for_numerical_owner='0ec97a32f5ebdf380792f4766f383c804f67b202',helpers_late_not_in_original_Git=True,exact_runtime_members=manifest,models=0))
   value=old.one(row)
   if not value.get('pipeline_passed')and value.get('first_error')=="AssertionError('PIPELINE_STAGE_FAILED:remote')":
    assert old.command(row,'remote_recovery',['/usr/bin/python3','-B',str(C/'run.py'),'--recover',row['round_id']],min(620,7200-(time.monotonic()-rs)))==0,'SAME_ARCHIVE_SECOND_IO_FAILED';finalize_barrier(row);v=read(O/'RUNTIME_CLOSED_REVIEW.json');value=dict(value,pipeline_passed=True,same_archive_transport_recovered=True,original_transport_failure_retained=True,whole_navigation_passed=v['whole_navigation_passed'],valid_finite_method_refusal=v['valid_finite_method_refusal'],technical_censor=v['technical_censor'],actual_native=v['actual_native'],own_replay_native=v['own_replay_native'])
   result['completed'].append(value);result['unexecuted']=sum(not(R/x['root']/'FORMAL_REGISTERED.json').exists()for x in plan['assignments']);put(D/'CHECKPOINT.json',result)
   assert value.get('pipeline_passed')and not value.get('technical_censor')and(value.get('whole_navigation_passed')or value.get('valid_finite_method_refusal')),'TECHNICAL_SAFETY_SOURCE_OR_UNKNOWN_STOP'
   # Sole actual lane is closed and fully backed up; only now retire duplicates.
   proof=storage.cleanup(row['round_id']);reconcile=storage.rebalance(row['round_id']);put(D/row['round_id']/'QUIESCENT_STORAGE_CLOSED.json',dict(passed=True,cleanup=proof,retention=reconcile));put(D/'CHECKPOINT.json',result)
  result['pipeline_passed']=True
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,wall_s=time.monotonic()-start);put(D/'RESULT.json',result)
 print(json.dumps(result));return 0 if result['pipeline_passed']else 1
if __name__=='__main__':
 if len(sys.argv)==3 and sys.argv[1]=='--recover':
  row=next(x for x in read(D/'PLAN_LOCKED.json')['assignments']if x['round_id']==sys.argv[2]);raise SystemExit(transfer_recovery(row))
 raise SystemExit(main())
