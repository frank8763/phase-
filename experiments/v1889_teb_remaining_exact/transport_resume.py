"""First bounded transport continuation of an unchanged failed-runtime archive."""
from pathlib import Path
import fcntl,hashlib,importlib.util,json,os,signal,subprocess,time,traceback
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;RID=os.environ['PHASE_EVENING_ASSIGNMENT'];O=R/'runs/v1889_teb_remaining_exact/transport_resume'/RID
S=R/'runs/v1889_teb_remaining_exact/rounds'/RID;D=R/'runs/v1889_teb_remaining_exact/runtime_archives'/RID
START=time.monotonic();WALL=time.time();BOOT=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
TAG='phase-v1889-'+RID.replace('_','-').lower()+'-runtime-20261124'
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def put(p,v):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n');t.replace(p)
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def guard(*_):
 assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==BOOT
 assert time.monotonic()<START+600 and time.time()<WALL+600,'IO_RESUME_DUAL_CLOCK_STOP'
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 assert not(O/'ONCE_CLAIM.json').exists()and not(D/'FULL_REMOTE_VERIFIED.json').exists()
 closed=read(S/'COMPLETION.json');assert closed['closed']and closed['review_restored']and closed['lock_idle']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for root,name in [(S,'OWNED_CHILD.json'),(R/'runs/v1871_rpccr_remaining_queue','BACKGROUND_OWNED_CHILD.json'),(D/'remote_delivery','CLAIM.json')]:
  identity=read(root/name);p=Path('/proc',str(identity['pid']),'stat')
  assert not p.exists()or ('start_ticks'in identity and p.read_text().split(') ',1)[1].split()[19]!=identity['start_ticks'])
 assert all(sha(R/n)==h for n,h in read(S/'SOURCE_FREEZE.json')['files'].items())
 index=read(D/'ARCHIVE_INDEX.json');indexsha=sha(D/'ARCHIVE_INDEX.json');assert read(D/'FINALIZED.json')['passed']
 sync=read(D/'SOURCE_SYNC_RESULT.json');assert sync['remote_verified']and not sync['push_executed']and not sync['ref_executed']
 for row in index['parts']:
  p=D/'archive'/row['name'];assert p.stat().st_size==row['bytes']and sha(p)==row['sha256']and row['bytes']<=32*1024**2
 assert int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0])+(32+512)*1024**2<15*1024**3
 O.mkdir(exist_ok=True)
 put(O/'ONCE_CLAIM.json',dict(pid=os.getpid(),boot_id=BOOT,unix=WALL,maximum_s=600,index_path=str((D/'ARCHIVE_INDEX.json').relative_to(R)),index_sha256=indexsha,old_delivery_error_sha256=sha(D/'remote_delivery/ERROR.json'),no_new_archive_or_push_or_model=True))
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('IO_RESUME600_STOP')));signal.setitimer(signal.ITIMER_REAL,600)
 h=load('v1839_unchanged_transfer_primitives',R/'experiments/v1389_idempotent_storage_transfer/resume.py');h.O=O;h.W=D/'remote_delivery';h.END=WALL+600;h.base.ROOT_END=WALL+600;h.base.TAG=TAG
 original=h.base.gh
 def bounded(*a,**kw):guard();v=original(*a,**kw);guard();return v
 h.base.gh=bounded
 Reader=load('v1839_original_stream_reader',R/'experiments/v1382_weekend_campaign/deliver_full9390_preparation.py').RemoteReader
 verify=load('v1839_original_stream_verifier',R/'experiments/v1400_archive_link_schema/resume.py').verify_stream
 result=dict(passed=False,closed=False,models=0,physical_native=0,replay_native=0,new_push=False,new_archive=False)
 try:
  gh=str(R/'tools/phase_storage_20261107/vendor/gh')
  # Only readonly lookups retry; a release is created once only after exact404.
  lookup=None
  for number in range(3):
   guard();lookup=subprocess.run([gh,'api','repos/frank8763/phase-/releases/tags/'+TAG],cwd=R,capture_output=True,text=True,timeout=30)
   put(O/('RELEASE_LOOKUP_%d.json'%number),dict(returncode=lookup.returncode,confirmed_missing=lookup.returncode!=0 and '404'in lookup.stderr,stderr=lookup.stderr[:3000],models=0))
   if lookup.returncode==0 or '404'in lookup.stderr:break
  assert lookup is not None
  if lookup.returncode==0:release=json.loads(lookup.stdout)
  else:
   assert '404'in lookup.stderr,'RELEASE_ABSENCE_NOT_CONFIRMED_AFTER_BOUNDED_LOOKUP'
   request=D/'remote_delivery/CREATE_RELEASE.json';assert read(request)['tag_name']==TAG and read(request)['target_commitish']==sync['head']
   put(O/'CREATE_ONCE_CLAIM.json',dict(unix=time.time(),request_sha256=sha(request),source_commit=sync['head'],confirmed404=True))
   answer=subprocess.run([gh,'api','--method','POST','repos/frank8763/phase-/releases','--input',str(request)],cwd=R,capture_output=True,text=True,timeout=90)
   put(O/'CREATE_RETURN.json',dict(returncode=answer.returncode,stderr=answer.stderr[:3000]))
   if answer.returncode==0:release=json.loads(answer.stdout)
   else:
    # Never repeat POST; query actualremote once after an uncertain create.
    release=json.loads(h.base.gh(['api','repos/frank8763/phase-/releases/tags/'+TAG],timeout=30))
  assert release['target_commitish']==sync['head']
  if(D/'remote_delivery/RELEASE.json').exists():assert release['id']==read(D/'remote_delivery/RELEASE.json')['id']
  else:put(D/'remote_delivery/RELEASE.json',dict(id=release['id'],url=release['html_url'],created_by_distinct_resume=True))
  ref=dict(id=release['id'],url=release['html_url']);known=h.assets(ref)
  put(O/'INITIAL_ASSETS.json',dict(names=sorted(known),confirmed_before_upload=True,models=0))
  for row in index['parts']:h.ensure_uploaded(D/'archive'/row['name'],h.assets(ref))
  h.ensure_uploaded(D/'ARCHIVE_INDEX.json',h.assets(ref));known=h.assets(ref)
  folder=O/'readback';folder.mkdir();reader=Reader(index['parts'],known,folder,h.download);count=verify(reader,index)
  assert len(reader.verified)==len(index['parts'])
  recovered=folder/'ARCHIVE_INDEX.json';h.download(recovered,known['ARCHIVE_INDEX.json']);assert sha(recovered)==indexsha
  assert sha(D/'ARCHIVE_INDEX.json')==indexsha
  proof=dict(passed=True,source_commit=sync['head'],release_url=release['html_url'],every_asset_actual_download_SHA=True,every_member_SHA_and_link_text=True,whole_archive_SHA=True,recovery_index_download_SHA=True,members=count,archive_bytes=index['archive_bytes'],models=0,physical_admission=False,scientific_navigation_passed=closed['passed'],verified_unix=time.time(),transport_resume_root=str(O.relative_to(R)),old_transport_failure_preserved=True,no_new_push_ref_archive_or_model=True,late_outside_original_archive=True)
  put(D/'FULL_REMOTE_VERIFIED.json',proof);put(O/'FULL_REMOTE_VERIFIED.json',proof)
  entries=[]
  for row in index['parts']:
   p=D/'archive'/row['name'];st=p.lstat();assert p.is_file()and not p.is_symlink()and st.st_size==row['bytes']and sha(p)==row['sha256']
   entries.append(dict(path=str(p.relative_to(R)),sha256=row['sha256'],bytes=st.st_size,device=st.st_dev,inode=st.st_ino,mtime_ns=st.st_mtime_ns))
  put(D/'TRANSPORT_CLEANUP_MANIFEST.json',dict(verified_remote_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),entries=entries,only_duplicate_transport=True))
  for row in entries:
   p=R/row['path'];st=p.lstat();assert (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)==(row['device'],row['inode'],row['bytes'],row['mtime_ns'])and sha(p)==row['sha256'];p.unlink()
  recovered.unlink();folder.rmdir()
  cleanup=dict(passed=True,only_remote_verified_duplicate_transport_removed=True,archive_bytes=index['archive_bytes'],all_original_qualification_inputs_and_outputs_retained=True,exact_SHA_size_mtime_device_inode_manifest=True,cleanup_unix=time.time(),models=0,transport_resume_root=str(O.relative_to(R)))
  put(D/'TRANSPORT_CLEANUP.json',cleanup);put(D/'remote_delivery/FINALIZED.json',proof);result.update(passed=True,members=count,archive_bytes=index['archive_bytes'])
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc(),unverified_originals_retained=True)
 finally:
  signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,wall_s=time.monotonic()-START);put(O/'RESULT.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':
 O.mkdir(parents=True,exist_ok=False)
 error=read(D/'remote_delivery/ERROR.json');assert error['error']=="AssertionError('RELEASE_ABSENCE_NOT_CONFIRMED')",'ONLY_EXACT_RELEASE_LOOKUP_FAILURE_CAN_RESUME'
 raise SystemExit(main())
