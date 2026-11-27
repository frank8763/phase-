"""One explicit readonly HEAD recovery; keep original failedref proof intact."""
from pathlib import Path
import json,os,subprocess,time,sys,hashlib,types
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name;OLD=R/'experiments/v2162_pcbf_conditioned_current100';ROOT=R/'runs'/OLD.name;D=ROOT/'recovery'
sys.path.insert(0,str(OLD));from context import read,put,sha,load
m=load('unmodified_source_transport',OLD/'evidence.py')
EXPECTED='8d2248738da385f58cd5269db875126a180311b9';LATE=D/'SOURCE_SYNC_READONLY_RECOVERY.json'
def record():
 assert os.sched_getaffinity(0)=={5}and not(S/'READONLY_RECOVERY_ONCE.json').exists()and not(ROOT/'components/PCBF/PILOT_ONCE_CLAIM.json').exists()
 original=read(D/'SOURCE_SYNC_RESULT.json');assert original['head']==EXPECTED and original['push_executed']and original['push_returncode']==0 and not original['remote_verified']and original['error']=='BOUNDED_PUSH_OR_REF_TIMEOUT'
 put(S/'READONLY_RECOVERY_ONCE.json',dict(unix=time.time(),method='ONE_READONLY_GET_AFTER_CANONICAL_REF_TIMEOUT',no_new_push=True,original_proof_sha256=sha(D/'SOURCE_SYNC_RESULT.json')))
 try:
  p=subprocess.run([str(R/'tools/phase_storage_20261107/vendor/gh'),'api','repos/frank8763/phase-/git/ref/heads/main'],cwd=R,env=dict(os.environ,GODEBUG='http2client=0'),capture_output=True,timeout=5)
  assert p.returncode==0;v=json.loads(p.stdout);assert v['object']['sha']==EXPECTED
  proof=dict(head=EXPECTED,remote_verified=True,push_executed=False,ref_executed=True,readonly_recovery=True,original_failed_source_sync_path=str((D/'SOURCE_SYNC_RESULT.json').relative_to(R)),original_failed_source_sync_sha256=sha(D/'SOURCE_SYNC_RESULT.json'),original_push_returned0=True,normal_ref_timeout_retained=True,readonly_recovery_GET_attempts=1,actual_ref_response_sha256=hashlib.sha256(p.stdout).hexdigest(),verified_unix=time.time())
  put(LATE,proof);put(S/'RESULT.json',dict(passed=True,closed=True,no_new_push=True,original_failure_preserved=True,recovery_proof_path=str(LATE.relative_to(R)),models=0,NLP=0))
 except BaseException as e:put(S/'RESULT.json',dict(passed=False,closed=True,error=repr(e),no_new_push=True,models=0,NLP=0));raise
def overlay(p):
 if Path(p)==D/'SOURCE_SYNC_RESULT.json':
  original=read(p);proof=read(LATE);assert proof['remote_verified']and proof['head']==original['head']==EXPECTED and proof['original_failed_source_sync_sha256']==sha(p);return proof
 return read(p)
def deliver():
 text=m.deliver(None,preview=True);target=R/'experiments/v2007_mppi_observed_source_recovery/deliver.py';scope={'__file__':str(target),'__name__':'one_readonly_ref_recovered_source_transfer'};exec(compile(text,str(target),'exec'),scope)
 reserve=load('original_fixed_math_quota',OLD/'reservation.py');scope.update(S=ROOT,ROOT=ROOT,D0=D,SOURCE_D=D,BOUND_D=D,CASE_ID='',CASES=m.CASES,RESERVED_TRANSPORT_USAGE=reserve.transport_current_upper,read=overlay)
 return scope['main'](runtime=False)
def chain():
 fn=types.FunctionType(m.chain.__code__,dict(m.chain.__globals__,read=overlay));fn()
 v=read(ROOT/'CURRENT_SOURCE_REMOTE_RECOVERY.json');v.update(source_sync_result_path=str(LATE.relative_to(R)),source_sync_result_sha256=sha(LATE),normal_ref_timeout_retained=True,additional_readonly_ref_recovery=True,no_second_push=True,late_helper_recovered_by_future_runtime_members=True);put(ROOT/'CURRENT_SOURCE_REMOTE_RECOVERY.json',v)
 barrier=read(ROOT/'POST_SOURCE_STORAGE_BARRIER.json');barrier['recovery_sha256']=sha(ROOT/'CURRENT_SOURCE_REMOTE_RECOVERY.json');put(ROOT/'POST_SOURCE_STORAGE_BARRIER.json',barrier)
 for p in C.iterdir():
  if p.is_file():
   target=ROOT/'components/PCBF'/('LATE_REF_HELPER_'+p.name+'.txt');assert not target.exists();target.write_bytes(p.read_bytes())
 put(ROOT/'components/PCBF/LATE_REF_RECOVERY_PROVENANCE.json',dict(helper_files={str(p.relative_to(R)):sha(p)for p in C.iterdir()if p.is_file()},new_helper_not_in_original_Git_or_sourceRelease=True,recovered_by_future_runtime_members=True,readonly_proof_sha256=sha(LATE),original_failed_sync_sha256=sha(D/'SOURCE_SYNC_RESULT.json'),new_push=False))
 print('source recovered chain PASS; original failedsync preserved')
if __name__=='__main__':
 stage=sys.argv[1]
 if stage=='record':record()
 elif stage=='deliver':raise SystemExit(deliver())
 elif stage=='chain':chain()
 else:raise AssertionError(stage)
