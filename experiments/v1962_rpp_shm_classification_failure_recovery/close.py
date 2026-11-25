from pathlib import Path
import json,hashlib,fcntl,time
R=Path(__file__).resolve().parents[2];D=R/'runs/v1962_rpp_shm_classification_failure_recovery';S=R/'runs/v1960_rpp_resource_before_guard';W=S
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 remote=read(D/'FULL_REMOTE_VERIFIED.json');assert remote['passed']and all(remote[k]for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA']);assert read(D/'TRANSPORT_CLEANUP.json')['passed']and read(D/'remote_delivery/RESULT.json')['passed']and not Path('/proc',str(read(D/'remote_delivery/CLAIM.json')['pid'])).exists()
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  with(R/n).open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert all(sha(R/n)==h for n,h in read(W/'SOURCE_FREEZE.json')['files'].items());members={v['path']:v for v in read(D/'ARCHIVE_INDEX.json')['files']}
 for path in [S/n for n in ['RESULT.json','COMPONENT_CLOSED.json','RUNTIME_CLOSED_REVIEW.json','AFTER_CONSTRUCTOR_MAPS.json','component.console','native.console']]:assert members[str(path.relative_to(R))]['sha256']==sha(path)
 proof=dict(passed=True,science_qualified=False,original_component_rerun=False,review_restored=True,locks_idle=True,source_all_SHA_verified=True,common_formal_counts=read(R/'runs/v1805_common_algorithm_registry/LEDGER.json')['closed'],runtime_index_path=str((D/'ARCHIVE_INDEX.json').relative_to(R)),runtime_index_sha256=sha(D/'ARCHIVE_INDEX.json'),full_remote_proof_path=str((D/'FULL_REMOTE_VERIFIED.json').relative_to(R)),full_remote_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),cleanup_proof_path=str((D/'TRANSPORT_CLEANUP.json').relative_to(R)),cleanup_proof_sha256=sha(D/'TRANSPORT_CLEANUP.json'),closed_review_path=str((S/'RUNTIME_CLOSED_REVIEW.json').relative_to(R)),closed_review_sha256=sha(S/'RUNTIME_CLOSED_REVIEW.json'),models=0,late_outside_archive=True)
 p=S/'COMPONENT_POST_STORAGE_BARRIER.json';assert not p.exists();p.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
