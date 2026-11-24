"""Complete existing immutable archive transfer; never rearchive or rerun science."""
from pathlib import Path
import importlib.util,json,os,sys,time,fcntl,subprocess,traceback,signal
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name

def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main(kind):
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 I=R/('runs/v1791_lossless_night_rounds/phase_10__no_time'if kind=='runtime'else'runs/v1792_lossless_final_preserve');O=D/kind;O.mkdir(exist_ok=True)
 h=load('v1795_existing_transfer',R/'experiments/v1389_idempotent_storage_transfer/resume.py');h.O=O;h.W=O;h.END=time.time()+600;h.base.ROOT_END=h.END
 start=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('CLOSED_TRANSFER_600S')));signal.alarm(600)
 def guard():assert time.time()<h.END and time.monotonic()<start+600 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot
 originalgh=h.base.gh;originaldownload=h.download
 def gh(*a,**kw):guard();x=originalgh(*a,**kw);guard();return x
 def download(*a,**kw):guard();x=originaldownload(*a,**kw);guard();return x
 h.base.gh=gh;h.download=download
 assert not(O/'ONCE_CLAIM.json').exists()and not(I/'FULL_REMOTE_VERIFIED.json').exists();assert h.read(I/'FINALIZED.json')['passed']
 assert h.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 index=h.read(I/'ARCHIVE_INDEX.json');indexsha=h.sha(I/'ARCHIVE_INDEX.json');assert h.base.usage()+(32+512)*1024**2<15*1024**3
 h.dump(O/'ONCE_CLAIM.json',dict(pid=os.getpid(),boot_id=boot,started_unix=time.time(),started_monotonic=start,index_path=str((I/'ARCHIVE_INDEX.json').relative_to(R)),index_sha256=indexsha,no_reseal_push_ref=True,models=0))
 result=dict(passed=False,closed=False,models=0)
 try:
  tag='phase-v1789-phase-10-no-time-runtime-20261123'if kind=='runtime'else'phase-v1792-overnight-phase-paper-evidence-20261124';h.base.TAG=tag
  sync=h.read(I/('SYNC_RESULT.json'if kind=='runtime'else'SOURCE_SYNC_RESULT.json'));assert sync['head']=='87fa264a2cfe3351faf1e95b2df9143a3b5aa92f'and sync['remote_verified']
  answer=subprocess.run([str(R/'tools/phase_storage_20261107/vendor/gh'),'api','repos/frank8763/phase-/releases/tags/'+tag],cwd=R,capture_output=True,text=True,timeout=30);guard()
  h.dump(O/'LOOKUP.json',dict(returncode=answer.returncode,confirmed_missing='404'in answer.stderr,models=0))
  if answer.returncode==0:release=json.loads(answer.stdout);assert release['target_commitish']==sync['head']
  else:
   assert '404'in answer.stderr,'RELEASE_ABSENCE_NOT_CONFIRMED';request=O/'CREATE.json';h.dump(request,dict(tag_name=tag,target_commitish=sync['head'],name='Phase closed evidence recovery',body='Existing immutable archive only. Original failure preserved. No new model, audit, replay, source push or reseal. Complete block/member/whole/index actual remote SHA before exact transport cleanup.',draft=False,prerelease=False,make_latest='false'));release=json.loads(gh(['api','--method','POST','repos/frank8763/phase-/releases','--input',str(request)],timeout=90))
  h.dump(O/'RELEASE.json',dict(id=release['id'],url=release['html_url']));known=h.assets(h.read(O/'RELEASE.json'))
  for row in index['parts']:
   p=I/'archive'/row['name'];assert h.sha(p)==row['sha256']and p.stat().st_size==row['bytes'];h.ensure_uploaded(p,known)
  h.ensure_uploaded(I/'ARCHIVE_INDEX.json',h.assets(h.read(O/'RELEASE.json')));known=h.assets(h.read(O/'RELEASE.json'))
  Reader=load('v1795_stream_reader',R/'experiments/v1382_weekend_campaign/deliver_full9390_preparation.py').RemoteReader;verify=load('v1795_stream_verify',R/'experiments/v1400_archive_link_schema/resume.py').verify_stream;folder=O/'readback';folder.mkdir();reader=Reader(index['parts'],known,folder,h.download);members=verify(reader,index);assert len(reader.verified)==len(index['parts'])
  p=folder/'ARCHIVE_INDEX.json';h.download(p,known['ARCHIVE_INDEX.json']);assert h.sha(p)==indexsha;p.unlink();folder.rmdir()
  proof=dict(passed=True,source_commit=sync['head'],release_url=release['html_url'],every_asset_actual_download_SHA=True,every_member_SHA_and_link_text=True,whole_archive_SHA=True,recovery_index_download_SHA=True,members=members,archive_bytes=index['archive_bytes'],models=0,physical_admission=False,verified_unix=time.time(),distinct_recovery_path=str(O.relative_to(R)),original_failed_attempt_preserved=True,no_reseal_push_ref=True)
  h.dump(O/'FULL_REMOTE_VERIFIED.json',proof);h.dump(I/'FULL_REMOTE_VERIFIED.json',proof)
  entries=[]
  for row in index['parts']:
   p=I/'archive'/row['name'];st=p.lstat();assert not p.is_symlink()and h.sha(p)==row['sha256']and st.st_size==row['bytes'];entries.append(dict(path=str(p.relative_to(R)),sha256=row['sha256'],bytes=st.st_size,device=st.st_dev,inode=st.st_ino,mtime_ns=st.st_mtime_ns))
  h.dump(O/'CLEANUP_MANIFEST.json',dict(proof_sha256=h.sha(O/'FULL_REMOTE_VERIFIED.json'),entries=entries))
  for e in entries:
   p=R/e['path'];st=p.lstat();assert(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)==(e['device'],e['inode'],e['bytes'],e['mtime_ns'])and h.sha(p)==e['sha256'];p.unlink()
  cleanup=dict(passed=True,only_remote_verified_duplicate_transport_removed=True,exact_SHA_size_mtime_device_inode_manifest=True,manifest_path=str((O/'CLEANUP_MANIFEST.json').relative_to(R)),manifest_sha256=h.sha(O/'CLEANUP_MANIFEST.json'),all_originals_retained=True,models=0,late_outside_archive=True);h.dump(O/'TRANSPORT_CLEANUP.json',cleanup);h.dump(I/'TRANSPORT_CLEANUP.json',cleanup);h.dump(O/'FINALIZED.json',proof)
  # Late canonical completion is distinct from the immutable original failed delivery.
  h.dump(I/'REMOTE_RECOVERY_COMPLETION.json',dict(passed=True,recovery=str(O.relative_to(R)),full_remote_sha256=h.sha(I/'FULL_REMOTE_VERIFIED.json'),cleanup_sha256=h.sha(I/'TRANSPORT_CLEANUP.json'),no_old_finalized_or_error_modified=True,models=0))
  result.update(passed=True,proof=proof)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc(),all_unverified_originals_retained=True)
 finally:result.update(closed=True,wall_s=time.monotonic()-start,closed_unix=time.time());h.dump(O/'RESULT.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main(sys.argv[1]))
