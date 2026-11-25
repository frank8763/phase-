"""Source delta coverage from exact inherited proof and actual remote index."""
from pathlib import Path
import json,hashlib,fcntl,subprocess,time
R=Path(__file__).resolve().parents[2];S=R/'runs/v1960_rpp_resource_before_guard';D=R/'runs/v1961_rpp_guard_order_source_recovery';P=R/'runs/v1957_rpp_observed_constructor_dependencies'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 assert not p.exists();p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def main():
 r=read(D/'FULL_REMOTE_VERIFIED.json');assert r['passed']and all(r[k]for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA']);assert read(D/'TRANSPORT_CLEANUP.json')['passed']and read(D/'remote_delivery/FINALIZED.json')['passed']
 assert not Path('/proc',str(read(D/'remote_delivery/CLAIM.json')['pid'])).exists()
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 old={}
 inherited=read(S/'SOURCE_INHERITED_CHAINS.json')['inherited']
 for row in inherited:
  base=R/row['root'];assert sha(base/'SOURCE_FREEZE.json')==row['freeze_sha256']and sha(R/row['recovery_path'])==row['recovery_sha256']
  rec=read(R/row['recovery_path']);assert rec['passed']and rec['all_frozen_members_remote_chain_covered']and not rec['uncovered_members']
  old.update(read(base/'SOURCE_FREEZE.json')['files'])
 frozen=read(S/'SOURCE_FREEZE.json')['files'];prior=read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert prior['passed']and prior['all_frozen_members_remote_chain_covered']and not prior['uncovered_members']
 for a,h in [('index_path','index_sha256'),('full_remote_proof_path','full_remote_proof_sha256')]:assert sha(R/prior[a])==prior[h]
 assert all(sha(R/n)==h for n,h in frozen.items());members={x['path']:x for x in read(D/'ARCHIVE_INDEX.json')['files']};missing=[n for n,h in frozen.items()if old.get(n)!=h and members.get(n,{}).get('sha256')!=h];assert not missing
 sync=read(D/'SOURCE_SYNC_RESULT.json');assert sync['remote_verified']and sync['head']==r['source_commit']
 for n in ['authority.py','entry.py','native_component.py']:
  path=R/'experiments/v1960_rpp_resource_before_guard'/n;assert subprocess.check_output(['git','show',sync['head']+':'+str(path.relative_to(R))],cwd=R)==path.read_bytes()
 for path in [S/name for name in ['SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','SOURCE_FREEZE.json','SOURCE_INHERITED_CHAINS.json','ISOLATED_ENTRY_SOFTWARE_PROOF.json','FIXTURE.json','CONSTRUCTOR_DEPENDENCY_PINS.json']]:assert members[str(path.relative_to(R))]['sha256']==sha(path)
 put(D/'DELIVERY_WORKER_EXIT.json',dict(passed=True,worker_gone=True,returncode=0,late_outside_archive=True))
 put(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json',dict(passed=True,all_frozen_members_remote_chain_covered=True,uncovered_members=missing,source_members=len(frozen),inherited_members=sum(old.get(n)==h for n,h in frozen.items()),new_delta_members=sum(old.get(n)!=h for n,h in frozen.items()),index_path=str((D/'ARCHIVE_INDEX.json').relative_to(R)),index_sha256=sha(D/'ARCHIVE_INDEX.json'),full_remote_proof_path=str((D/'FULL_REMOTE_VERIFIED.json').relative_to(R)),full_remote_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),inherited_source_chains=inherited,source_commit=sync['head'],source_sync_result_path=str((D/'SOURCE_SYNC_RESULT.json').relative_to(R)),source_sync_result_sha256=sha(D/'SOURCE_SYNC_RESULT.json'),models_authorized=False,late_outside_archive=True))
 paths=[S/'SOURCE_FREEZE.json',S/'SOURCE_QUALIFICATION.json',S/'SOURCE_OUTER_CLOSED.json',S/'CURRENT_SOURCE_REMOTE_RECOVERY.json',D/'FULL_REMOTE_VERIFIED.json',D/'TRANSPORT_CLEANUP.json',D/'DELIVERY_WORKER_EXIT.json']
 put(S/'POST_SOURCE_STORAGE_BARRIER.json',dict(passed=True,proof_paths_SHA256={str(p.relative_to(R)):sha(p)for p in paths},all_originals_retained=True,models_authorized=False,late_outside_archive=True))
 print(json.dumps(dict(passed=True,source_members=len(frozen),new_delta_members=sum(old.get(n)!=h for n,h in frozen.items()))))
if __name__=='__main__':main()
