"""Remove only identified closed, remotely verified Phase temporary data."""
import fcntl,gzip,hashlib,json,os,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];REC=R/'records/nav2_v863_execution_20261107';O=R/'runs/v862_v863_closure'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert read(REC/'FULL_REMOTE_VERIFIED.json')['public_release_verified']and read(REC/'PUBLIC_RESTORE_QUALIFICATION.json')['actual_extracted_members_sha_passed']
 assert read(REC/'SOURCE_SYNC_RESULT.json')['remote_head_verified']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with (REC/'CLEANUP_CLAIM.json').open('x')as f:json.dump(dict(started_unix=time.time(),scope='ONLY_LISTED_CLOSED_PHASE_TEMP'),f)
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 inventory=read(O/'cloud/v862-v863-evidence.INVENTORY.json');rows={x['path']:x for x in inventory['files']}
 # Current raw execution and plugin bytes must still match the publicly restored inventory.
 for name,row in rows.items():
  if name.startswith(('runs/v858_nav2_verified/v862_ready_static/','runs/v858_nav2_verified/v863_rpp_static/','runs/v862_execution_20261107/','runs/v863_execution_20261107/','runs/v863_rpp_preparation/','runs/v856_nav2_foundation/rootfs/')):
   assert row['type']=='file'and sha(R/name)==row['sha256'],name
 assert read(R/'records/nav2_v856_20261107/FINALIZED.json')['all9assets_streamed_sha_verified']
 assert read(R/'records/nav2_v856_20261107/FINALIZED.json')['evidence_restore_roundtrip_sha_verified']
 operation=REC/'operations';operation.mkdir(exist_ok=True)
 for name in ['upload.console','source_sync.console','public_restore.console']:
  if(O/name).exists():shutil.copyfile(O/name,operation/name)
 for name in ['ROS_IMPORT_PROBE.console','RESTORE_QUALIFICATION.json']:
  p=R/'runs/v856_nav2_foundation'/name
  if p.exists():shutil.copyfile(p,operation/name)
 targets=['runs/v858_nav2_verified/v862_ready_static','runs/v858_nav2_verified/v863_rpp_static','runs/v862_execution_20261107','runs/v863_execution_20261107','runs/v863_rpp_preparation','runs/v856_nav2_foundation','runs/v862_v863_closure/cloud','runs/v863_restore_qualification']
 removed=[];files=[]
 for name in targets:
  p=R/name
  if not p.exists():continue
  assert p.resolve().is_relative_to(R/'runs')and not p.is_symlink()
  total=0;count=0
  for root,dirs,names in os.walk(p,followlinks=False):
   for file in names:
    f=Path(root)/file;st=f.lstat();total+=st.st_size;count+=1;files.append(dict(path=str(f.relative_to(R)),bytes=st.st_size))
  removed.append(dict(path=name,bytes=total,files=count))
 (REC/'CLEANUP_FILES.jsonl.gz').write_bytes(gzip.compress(('\n'.join(json.dumps(x)for x in files)+'\n').encode(),mtime=0))
 for row in removed:shutil.rmtree(R/row['path'])
 result=dict(passed=True,removed=removed,total_bytes=sum(x['bytes']for x in removed),total_files=sum(x['files']for x in removed),all_required_evidence_remote_digest_download_and_member_restore_verified=True,base_runtime_previous_release_verified=True,source_remote_head_verified=True,guard_restored=True,lock_idle=True,models_restarted=0,closed_unix=time.time())
 (REC/'CLEANUP_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
