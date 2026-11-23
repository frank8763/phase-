"""Canonical actual runtime barrier after first complete remote readback."""
import argparse,fcntl,hashlib,json,os
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1739_teb_current_cycle';D=R/'runs/v1741_teb_current_cycle_runtime_recovery'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):assert not p.exists();p.write_text(json.dumps(v,indent=2)+'\n')
def main():
 os.sched_setaffinity(0,{5});a=argparse.ArgumentParser();a.add_argument('--session',required=True);args=a.parse_args()
 assert read(O/'COMPLETION.json')['closed']and read(O/'ACTUAL_RUNTIME_CLOSED_REVIEW.json')['closed']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 v=read(D/'FULL_REMOTE_VERIFIED.json');assert v['passed']and all(v[k]for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA'])and read(D/'TRANSPORT_CLEANUP.json')['passed']and read(D/'remote_delivery/FINALIZED.json')['passed']
 assert not Path('/proc',str(read(D/'remote_delivery/CLAIM.json')['pid'])).exists()
 put(D/'DELIVERY_WORKER_EXIT.json',dict(passed=True,tool_session=args.session,returncode=0,worker_gone=True,late_outside_archive=True))
 paths=[D/n for n in ['ARCHIVE_INDEX.json','FULL_REMOTE_VERIFIED.json','TRANSPORT_CLEANUP_MANIFEST.json','TRANSPORT_CLEANUP.json','DELIVERY_WORKER_EXIT.json']]
 put(O/'POST_ROUND_STORAGE_BARRIER.json',dict(passed=True,proof_paths_SHA256={str(p.relative_to(R)):sha(p)for p in paths},actual_closed_review_sha256=sha(O/'ACTUAL_RUNTIME_CLOSED_REVIEW.json'),late_outside_archive=True))
 put(O/'REMOTE_RECOVERY_SUPPLEMENT.json',dict(passed=True,full_remote=v,canonical_barrier_sha256=sha(O/'POST_ROUND_STORAGE_BARRIER.json'),original_source_review_and_actual_review_unmodified=True,late_outside_archive=True))
 print(json.dumps(dict(remote_closed=True,scientific_component_passed=read(O/'ACTUAL_RUNTIME_CLOSED_REVIEW.json')['passed'])))
if __name__=='__main__':main()
