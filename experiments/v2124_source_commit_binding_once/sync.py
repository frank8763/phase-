"""One correct new-head binding after a preserved pre-commit no-op error."""
from pathlib import Path
import os,json,subprocess,hashlib,time,sys
R=Path(__file__).resolve().parents[2];C=R/'experiments/v2123_causal_footprint_filters';S=R/'runs'/C.name;D=S/'recovery'
sys.path.insert(0,str(C));from common import read,put,sha
os.sched_setaffinity(0,{5})
assert not(D/'CORRECT_HEAD_SYNC_ONCE.json').exists()and not(S/'ONCE.json').exists()
head=read(S/'CORRECT_COMMIT_PREPUSH_VERIFIED.json')['head'];assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==head
old=read(D/'SOURCE_SYNC_ATTEMPT01_RAW_RESULT.json');assert head!=old['head']and read(S/'PUBLISH_BINDING_FAILURE.json')['new_source_published']is False
for p in C.iterdir():
 if p.is_file()and p.suffix in{'.py','.md'}:assert subprocess.check_output(['git','show',head+':'+str(p.relative_to(R))],cwd=R)==p.read_bytes()
files=read(S/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in files.items())
put(D/'CORRECT_HEAD_SYNC_ONCE.json',dict(head=head,unix=time.time(),new_head_push_attempt_limit=1,old_noop_push_preserved=True))
proof=dict(head=head,remote_verified=False,push_executed=False,prior_misbound_attempt_raw_path=str((D/'SOURCE_SYNC_ATTEMPT01_RAW_RESULT.json').relative_to(R)),prior_misbound_attempt_sha256=sha(D/'SOURCE_SYNC_ATTEMPT01_RAW_RESULT.json'),source_binding_repair=True,repair_helper_path=str(Path(__file__).relative_to(R)),repair_helper_sha256=sha(__file__),old_noop_push_plus_one_new_head_push=True)
try:
 assert time.time()+40<read(S/'AUTHORIZATION.json')['absolute_end_unix']
 p=subprocess.run(['git','push','origin','HEAD:main'],cwd=R,capture_output=True,timeout=30);proof.update(push_executed=True,push_returncode=p.returncode)
 q=subprocess.run([str(R/'tools/phase_storage_20261107/vendor/gh'),'api','repos/frank8763/phase-/git/ref/heads/main'],cwd=R,env=dict(os.environ,GODEBUG='http2client=0'),capture_output=True,timeout=5)
 proof['remote_verified']=p.returncode==0 and q.returncode==0 and json.loads(q.stdout)['object']['sha']==head
except subprocess.TimeoutExpired:proof['error']='BOUNDED_CORRECT_NEW_HEAD_SYNC_TIMEOUT_NO_RETRY'
# Original claim/result are retained byte-for-byte under ATTEMPT01_RAW paths.
# This canonical pointer now describes the new head and explicitly links the failed binding.
put(D/'SOURCE_SYNC_RESULT.json',proof)
(S/'PUBLISH_BINDING_REPAIR_HELPER.py').write_bytes(Path(__file__).read_bytes())
put(S/'PUBLISH_BINDING_REPAIR.json',dict(passed=proof['remote_verified'],original_misbound_noop_preserved=True,old_sync_result_raw_sha256=sha(D/'SOURCE_SYNC_ATTEMPT01_RAW_RESULT.json'),new_proof_sha256=sha(D/'SOURCE_SYNC_RESULT.json'),helper_not_in_previously_sealed_source=True,helper_copy_for_runtime_archive='PUBLISH_BINDING_REPAIR_HELPER.py',source_requalified=False,source_resealed=False,models=0,solvers=0))
print(json.dumps(proof));assert proof['remote_verified']
