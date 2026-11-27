"""Lossless closed-cycle byte packing + exact remote-verified derived retirement."""
from pathlib import Path
import fcntl,gzip,tarfile,hashlib,io,os,subprocess,json,time
import evidence as e
R=e.R;S=e.ROOT;STUDY=R/'runs/v2095_svg_common_full_route'
def retire(rid):
 os.sched_setaffinity(0,{5});O=STUDY/'rounds'/rid;T=S/'runtime_archives'/rid;B=S/'closed_cache'/rid;B.mkdir(parents=True,exist_ok=True)
 assert not(B/'RESULT.json').exists()and e.read(O/'POST_ROUND_STORAGE_BARRIER.json')['passed']and e.read(O/'COMPLETION.json')['closed']
 locks=[]
 for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
 assert e.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 i=e.read(O/'OWNED_CHILD.json');p=Path('/proc',str(i['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=i['start_ticks']
 remote=e.read(T/'FULL_REMOTE_VERIFIED.json');assert remote['passed']and all(remote[k]for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA'])and e.read(T/'TRANSPORT_CLEANUP.json')['passed']
 source=e.read(S/'SOURCE_FREEZE.json')['files'];assert all(e.sha(R/n)==h for n,h in source.items())
 members={x['path']:x for x in e.read(T/'ARCHIVE_INDEX.json')['files']};A=O/'actual'
 tracked=set(subprocess.check_output(['git','ls-files','--',str(A.relative_to(R))],cwd=R,text=True).splitlines())
 allcycles=sorted(A.glob('cycle_*.json'));origins=sorted(A.glob('cycle_*_origin.json'));keep=set()
 if origins:
  first=origins[0].stem[:12];last=origins[-1].stem[:12]
  keep={p for p in allcycles if p.stem.startswith((first,last))}
 targets=[p for p in allcycles if p not in keep and str(p.relative_to(R))not in source and str(p.relative_to(R))not in tracked]
 # Lossless local container retains every old measured input/candidate/proof byte,
 # index plus remote duplicate. Current files and first/last anchors never removed.
 cold=A/'CLOSED_CYCLE_BYTES.tar.gz';assert not cold.exists();entries=[]
 with cold.open('xb')as f,gzip.GzipFile(fileobj=f,mode='wb',compresslevel=3,mtime=0)as z,tarfile.open(fileobj=z,mode='w|')as tar:
  for p in targets:
   n=str(p.relative_to(R));st=p.lstat();row=members[n];assert not p.is_symlink()and st.st_nlink==1 and st.st_size==row['bytes']and e.sha(p)==row['sha256']
   raw=p.read_bytes();info=tarfile.TarInfo(p.name);info.size=len(raw);tar.addfile(info,io.BytesIO(raw));entries.append(dict(path=n,name=p.name,sha256=row['sha256'],bytes=st.st_size,allocated_bytes=st.st_blocks*512,device=st.st_dev,inode=st.st_ino,mtime_ns=st.st_mtime_ns))
   assert f.tell()<8*1024**2,'COLD_LOCAL_CONTAINER_CAP'
 assert cold.stat().st_size<8*1024**2
 wanted={x['name']:x for x in entries};seen=set()
 with tarfile.open(cold,'r:gz')as tar:
  for m in tar:
   assert m.isfile()and m.name in wanted and m.name not in seen;raw=tar.extractfile(m).read();row=wanted[m.name];assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256'];seen.add(m.name)
 assert seen==set(wanted)
 p=A/'DWA_PREDICTIONS.pack';packentry=None
 if p.exists():
  n=str(p.relative_to(R));st=p.lstat();row=members[n];assert n not in source and n not in tracked and not p.is_symlink()and st.st_nlink==1 and st.st_size==row['bytes']and e.sha(p)==row['sha256']
  pack=e.load('closed_pack_original_reader',R/'experiments/v1903_dwa_durable_proof_pack/proof_pack.py')
  shadows=sorted(A.glob('cycle_*_shadow.json'))
  with p.open('rb')as stream:
   for label,proofpath in [('FIRST',shadows[0]),('TERMINAL_REFUSAL_OR_LAST',shadows[-1])]:
    proof=e.read(proofpath);r=proof['hybrid_evidence'];_,end=pack.read_record(stream,r['offset'],proof['arrays']);assert end==r['offset']+r['frame_bytes'];stream.seek(r['offset']);raw=stream.read(r['frame_bytes']);anchor=A/(label+'.prediction_record');anchor.write_bytes(raw);assert e.sha(anchor)==hashlib.sha256(raw).hexdigest()
  packentry=dict(path=n,sha256=row['sha256'],bytes=st.st_size,allocated_bytes=st.st_blocks*512,device=st.st_dev,inode=st.st_ino,mtime_ns=st.st_mtime_ns)
 manifest=dict(entries=entries,pack=packentry,local_container_path=str(cold.relative_to(R)),local_container_sha256=e.sha(cold),local_container_every_original_member_byte_verified=True,remote_index_path=str((T/'ARCHIVE_INDEX.json').relative_to(R)),remote_index_sha256=e.sha(T/'ARCHIVE_INDEX.json'),remote_proof_sha256=e.sha(T/'FULL_REMOTE_VERIFIED.json'),all_actual_fullstates_journal_sensors_contacts_model_initial_final_raw_paths_retained=True,first_and_last_cycle_raw_anchors_retained=True)
 raw=json.dumps(manifest,separators=(',',':'),allow_nan=False).encode();encoded=gzip.compress(raw,compresslevel=3,mtime=0);assert len(encoded)<=2*1024**2
 path=B/'EXACT_MANIFEST.json.gz';path.write_bytes(encoded);assert gzip.decompress(path.read_bytes())==raw
 for x in entries+([packentry]if packentry else[]):
  p=R/x['path'];st=p.lstat();assert(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_nlink)==(x['device'],x['inode'],x['bytes'],x['mtime_ns'],1)and e.sha(p)==x['sha256'];p.unlink()
 assert all(e.sha(R/n)==h for n,h in source.items())
 result=dict(passed=True,models=0,physics=0,replay=0,old_audit_rerun=False,cycle_entries_losslessly_packed=len(entries),pack_remote_retired=bool(packentry),actual_allocated_bytes=int(subprocess.check_output(['du','-sx','-B1',str(A)]).split()[0]),no_current_source_or_anchor_removed=True,restore_old_cycle_names_from_local_lossless_container_for_old_audit=True,restore_old_full_prediction_pack_only_from_exact_remote=True)
 e.put(B/'RESULT.json',result);return result
