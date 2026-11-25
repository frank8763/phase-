"""Already publicly restored old cloud transport duplicates; raw never removed."""
from pathlib import Path
import os,json,hashlib,fcntl,time
R=Path(__file__).resolve().parents[2];O=R/'runs'/Path(__file__).resolve().parent.name
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):assert not p.exists();p.write_text(json.dumps(v,indent=2)+'\n')
def row(p):
 s=p.lstat();return dict(path=str(p.relative_to(R)),bytes=s.st_size,sha256=sha(p),device=s.st_dev,inode=s.st_ino,mtime_ns=s.st_mtime_ns,allocated_bytes=s.st_blocks*512)
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));start=time.monotonic();assert not(O/'RESULT.json').exists();frozen=read(R/'runs/v1978_rpp_first_common_round/SOURCE_FREEZE.json')['files'];candidates={}
 for record in (R/'records').iterdir():
  if not record.is_dir():continue
  public=record/'PUBLIC_RESTORE_QUALIFICATION.json';assets=record/'ASSET_REMOTE_VERIFICATION.json';full=record/'FULL_REMOTE_VERIFIED.json';index=record/'RECORD_INDEX.json'
  if not all(p.is_file()for p in [public,assets,full,index]):continue
  restore=read(public);proof=read(full);entries=read(assets)
  if not(restore.get('passed')and restore.get('public_part_download_sha_passed')and restore.get('whole_reassembly_sha_passed')and restore.get('actual_extracted_members_sha_passed')and proof.get('passed')and proof.get('all_streamed_download_sha_verified')):continue
  if not isinstance(entries,list):continue
  index_entry=next((v for v in entries if v.get('name')=='RECORD_INDEX.json'),None)
  if not index_entry or not index_entry.get('streamed_download_sha_verified')or index_entry['sha256']!=sha(index):continue
  if not isinstance(restore.get('groups'),list):continue
  groups={v['group']for v in restore['groups']}
  for v in entries:
   name=v.get('name','');group=name.split('.tar.')[0]
   if '.tar.'not in name or '.part'not in name or group not in groups or not v.get('streamed_download_sha_verified'):continue
   candidates.setdefault(name,[]).append(dict(asset=v,proofs={str(p.relative_to(R)):sha(p)for p in [public,assets,full,index]}))
 eligible=[]
 for base in (R/'runs').iterdir():
  cloud=base/'cloud'
  if not cloud.is_dir():continue
  for p in cloud.iterdir():
   if p.name not in candidates or not p.is_file()or p.is_symlink()or str(p.relative_to(R))in frozen:continue
   for v in candidates[p.name]:
    if p.stat().st_size==v['asset']['bytes']and sha(p)==v['asset']['sha256']:
     r=row(p);r.update(remote=v,reason='duplicate compressed cloud transport; actual public part/whole/member/index already verified; no raw/source/input/anchor');eligible.append(r);break
 put(O/'ELIGIBLE_MANIFEST.json',dict(passed=True,entries=eligible,models=0))
 locks=[]
 for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
 assert read(R/'CURRENT_EXPERIMENT.json')['active_round']is None and sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';assert all(sha(R/n)==h for n,h in frozen.items())
 for r in eligible:
  assert row(R/r['path'])=={k:r[k]for k in row(R/r['path'])}
  assert all(sha(R/n)==h for n,h in r['remote']['proofs'].items())
 put(O/'DELETE_CLAIM.json',dict(manifest_sha256=sha(O/'ELIGIBLE_MANIFEST.json'),execution_and_owner_locks_held=True,models=0))
 for r in eligible:
  p=R/r['path'];assert row(p)=={k:r[k]for k in row(p)};p.unlink()
 assert all(sha(R/n)==h for n,h in frozen.items())
 result=dict(passed=True,closed=True,models=0,removed_paths=[r['path']for r in eligible],freed_logical_bytes=sum(r['bytes']for r in eligible),freed_allocated_bytes=sum(r['allocated_bytes']for r in eligible),all_original_raw_source_current_inputs_anchors_retained=True,all15897source_SHA_after_verified=True,wall_s=time.monotonic()-start);put(O/'RESULT.json',result);print(json.dumps(result))
if __name__=='__main__':main()
