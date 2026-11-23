"""Source closed review and exact inherited/new full-source remote coverage."""
import argparse,fcntl,json,hashlib,os
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/v1739_teb_current_cycle';D=R/'runs/v1740_teb_current_cycle_source_recovery'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 assert not p.exists();p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
 os.sched_setaffinity(0,{5});a=argparse.ArgumentParser();a.add_argument('--barrier-session');args=a.parse_args()
 outer=read(O/'SOURCE_OUTER_CLOSED.json');inner=read(O/'SOURCE_QUALIFICATION.json');assert outer['closed']and outer['review_restored']
 for n,key in [('SOURCE_OUTER_ONCE_CLAIM.json','owner_pid'),('SOURCE_OWNED_CHILD.json','pid')]:assert not Path('/proc',str(read(O/n)[key])).exists()
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if not args.barrier_session:
  source=read(O/('SOURCE_FREEZE.json'if inner['passed']else'FAILED_SOURCE_FREEZE.json'))['files'];assert all(sha(R/n)==h for n,h in source.items())
  v=dict(closed=True,passed=outer['passed'],SOURCE_only=True,models=0,optimizer_calls=0,explicit_DLL_loads=0,physical_native=0,replay_native=0,all_source_SHA_verified=True,source_members=len(source),first_error=inner.get('first_error'),outer_first_error=outer.get('first_error'),runtime_or_vehicle_PASS=False,runtime_recovery_pending=True)
  put(O/'RUNTIME_CLOSED_REVIEW.json',v)
  (R/'docs/TEB_CURRENT_CYCLE_V1739_REPORT.md').write_text('# TEB current cycle V1739\n\nSOURCE software qualification only. Actual constructor/query/physical cycle not yet run. Original HCP/author/binary retained. Body-centre/rear-axle frame and footprint, shared causal receipt, explicit upstream ROS velocity saturation Python port, readonly native worker and original fullstate stop/audit chain. Old exposed WE03 task, not new phase or independent benchmark.\n\n```json\n'+json.dumps(v,indent=2)+'\n```\n')
  print(json.dumps(v));return
 v=read(D/'FULL_REMOTE_VERIFIED.json');assert v['passed']and all(v[k]for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA'])and read(D/'TRANSPORT_CLEANUP.json')['passed']and read(D/'remote_delivery/FINALIZED.json')['passed']
 assert not Path('/proc',str(read(D/'remote_delivery/CLAIM.json')['pid'])).exists()
 put(D/'DELIVERY_WORKER_EXIT.json',dict(passed=True,tool_session=args.barrier_session,returncode=0,worker_gone=True,late_outside_archive=True))
 paths=[D/n for n in ['ARCHIVE_INDEX.json','FULL_REMOTE_VERIFIED.json','TRANSPORT_CLEANUP_MANIFEST.json','TRANSPORT_CLEANUP.json','DELIVERY_WORKER_EXIT.json']]
 put(O/'POST_SOURCE_STORAGE_BARRIER.json',dict(passed=True,proof_paths_SHA256={str(p.relative_to(R)):sha(p)for p in paths},late_outside_archive=True))
 source=read(O/'SOURCE_FREEZE.json')['files'];base=read(R/'runs/v1694_shared_observation_closure/SOURCE_FREEZE.json')['files'];inherited=R/'runs/v1694_shared_observation_closure/CURRENT_SOURCE_REMOTE_RECOVERY.json';assert read(inherited)['all_frozen_members_remote_chain_covered']
 members={x['path']:x.get('sha256')for x in read(D/'ARCHIVE_INDEX.json')['files']};missing=[n for n,h in source.items()if base.get(n)!=h and members.get(n)!=h];assert not missing
 gates={str((O/n).relative_to(R)):sha(O/n)for n in ['SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json']};assert all(members[n]==h for n,h in gates.items())
 put(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json',dict(passed=True,source_freeze_sha256=sha(O/'SOURCE_FREEZE.json'),all_frozen_members=len(source),all_frozen_members_remote_chain_covered=True,uncovered_members=missing,inherited_recovery_path=str(inherited.relative_to(R)),inherited_recovery_sha256=sha(inherited),index_path=str((D/'ARCHIVE_INDEX.json').relative_to(R)),index_sha256=sha(D/'ARCHIVE_INDEX.json'),full_remote_proof_path=str((D/'FULL_REMOTE_VERIFIED.json').relative_to(R)),full_remote_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),source_commit=v['source_commit'],additional_qualification_gate_members_verified=gates,physical_admission=False,late_outside_archive=True))
 print(json.dumps(dict(remote_closed=True,source_chain_members=len(source),models=0)))
if __name__=='__main__':main()
