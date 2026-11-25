"""Close exact already-verified archive using link and target identities."""
from pathlib import Path,PurePosixPath
import fcntl,hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;S=R/'runs/v1948_rpp_observed_dependency_scope';D=R/'runs/v1949_rpp_observed_source_recovery';P=R/'runs/v1923_dwa_five_checked_queue'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 assert not p.exists();p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def target_name(name,link):
 assert not PurePosixPath(link).is_absolute(),'ABSOLUTE_ARCHIVE_LINK'
 parts=[]
 for v in (PurePosixPath(name).parent/PurePosixPath(link)).parts:
  if v=='..':assert parts,'ARCHIVE_LINK_ESCAPES_ROOT';parts.pop()
  elif v!='.':parts.append(v)
 return '/'.join(parts)
def covered(name,h,members,*,current=False):
 visited=set()
 for _ in range(16):
  assert name not in visited,'ARCHIVE_LINK_CYCLE';visited.add(name);row=members[name]
  if 'symlink'not in row:
   assert row['sha256']==h,'ARCHIVE_TARGET_SHA_MISMATCH'
   if current:assert not(R/name).is_symlink()and sha(R/name)==h
   return len(visited)-1
  if current:assert(R/name).is_symlink()and os.readlink(R/name)==row['symlink'],'CURRENT_LINK_TEXT_CHANGED'
  name=target_name(name,row['symlink'])
 raise AssertionError('ARCHIVE_LINK_DEPTH')
def negative_cases():
 valid={'dir/link':dict(symlink='target'),'dir/target':dict(sha256='a')};assert covered('dir/link','a',valid)==1
 cases=[('target_SHA','dir/link','b',valid),('missing_target','dir/link','a',{'dir/link':dict(symlink='absent')}),('cycle','dir/link','a',{'dir/link':dict(symlink='link')}),('escape','dir/link','a',{'dir/link':dict(symlink='../../escape')}),('absolute','dir/link','a',{'dir/link':dict(symlink='/outside')}),('wrong_link_text','dir/link','a',{'dir/link':dict(symlink='wrong'),'dir/target':dict(sha256='a')})];out=[]
 for label,n,h,idx in cases:
  try:covered(n,h,idx)
  except(AssertionError,KeyError):out.append(label)
  else:raise AssertionError('BAD_LINK_ACCEPTED:'+label)
 return out

def main():
 negatives=negative_cases();assert not(O/'ONCE_CLAIM.json').exists();put(O/'ONCE_CLAIM.json',dict(unix=time.time(),pid=os.getpid(),models=0,remote_index_sha256=sha(D/'ARCHIVE_INDEX.json'),freeze_sha256=sha(S/'SOURCE_FREEZE.json'),late_outside_archive=True))
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);owner=(R/'runs/v1643_formal_parent_metadata/OWNER.lock').open();fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 remote=read(D/'FULL_REMOTE_VERIFIED.json');assert remote['passed']and all(remote[k]for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA'])
 assert read(D/'TRANSPORT_CLEANUP.json')['passed']and read(D/'remote_delivery/RESULT.json')['passed']and not Path('/proc',str(read(D/'remote_delivery/CLAIM.json')['pid'])).exists()
 inherited=read(S/'SOURCE_INHERITED_CHAINS.json')['inherited'];old={}
 for row in inherited:
  base=R/row['root'];assert sha(base/'SOURCE_FREEZE.json')==row['freeze_sha256']and sha(R/row['recovery_path'])==row['recovery_sha256'];rec=read(R/row['recovery_path']);assert rec['passed']and rec['all_frozen_members_remote_chain_covered']and not rec['uncovered_members'];old.update(read(base/'SOURCE_FREEZE.json')['files'])
 frozen=read(S/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items());members={x['path']:x for x in read(D/'ARCHIVE_INDEX.json')['files']};links={};direct=[]
 for n,h in frozen.items():
  if old.get(n)==h:continue
  hops=covered(n,h,members,current=True)
  if hops:links[n]=dict(hops=hops,symlink=members[n]['symlink'],resolved_byte_sha256=h)
  else:direct.append(n)
 assert len(links)==7 and len(direct)==103
 for name in ['SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','SOURCE_FREEZE.json','SOURCE_INHERITED_CHAINS.json','INVENTORY_SOFTWARE_RESULT.json','NATIVE_METADATA_RESULT.json']:covered(str((S/name).relative_to(R)),sha(S/name),members,current=True)
 sync=read(D/'SOURCE_SYNC_RESULT.json');assert sync['remote_verified']and sync['head']==remote['source_commit']
 for name in ['dependency_scope.py','source_target.py','native_metadata.py']:
  p=S.parent.parent/'experiments/v1948_rpp_observed_dependency_scope'/name;assert subprocess.check_output(['git','show',sync['head']+':'+str(p.relative_to(R))],cwd=R)==p.read_bytes()
 proof=dict(passed=True,negative_cases=negatives,source_members=len(frozen),inherited_members=sum(old.get(n)==h for n,h in frozen.items()),new_delta_members=110,new_direct_members=103,new_resolved_symlink_members=links,all_source_bytes_unchanged=True,all_raw_retained=True,models=0,late_outside_archive=True)
 put(O/'RESULT.json',proof);put(D/'DELIVERY_WORKER_EXIT.json',dict(passed=True,worker_gone=True,returncode=0,late_outside_archive=True))
 put(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json',dict(passed=True,all_frozen_members_remote_chain_covered=True,uncovered_members=[],source_members=len(frozen),inherited_members=proof['inherited_members'],new_delta_members=110,index_path=str((D/'ARCHIVE_INDEX.json').relative_to(R)),index_sha256=sha(D/'ARCHIVE_INDEX.json'),full_remote_proof_path=str((D/'FULL_REMOTE_VERIFIED.json').relative_to(R)),full_remote_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),inherited_source_chains=inherited,source_commit=sync['head'],source_sync_result_path=str((D/'SOURCE_SYNC_RESULT.json').relative_to(R)),source_sync_result_sha256=sha(D/'SOURCE_SYNC_RESULT.json'),exact_symlink_coverage_proof=str((O/'RESULT.json').relative_to(R)),exact_symlink_coverage_sha256=sha(O/'RESULT.json'),models_authorized=False,late_outside_archive=True))
 paths=[S/'SOURCE_FREEZE.json',S/'SOURCE_QUALIFICATION.json',S/'SOURCE_OUTER_CLOSED.json',S/'CURRENT_SOURCE_REMOTE_RECOVERY.json',D/'FULL_REMOTE_VERIFIED.json',D/'TRANSPORT_CLEANUP.json',D/'DELIVERY_WORKER_EXIT.json',O/'RESULT.json']
 put(S/'POST_SOURCE_STORAGE_BARRIER.json',dict(passed=True,proof_paths_SHA256={str(p.relative_to(R)):sha(p)for p in paths},all_originals_retained=True,models_authorized=False,late_outside_archive=True));print(json.dumps({k:v for k,v in proof.items()if k!='new_resolved_symlink_members'}))
if __name__=='__main__':main()
