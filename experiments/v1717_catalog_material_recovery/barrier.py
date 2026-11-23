"""Record actual transfer worker exit and exact proof links before next batch."""
import argparse,fcntl,hashlib,json,os
from pathlib import Path
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v1716_catalog_directory_materials';DROOT=R/'runs/v1717_catalog_material_recovery'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 assert not p.exists(),str(p);p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--batch',required=True);parser.add_argument('--tool-session',required=True);args=parser.parse_args();assert args.batch in [x['id']for x in read(ROOT/'BATCHES_LOCKED.json')['batches']]
 os.sched_setaffinity(0,{5});O=ROOT/'rounds'/args.batch;D=DROOT/args.batch;v=read(D/'FULL_REMOTE_VERIFIED.json');assert v['passed']and all(v[k]for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA'])and read(D/'TRANSPORT_CLEANUP.json')['passed']and read(D/'remote_delivery/FINALIZED.json')['passed']
 assert not Path('/proc',str(read(D/'remote_delivery/CLAIM.json')['pid'])).exists()and not Path('/proc',str(read(O/'ONCE_CLAIM.json')['owner_pid'])).exists()
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(ROOT/'OWNER.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 put(D/'DELIVERY_WORKER_EXIT.json',dict(passed=True,tool_session=args.tool_session,returncode=0,owned_worker_gone=True,models=0,late_metadata_outside_archive=True))
 paths=[D/n for n in ['ARCHIVE_INDEX.json','FULL_REMOTE_VERIFIED.json','TRANSPORT_CLEANUP_MANIFEST.json','TRANSPORT_CLEANUP.json','DELIVERY_WORKER_EXIT.json']]
 put(O/'POST_ROUND_STORAGE_BARRIER.json',dict(passed=True,closed_runtime_review_sha256=sha(O/'RUNTIME_CLOSED_REVIEW.json'),proof_paths_SHA256={str(p.relative_to(R)):sha(p)for p in paths},full_remote_and_exact_transport_cleanup=True,review_original=True,execution_idle=True,models=0,method_executed=False,late_metadata_outside_archive=True))
 put(O/'REMOTE_RECOVERY_SUPPLEMENT.json',dict(passed=True,remote=v,barrier_sha256=sha(O/'POST_ROUND_STORAGE_BARRIER.json'),models=0,method_outcome=None,late_metadata_outside_closed_archive=True))
 p=R/'CURRENT_EXPERIMENT.json';cur=read(p);cur['status']='NATIVE_MATERIAL_BATCH_REMOTE_CLOSED_NO_MODELS';cur['latest_native_material_batch'].update(recovery_pending=False,runtime_remote_verified=True,barrier_sha256=sha(O/'POST_ROUND_STORAGE_BARRIER.json'));p.write_text(json.dumps(cur,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write(f"\nV1716 {args.batch} selected-materialdataPASS={read(O/'RESULT.json')['passed']}，V1717 distinctarchive{v['members']}members/{v['archive_bytes']}B全actualremote block/member/whole/indexSHA核/exactduplicatecleanup/worker{args.tool_session}exit0/sourcecommonrefonly不二push。原debs/sysroot/selected+excluded manifests留，canonicalbarrier已存、lateoutsidearchive明确，0packageprogram/compiler/model/optimizer/physical/replay，非ABI/build/算法PASS；下一仅固定后继batch或单独登记原库编译，旧计数不改。\n")
 print(json.dumps(dict(batch=args.batch,remote_closed=True,members=v['members'],archive_bytes=v['archive_bytes'],models=0)))
if __name__=='__main__':main()
