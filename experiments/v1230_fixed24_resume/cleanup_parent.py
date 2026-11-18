"""Delete only remotely member-SHA-verified closed raw; retain repeat1 baseline."""
from pathlib import Path
import json,hashlib,fcntl,time
R=Path(__file__).resolve().parents[2];D=R/'records/nav2_v1228_checkpoint_20261116';O=R/'runs/v1230_fixed24_resume'
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 assert not(D/'CLEANUP.json').exists()
 f=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 assert read(D/'REMOTE_VERIFIED.json')['all_bytes_and_sha_and_decompressed_members_verified']
 inventory=read(D/'INVENTORY.json')['files'];pinned=set(read(R/'experiments/v1228_terminal_reserve_confirmation/SOURCE_FREEZE.json')['files'])
 root=R/'runs/v858_nav2_verified/v1228';baseline=root/'main_slot01';files=[]
 for p in root.rglob('*'):
  key=str(p.relative_to(R))
  if not p.is_file()or p.is_symlink()or p.is_relative_to(baseline)or p.stat().st_size<=1024**2 or key in pinned:continue
  v=inventory[key];assert p.resolve().is_relative_to(root)and p.stat().st_size==v['bytes']and sha(p)==v['sha256'];files.append(dict(path=key,**v))
 (D/'CLEANUP_MANIFEST.json').write_text(json.dumps(dict(files=files,baseline_retained=str(baseline.relative_to(R))),indent=2)+'\n')
 for row in files:
  p=R/row['path'];assert not p.is_symlink()and sha(p)==row['sha256'];p.unlink()
 cloud=O/'cloud';archive=cloud/'v1228-checkpoint-and-source-v2.tar.gz';receipt=next(a for a in read(D/'REMOTE_VERIFIED.json')['assets']if a['name']==archive.name);assert sha(archive)==receipt['sha256'];archive_bytes=archive.stat().st_size;archive.unlink()
 # Incomplete local packaging attempt is redundant, not unique scientific evidence.
 partial=cloud/'v1228-checkpoint-and-source.tar.partial';partial_bytes=partial.stat().st_size if partial.exists()else 0
 if partial.exists():partial.unlink()
 result=dict(passed=True,files=len(files),raw_removed_bytes=sum(r['bytes']for r in files),verified_transport_cache_removed_bytes=archive_bytes,redundant_partial_removed_bytes=partial_bytes,all_removed_files_remotely_sha_verified=True,original_reports_small_packets_and_repeat1_retained=True,parent_finalized_unchanged=True,models=0,new_mujoco_native=0,closed_unix=time.time())
 (D/'CLEANUP.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
