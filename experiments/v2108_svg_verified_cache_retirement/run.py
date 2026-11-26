from pathlib import Path
import fcntl,hashlib,importlib.util,json,os,subprocess,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;W=R/'runs'/C.name;STUDY=R/'runs/v2095_svg_common_full_route'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 assert not p.exists();p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def freeze(p):
 x=read(p);base=freeze(R/x['inherit_freeze_path'])if'inherit_freeze_path'in x else{}
 if'inherit_freeze_path'in x:assert sha(R/x['inherit_freeze_path'])==x['inherit_freeze_sha256']
 assert all(n not in base or base[n]==h for n,h in x['files'].items());return dict(base,**x['files'])
def main():
 os.sched_setaffinity(0,{5});assert not(W/'RESULT.json').exists();locks=[]
 for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 allsource=freeze(R/'runs/v2105_svg03_exact_transport_parent/SOURCE_FREEZE.json');assert all(sha(R/n)==h for n,h in allsource.items())
 packpath=R/'experiments/v1903_dwa_durable_proof_pack/proof_pack.py';s=importlib.util.spec_from_file_location('original_pack_checksums_only',packpath);pack=importlib.util.module_from_spec(s);s.loader.exec_module(pack)
 entries=[]
 for rid,root in [('common_02__SVGMPPI','runs/v2099_svg_direct_array_scope'),('common_03__SVGMPPI','runs/v2105_svg03_exact_transport_parent')]:
  O=STUDY/'rounds'/rid;T=R/root/'runtime_archives'/rid;B=W/rid;B.mkdir()
  assert read(O/'COMPLETION.json')['closed']and read(O/'POST_ROUND_STORAGE_BARRIER.json')['passed']
  i=read(O/'OWNED_CHILD.json');p=Path('/proc',str(i['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
  remote=read(T/'FULL_REMOTE_VERIFIED.json');assert remote['passed']and all(remote[k]for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA'])and read(T/'TRANSPORT_CLEANUP.json')['passed']
  path=O/'actual/DWA_PREDICTIONS.pack';name=str(path.relative_to(R));index=read(T/'ARCHIVE_INDEX.json');row=next(x for x in index['files']if x['path']==name)
  assert name not in allsource and not subprocess.check_output(['git','ls-files','--',name],cwd=R)
  st=path.lstat();assert path.is_file()and not path.is_symlink()and st.st_nlink==1 and st.st_size==row['bytes']and sha(path)==row['sha256']
  proofs=[read(p)for p in sorted((O/'actual').glob('cycle_*_shadow.json'))];assert proofs
  anchors=[]
  with path.open('rb')as stream:
   for label,proof in [('FIRST',proofs[0]),('TERMINAL_REFUSAL',proofs[-1])]:
    r=proof['hybrid_evidence'];raw,end=pack.read_record(stream,r['offset'],proof['arrays']);assert end==r['offset']+r['frame_bytes']
    stream.seek(r['offset']);frame=stream.read(r['frame_bytes']);target=B/(label+'.original_record');target.write_bytes(frame);assert target.read_bytes()==frame
    anchors.append(dict(label=label,path=str(target.relative_to(R)),sha256=sha(target),original_offset=r['offset'],original_frame_bytes=len(frame),original_pack_sha256=row['sha256'],proof_sha256=hashlib.sha256(json.dumps(proof,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
  entries.append(dict(path=name,sha256=row['sha256'],bytes=st.st_size,allocated_bytes=st.st_blocks*512,device=st.st_dev,inode=st.st_ino,mtime_ns=st.st_mtime_ns,nlink=1,index_path=str((T/'ARCHIVE_INDEX.json').relative_to(R)),index_sha256=sha(T/'ARCHIVE_INDEX.json'),remote_proof_path=str((T/'FULL_REMOTE_VERIFIED.json').relative_to(R)),remote_proof_sha256=sha(T/'FULL_REMOTE_VERIFIED.json'),anchors=anchors))
 put(W/'ELIGIBLE_MANIFEST.json',dict(models=0,entries=entries))
 for x in entries:
  p=R/x['path'];st=p.lstat();assert(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_nlink)==(x['device'],x['inode'],x['bytes'],x['mtime_ns'],1)and sha(p)==x['sha256'];p.unlink()
 f=(STUDY/'retention.lock').open('a+');fcntl.flock(f,fcntl.LOCK_EX);p=STUDY/'RETENTION_STATE.json';old=read(p);(W/'ORIGINAL_RETENTION_STATE.json').write_bytes(p.read_bytes());sizes={}
 for rid in old['charged']:
  O=STUDY/'rounds'/rid;assert read(O/'POST_ROUND_STORAGE_BARRIER.json')['passed'];sizes[rid]=int(subprocess.check_output(['du','-sx','-B1',str(O/'actual')],timeout=10).split()[0])
 new=dict(old,retained_actual_bytes=sum(sizes.values()));assert new['retained_actual_bytes']<=old['retained_actual_bytes'];tmp=p.with_suffix('.reconcile.tmp');tmp.write_text(json.dumps(new,separators=(',',':'))+'\n');tmp.replace(p)
 assert all(sha(R/n)==h for n,h in allsource.items())
 result=dict(passed=True,models=0,physics=0,replay=0,audit_calls=0,freed_allocated_bytes=sum(x['allocated_bytes']for x in entries),old_retention=old,new_retention=new,actual_sizes_alreadycharged=sizes,original_sources_inputs_actuals_and_anchors_retained=True,only_exact_remote_verified_derived_pack_removed=True,full_old_pack_now_requires_exact_remote_restore=True)
 put(W/'RESULT.json',result);print(json.dumps(result))
if __name__=='__main__':main()
