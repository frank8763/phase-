"""Per-case exact archive transport into existing same-source Phase Release."""
from pathlib import Path
import fcntl,hashlib,importlib.util,json,os,signal,time,traceback,subprocess
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;SOURCE=Path(os.environ.get('PHASE_TRANSPORT_SOURCE_ROOT',str(R/'runs/v1913_dwa_night_qualified')));RID=os.environ.get('PHASE_EVENING_ASSIGNMENT','common_07__DWA');S=SOURCE/'rounds'/RID;D=SOURCE/'runtime_archives'/RID;O=Path(os.environ.get('PHASE_TRANSPORT_OUTPUT',str(R/'runs/v1917_dwa_day_transport_recovery/episode01')))
WALL=time.time();MONO=time.monotonic();BOOT=Path('/proc/sys/kernel/random/boot_id').read_text().strip();RELEASE_ID=456739514
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def guard(*_):assert time.time()<WALL+600 and time.monotonic()<MONO+600 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT,'IO600_DUAL_CLOCK'
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 assert RID in [f'common_{i:02d}__DWA'for i in range(7,13)]
 O.mkdir(parents=True,exist_ok=True);assert not(O/'ONCE_CLAIM.json').exists()and not(D/'FULL_REMOTE_VERIFIED.json').exists()
 closed=read(S/'COMPLETION.json');assert closed['closed']and closed['review_restored']and closed['lock_idle']
 identity=read(S/'OWNED_CHILD.json');p=Path('/proc',str(identity['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=identity['start_ticks']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert all(sha(R/n)==h for n,h in read(SOURCE/'SOURCE_FREEZE.json')['files'].items())
 recovery=read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']
 index=read(D/'ARCHIVE_INDEX.json');sync=read(D/'SOURCE_SYNC_RESULT.json');assert sync['remote_verified']and not sync['push_executed']and not sync['ref_executed']and read(D/'FINALIZED.json')['passed']and sync['head']==recovery['source_commit']
 for row in index['parts']:
  p=D/'archive'/row['name'];assert p.stat().st_size==row['bytes']and sha(p)==row['sha256']
 put(O/'ONCE_CLAIM.json',dict(pid=os.getpid(),unix=WALL,maximum_s=600,index_sha256=sha(D/'ARCHIVE_INDEX.json'),source_sync_sha256=sha(D/'SOURCE_SYNC_RESULT.json'),existing_release_id=RELEASE_ID,release_POSTs=0,no_push_ref_reseal_or_model=True))
 canonical=D/'remote_delivery';canonical.mkdir(exist_ok=True)
 if(canonical/'CLAIM.json').exists():assert not Path('/proc',str(read(canonical/'CLAIM.json')['pid'])).exists()
 else:put(canonical/'CLAIM.json',dict(pid=os.getpid(),boot_id=BOOT,transport_owner=str(O.relative_to(R))))
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('IO600_STOP')));signal.setitimer(signal.ITIMER_REAL,600)
 h=load('v1898_transfer',R/'experiments/v1389_idempotent_storage_transfer/resume.py');h.O=O/'remote_delivery';h.W=h.O;h.O.mkdir();h.END=WALL+600;h.base.ROOT_END=WALL+600
 receipts=O/'http_receipts';receipts.mkdir()
 counter=[0]
 def receipt(value):
  counter[0]+=1;put(receipts/(str(counter[0])+'.json'),value)
 http=load('v1917_repaired_transport',C/'net.py').Client(R,guard,receipt);h.base.gh=http.gh
 Reader=load('v1898_reader',R/'experiments/v1382_weekend_campaign/deliver_full9390_preparation.py').RemoteReader;verify=load('v1898_verifier',R/'experiments/v1400_archive_link_schema/resume.py').verify_stream
 result=dict(passed=False,closed=False,models=0,new_release_POST=False,new_push=False,new_ref=False,new_archive=False)
 try:
  assert h.base.usage()+(32+512)*1024**2<15*1024**3
  release=http.request('GET','https://api.github.com/repos/frank8763/phase-/releases/'+str(RELEASE_ID));assert release['target_commitish']==sync['head']
  assert read(R/'runs/v1913_dwa_night_qualified/rounds/common_06__DWA/POST_ROUND_STORAGE_BARRIER.json')['passed']
  http.release_id=RELEASE_ID;h.base.TAG=release['tag_name'];h.dump(h.O/'RELEASE.json',dict(id=RELEASE_ID,url=release['html_url']));h.dump(h.O/'CLAIM.json',dict(pid=os.getpid(),source_index_sha256=sha(D/'ARCHIVE_INDEX.json')))
  alias=D/(RID+'.ARCHIVE_INDEX.json')
  if not alias.exists():alias.write_bytes((D/'ARCHIVE_INDEX.json').read_bytes())
  assert alias.is_file()and not alias.is_symlink()and sha(alias)==sha(D/'ARCHIVE_INDEX.json')
  for row in index['parts']:h.ensure_uploaded(D/'archive'/row['name'],h.assets(h.read(h.O/'RELEASE.json')))
  h.ensure_uploaded(alias,h.assets(h.read(h.O/'RELEASE.json')));known=h.assets(h.read(h.O/'RELEASE.json'));folder=h.O/'readback';folder.mkdir();reader=Reader(index['parts'],known,folder,h.download);count=verify(reader,index);assert len(reader.verified)==len(index['parts'])
  recovered=folder/'ARCHIVE_INDEX.json';h.download(recovered,known[alias.name]);assert sha(recovered)==sha(D/'ARCHIVE_INDEX.json')
  proof=dict(passed=True,source_commit=sync['head'],release_url=release['html_url'],existing_same_source_release_id=RELEASE_ID,assignment_id=RID,remote_index_asset_name=alias.name,local_index_sha256=sha(D/'ARCHIVE_INDEX.json'),every_asset_actual_download_SHA=True,every_member_SHA_and_link_text=True,whole_archive_SHA=True,recovery_index_download_SHA=True,members=count,archive_bytes=index['archive_bytes'],models=0,physical_admission=False,verified_unix=time.time(),distinct_transport_owner=str(O.relative_to(R)),no_second_push_ref_reseal=True,no_new_release_POST=True,scientific_result_not_inferred_from_release_name=True)
  put(D/'FULL_REMOTE_VERIFIED.json',proof);entries=[]
  for p,expected in [(D/'archive'/row['name'],row['sha256'])for row in index['parts']]+[(alias,sha(D/'ARCHIVE_INDEX.json'))]:
   st=p.lstat();assert p.is_file()and not p.is_symlink()and sha(p)==expected;entries.append(dict(path=str(p.relative_to(R)),sha256=expected,bytes=st.st_size,device=st.st_dev,inode=st.st_ino,mtime_ns=st.st_mtime_ns))
  put(D/'TRANSPORT_CLEANUP_MANIFEST.json',dict(verified_remote_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),entries=entries))
  for row in entries:
   p=R/row['path'];st=p.lstat();assert(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)==(row['device'],row['inode'],row['bytes'],row['mtime_ns'])and sha(p)==row['sha256'];p.unlink()
  recovered.unlink();folder.rmdir();put(D/'TRANSPORT_CLEANUP.json',dict(passed=True,only_remote_verified_duplicate_transport_removed=True,all_original_qualification_inputs_and_outputs_retained=True,exact_SHA_size_mtime_device_inode_manifest=True,models=0));assert not(canonical/'FINALIZED.json').exists()
  put(canonical/'FINALIZED.json',proof);put(h.O/'FINALIZED.json',proof);result.update(passed=True,proof=proof)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'ERROR.json',dict(error=repr(e),all_unverified_originals_retained=True))
 finally:result.update(closed=True,wall_s=time.monotonic()-MONO);put(O/'RESULT.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
