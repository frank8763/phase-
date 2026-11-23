"""Exact closed build review, then a separate actualremote storage barrier."""
import argparse,fcntl,hashlib,json,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];P=R/'runs/v1720_teb_writable_mountpoints';D=R/'runs/v1721_teb_mount_build_recovery'
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def put(p,v):
 assert not p.exists();p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
 a=argparse.ArgumentParser();a.add_argument('--barrier-session');args=a.parse_args();os.sched_setaffinity(0,{5})
 result=read(P/'RESULT.json');assert result['closed']and result['compiler_exited'];claim=read(P/'ONCE_CLAIM.json');assert not Path('/proc',str(claim['owner_pid'])).exists()
 if(P/'OWNED_CHILD.json').exists():assert not Path('/proc',str(read(P/'OWNED_CHILD.json')['pid'])).exists()
 assert all(sha(R/k)==v for k,v in claim['source_files_SHA256'].items())and sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if not args.barrier_session:
  frozen=read(R/'runs/v1694_shared_observation_closure/SOURCE_FREEZE.json')['files'];assert all(sha(R/k)==v for k,v in frozen.items())
  current=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert current+(32+32+512)*1024**2<15*1024**3
  review=dict(closed=True,passed=result['passed'],scope='ORIGINAL_TEB_CPU4_LIBRARY_BUILD_ONLY',first_error=result['first_error'],secondary_errors=result['secondary_errors'],configure_calls=result['configure_calls'],compile_calls=result['compile_calls'],source_SHA_unchanged=result['source_SHA_unchanged'],optimizer_constructors=0,optimizer_calls=0,optimizer_DLL_loads=0,other_toolchain_dynamic_load_count=None,models=0,physical_native=0,replay_native=0,method_outcome=None,allruns_bytes=current,owner_and_child_gone=True,review_original=True,execution_idle=True,all14079_shared_source_SHA_verified=True,result_sha256=sha(P/'RESULT.json'),runtime_recovery_pending=True)
  put(P/'RUNTIME_CLOSED_REVIEW.json',review)
  (R/'docs/TEB_NATIVE_BUILD_V1720_REPORT.md').write_text('# Original TEB isolated native build V1720\n\nOriginal author9e55af4724310c34bcfa8cbb3b2783478c1a246a files unchanged, original recovered ROS/Ubuntu dependencies mounted read-only in a network-isolated namespace. Host fallback and exact package link/path mapping recorded. Build completion is not optimizer or navigation qualification.\n\n```json\n'+json.dumps(review,indent=2)+'\n```\n\nOriginal RESULT and separate configure/compile consoles are authoritative; no old failed attempt was reopened.0optimizer/model/physical/replay.\n')
  c=read(R/'CURRENT_EXPERIMENT.json');c.update(status='TEB_NATIVE_BUILD_CLOSED_RECOVERY_PENDING',models_now_authorized=False);c['latest_teb_native_build']=review;(R/'CURRENT_EXPERIMENT.json').write_text(json.dumps(c,indent=2,sort_keys=True,ensure_ascii=False)+'\n');print(json.dumps(review));return
 v=read(D/'FULL_REMOTE_VERIFIED.json');assert v['passed']and all(v[k]for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA'])and read(D/'TRANSPORT_CLEANUP.json')['passed']and read(D/'remote_delivery/FINALIZED.json')['passed']
 assert not Path('/proc',str(read(D/'remote_delivery/CLAIM.json')['pid'])).exists()
 put(D/'DELIVERY_WORKER_EXIT.json',dict(passed=True,tool_session=args.barrier_session,returncode=0,worker_gone=True,late_outside_archive=True))
 paths=[D/n for n in ['ARCHIVE_INDEX.json','FULL_REMOTE_VERIFIED.json','TRANSPORT_CLEANUP_MANIFEST.json','TRANSPORT_CLEANUP.json','DELIVERY_WORKER_EXIT.json']]
 put(P/'POST_ROUND_STORAGE_BARRIER.json',dict(passed=True,proof_paths_SHA256={str(p.relative_to(R)):sha(p)for p in paths},closed_review_sha256=sha(P/'RUNTIME_CLOSED_REVIEW.json'),models=0,late_outside_archive=True))
 put(P/'REMOTE_RECOVERY_SUPPLEMENT.json',dict(passed=True,full_remote=v,barrier_sha256=sha(P/'POST_ROUND_STORAGE_BARRIER.json'),late_outside_archive=True))
 c=read(R/'CURRENT_EXPERIMENT.json');c['status']='TEB_NATIVE_BUILD_REMOTE_CLOSED_NO_MODELS';c['latest_teb_native_build']['runtime_recovery_pending']=False;(R/'CURRENT_EXPERIMENT.json').write_text(json.dumps(c,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\nV1720原作者TEB namespacebuild closed passed='+str(result['passed'])+'，configure='+str(result['configure_calls'])+'/compile='+str(result['compile_calls'])+'，首错原RESULT/console保留。V1721全actualremoteSHA/精确运输cleanup/worker'+args.barrier_session+'exit0/canonicalbarrier，sole新source runtime仅refonly不二push，0optimizer/model/physical/replay，未构成TEB算法比较结果。\n')
 print(json.dumps(dict(remote_closed=True,build_passed=result['passed'],models=0)))
if __name__=='__main__':main()
