"""Close loader evidence without turning source PASS into numerical success."""
import argparse,fcntl,os
from pathlib import Path
R=Path(__file__).resolve().parents[2];P=R/'runs/v1737_teb_exact_native_aliases';D=R/'runs/v1738_teb_exact_alias_recovery'
import hashlib,json
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 assert not p.exists();p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
 a=argparse.ArgumentParser();a.add_argument('--barrier-session');args=a.parse_args();os.sched_setaffinity(0,{5})
 outer=read(P/'SOURCE_OUTER_CLOSED.json');assert outer['closed']and outer['review_restored'];claim=read(P/'SOURCE_OUTER_ONCE_CLAIM.json');assert not Path('/proc',str(claim['owner_pid'])).exists()
 assert not Path('/proc',str(read(P/'SOURCE_OWNED_CHILD.json')['pid'])).exists();assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if not args.barrier_session:
  native=read(P/'build/SOURCE_NATIVE_RESULT.json')if(P/'build/SOURCE_NATIVE_RESULT.json').exists()else None
  source=read(P/'SOURCE_FREEZE.json')if(P/'SOURCE_FREEZE.json').exists()else read(P/'FAILED_SOURCE_FREEZE.json');assert all(sha(R/k)==h for k,h in source['files'].items())
  proof=dict(closed=True,passed=outer['passed'],scope='TEB_LOADER_C_POD_SOURCE_ONLY',outer_first_error=outer.get('first_error'),native_first_error=native.get('first_error')if native else None,explicit_DLL_loads=native['explicit_DLL_loads']if native else None,metadata_FFI_calls=native['metadata_FFI_calls']if native else None,planner_constructors=0,optimizer_calls=0,models=0,physical_native=0,replay_native=0,upstream_static_registration_count=None,complete_vehicle_or_numeric_runtime_qualified=False,all_source_SHA_verified=True,owner_and_child_gone=True,review_original=True,execution_idle=True,runtime_recovery_pending=True)
  put(P/'RUNTIME_CLOSED_REVIEW.json',proof);(R/'docs/TEB_RUNTIME_BINDING_V1737_REPORT.md').write_text('# Original TEB runtime binding V1737\n\nSource qualification only: actual private CPU2 loader, exact dependency inode identity and C POD metadata, immutable sourceguard. Original HomotopyClassPlanner identity retained; future numeric parallelism constrained to1thread, no RNG reseed API. Thin C functions compiled but no constructor/plan/destroy invoked. Phase vehicle config/causal observation client/full independent audit remain pending. Upstream DLL static registration effects count unknown.\n\n```json\n'+json.dumps(proof,indent=2)+'\n```\n\nNo navigation/safety/efficacy/realtime or statistical result. Original experiment denominators unchanged.\n');print(json.dumps(proof));return
 v=read(D/'FULL_REMOTE_VERIFIED.json');assert v['passed']and all(v[k]for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA'])and read(D/'TRANSPORT_CLEANUP.json')['passed']and read(D/'remote_delivery/FINALIZED.json')['passed']
 assert not Path('/proc',str(read(D/'remote_delivery/CLAIM.json')['pid'])).exists();put(D/'DELIVERY_WORKER_EXIT.json',dict(passed=True,tool_session=args.barrier_session,returncode=0,worker_gone=True,late_outside_archive=True));paths=[D/n for n in ['ARCHIVE_INDEX.json','FULL_REMOTE_VERIFIED.json','TRANSPORT_CLEANUP_MANIFEST.json','TRANSPORT_CLEANUP.json','DELIVERY_WORKER_EXIT.json']]
 put(P/'POST_ROUND_STORAGE_BARRIER.json',dict(passed=True,proof_paths_SHA256={str(p.relative_to(R)):sha(p)for p in paths},closed_review_sha256=sha(P/'RUNTIME_CLOSED_REVIEW.json'),models=0,late_outside_archive=True));put(P/'REMOTE_RECOVERY_SUPPLEMENT.json',dict(passed=True,full_remote=v,barrier_sha256=sha(P/'POST_ROUND_STORAGE_BARRIER.json'),late_outside_archive=True))
 print(json.dumps(dict(remote_closed=True,source_passed=outer['passed'],models=0)))
if __name__=='__main__':main()
