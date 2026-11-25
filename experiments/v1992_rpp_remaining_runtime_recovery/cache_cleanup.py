"""Exact remotely verified THIS round cache cleanup; small closure stays local."""
from pathlib import Path
import fcntl,hashlib,json,os,time,gzip
R=Path(__file__).resolve().parents[2];ROOT=R/'runs/v1990_rpp_unexecuted_output_audit';RID=os.environ['PHASE_RPP_ASSIGNMENT'];assert RID in [f'common_{i:02d}__RPP'for i in range(3,13)];S=ROOT/'rounds'/RID;D=ROOT/'runtime_archives'/RID
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def put(p,v):assert not p.exists();p.write_text(json.dumps(v,indent=2)+'\n')
def main():
 assert not(S/'LOCAL_RAW_CACHE_CLEANUP.json').exists();remote=read(D/'FULL_REMOTE_VERIFIED.json');assert remote['passed']and all(remote[k]for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA']);assert read(D/'TRANSPORT_CLEANUP.json')['passed']and read(D/'remote_delivery/RESULT.json')['passed'];assert not Path('/proc',str(read(D/'remote_delivery/CLAIM.json')['pid'])).exists();assert read(S/'COMPLETION.json')['closed']and read(S/'COMPLETION.json')['review_restored']and read(S/'COMPLETION.json')['lock_idle']
 frozen=read(ROOT/'SOURCE_FREEZE.json')['files'];members={row['path']:row for row in read(D/'ARCHIVE_INDEX.json')['files']};entries=[];retained=[]
 keep={'RESULT.json','FINAL_INDEPENDENT_AUDIT.json','FUNCTIONAL_AUDIT_INPUT.json','ACTUAL_FINAL_PACKET.json','ACTUAL_PROGRESS.json','NAVIGATION_PROGRESS.json','RPP_NATIVE_CLOSED.json','RPP_NATIVE_CONSOLE.json','RPP_NATIVE_SECONDARY_CLOSE_ERROR.json','RPP_NATIVE_INITIALIZATION_FAILURE.json','RPP_NATIVE_PEER_IDENTITY.json','SETUP.json','CANONICAL_INITIAL_PACKET.json'}
 locks=[]
 for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 for p in(S/'actual').rglob('*'):
  if not p.is_file()or p.is_symlink():continue
  name=str(p.relative_to(R));assert name.startswith(str(S.relative_to(R))+'/actual/')and name not in frozen
  if p.name in keep:retained.append(name);continue
  st=p.lstat();row=members[name];assert row['sha256']==sha(p)and row['bytes']==st.st_size
  entries.append(dict(path=name,sha256=row['sha256'],bytes=st.st_size,device=st.st_dev,inode=st.st_ino,mtime_ns=st.st_mtime_ns,allocated_bytes=st.st_blocks*512))
 raw=json.dumps(entries,separators=(',',':')).encode();packed=gzip.compress(raw,compresslevel=3,mtime=0);assert len(packed)<=2*1024**2,'CLEANUP_MANIFEST_2MIB_CAP';manifest=S/'LOCAL_RAW_CACHE_ENTRIES.json.gz';assert not manifest.exists();manifest.write_bytes(packed)
 put(S/'LOCAL_RAW_CACHE_CLEANUP_MANIFEST.json',dict(remote_proof_path=str((D/'FULL_REMOTE_VERIFIED.json').relative_to(R)),remote_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),archive_index_path=str((D/'ARCHIVE_INDEX.json').relative_to(R)),archive_index_sha256=sha(D/'ARCHIVE_INDEX.json'),entries_gzip_path=str(manifest.relative_to(R)),entries_gzip_sha256=sha(manifest),entries_count=len(entries),retained=retained,full_remote_recovery_required_for_cold_raw=True,old_inputs_sources_anchors_untouched=True))
 for row in entries:
  p=R/row['path'];st=p.lstat();assert(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)==(row['device'],row['inode'],row['bytes'],row['mtime_ns'])and sha(p)==row['sha256'];p.unlink()
 assert all(sha(R/n)==h for n,h in frozen.items())
 proof=dict(passed=True,new_round_restorable_cache_only=True,old_raw_inputs_sources_anchors_untouched=True,exact_SHA_size_mtime_device_inode=True,local_cache_entries=len(entries),freed_allocated_bytes=sum(x['allocated_bytes']for x in entries),manifest_sha256=sha(S/'LOCAL_RAW_CACHE_CLEANUP_MANIFEST.json'),all_source_SHA_unchanged=True,models=0);put(S/'LOCAL_RAW_CACHE_CLEANUP.json',proof);print(json.dumps(proof))
if __name__=='__main__':main()
