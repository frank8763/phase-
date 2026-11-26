"""Move only remotely verified closed DWA prediction duplicates to cold cache."""
from pathlib import Path
import fcntl,gzip,hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def full(p):
 x=read(p)
 if 'inherit_freeze_path'in x:
  parent=R/x['inherit_freeze_path'];assert sha(parent)==x['inherit_freeze_sha256'];f=full(parent);assert all(n not in f or f[n]==h for n,h in x['files'].items());f.update(x['files']);return f
 return x['files']
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));D.mkdir(exist_ok=True)
 assert not(D/'ONCE.json').exists();put(D/'ONCE.json',dict(unix=time.time(),models=0,scope='closed_DWA_derived_prediction_cache_only'))
 lock=(D/'cleanup.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 protected={}
 for path in [R/'runs/v1990_rpp_unexecuted_output_audit/SOURCE_FREEZE.json',R/'runs/v2027_mppi_journal_snapshot_consistency/SOURCE_FREEZE.json']:protected.update(full(path))
 assert all(sha(R/n)==h for n,h in protected.items())
 ledger=read(R/'runs/v1805_common_algorithm_registry/LEDGER.json');rows=[];proofs=[];total=0
 for slot in ledger['slots']:
  if slot['method']!='DWA'or slot['task_id']not in [f'common_{i:02d}'for i in range(5,13)]:continue
  assert slot['closed']and slot['remote_closed'];root=(R/slot['result_path']).parent;actual=root/'actual';barrier=root/'POST_ROUND_STORAGE_BARRIER.json';b=read(barrier);assert b['passed']
  completion=read(root/'COMPLETION.json');assert completion['closed']
  child=root/'OWNED_CHILD.json'
  if child.exists():
   z=read(child);p=Path('/proc',str(z['pid']))
   assert not p.exists()or p.joinpath('stat').read_text().split(') ',1)[1].split()[19]!=str(z['start_ticks']),'EXACT_CLOSED_DWA_CHILD_STILL_LIVE'
  if 'remote_proof_path'in b:
   remote=R/b['remote_proof_path'];assert sha(remote)==b['remote_proof_sha256']
  else:
   candidates=[R/n for n,h in b['proof_paths_SHA256'].items()if n.endswith('/FULL_REMOTE_VERIFIED.json')];assert len(candidates)==1;remote=candidates[0];assert sha(remote)==b['proof_paths_SHA256'][str(remote.relative_to(R))]
  r=read(remote);assert r['passed']
  assert all(r[k]for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA'])
  index=remote.parent/'ARCHIVE_INDEX.json';members={x['path']:x for x in read(index)['files']};assert read(remote.parent/'TRANSPORT_CLEANUP.json')['passed']
  # Current inputs, source proofs and numerical anchors are protected by hashes.
  own=full(root/'SOURCE_FREEZE.json');protected.update(own)
  tracked=set(subprocess.check_output(['git','ls-files','--',str(actual.relative_to(R))],cwd=R,text=True).splitlines())
  chosen=[]
  for p in actual.iterdir():
   if not p.is_file()or p.is_symlink():continue
   eligible=(p.name=='DWA_PREDICTIONS.pack'or(p.name.startswith('cycle_')and p.suffix in {'.npz','.json'}))
   n=str(p.relative_to(R))
   if not eligible or n in protected or n in tracked:continue
   st=p.lstat();assert st.st_nlink==1 and n in members and st.st_size==members[n]['bytes']and sha(p)==members[n]['sha256']
   chosen.append(dict(path=n,sha256=members[n]['sha256'],bytes=st.st_size,allocated_bytes=st.st_blocks*512,device=st.st_dev,inode=st.st_ino,mtime_ns=st.st_mtime_ns))
  rows.extend(chosen);total+=sum(x['allocated_bytes']for x in chosen)
  proofs.append(dict(task=slot['task_id'],root=str(root.relative_to(R)),barrier_sha256=sha(barrier),remote_proof_path=str(remote.relative_to(R)),remote_proof_sha256=sha(remote),index_path=str(index.relative_to(R)),index_sha256=sha(index),entries=len(chosen)))
  if total>=600*1024**2:break
 assert rows and total>=400*1024**2,'INSUFFICIENT_VERIFIED_DERIVED_CACHE'
 assert all(sha(R/n)==h for n,h in protected.items())
 manifest=D/'ELIGIBLE_MANIFEST.jsonl.gz'
 with manifest.open('xb')as raw,gzip.GzipFile(fileobj=raw,mode='wb',mtime=0)as f:
  for row in rows:f.write(json.dumps(row,separators=(',',':')).encode()+b'\n')
 assert manifest.stat().st_size<16*1024**2
 put(D/'ELIGIBILITY_PROOF.json',dict(passed=True,entries=len(rows),allocated_bytes=total,source_members_protected=len(protected),all_protected_SHA_verified=True,proofs=proofs,manifest_sha256=sha(manifest),preserved_local=['all_canonical_results_and_first_secondary_errors','all_actual_physical_traces_contacts_sensors_controls','all_actual_journals_initial_final_packets_Nplus1','all_source_current_inputs_and_anchors','all_runtime_indices_and_remote_proofs'],deleted_scope='closed_DWA_derived_cycle_predictions_only',new_numerical_calls=0))
 # Closed root, exact identity and bytes revalidated immediately before unlink.
 for row in rows:
  p=R/row['path'];st=p.lstat();assert(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_nlink)==(row['device'],row['inode'],row['bytes'],row['mtime_ns'],1)and sha(p)==row['sha256'];p.unlink()
 assert all(sha(R/n)==h for n,h in protected.items())
 put(D/'RESULT.json',dict(passed=True,entries=len(rows),freed_allocated_bytes=total,exact_SHA_size_mtime_device_inode_verified=True,all_source_SHA_after=True,only_remotely_verified_closed_derived_duplicates=True,native_physical_raw_and_results_retained=True,new_models_physics_replay_audit=0,unix=time.time()))
 print(json.dumps(read(D/'RESULT.json')))
if __name__=='__main__':main()
