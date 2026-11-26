"""Bounded source and component evidence transport, never controller execution."""
from pathlib import Path
import fcntl,gzip,hashlib,importlib.util,json,os,subprocess,sys,tarfile,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
S=R/'runs/v2027_mppi_journal_snapshot_consistency';SOURCE_D=R/'runs'/C.name/'source';RUNTIME_D=SOURCE_D.parent/'runtime';P=R/'runs/v2021_mppi_parallel_counter_affinity'
def read(p):
 p=Path(p);v=json.loads(p.read_text())
 if p.name=='SOURCE_FREEZE.json'and 'inherit_freeze_path'in v:
  parent=R/v['inherit_freeze_path'];assert sha(parent)==v['inherit_freeze_sha256'];base=read(parent)['files'];assert all(n not in base or base[n]==h for n,h in v['files'].items());v=dict(v,files=dict(base,**v['files']))
 return v
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def put(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');raw=json.dumps(v,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<2*1024**2;t.write_bytes(raw);t.replace(p)
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
def archive(runtime=False):
 os.sched_setaffinity(0,{5});D=RUNTIME_D if runtime else SOURCE_D;D.mkdir(parents=True,exist_ok=True)
 assert not(D/'ARCHIVE_CLAIM.json').exists()
 if runtime:assert read(S/'COMPLETION.json')['closed']and read(S/'RUNTIME_CLOSED_REVIEW.json')['closed']
 else:assert read(S/'SOURCE_QUALIFICATION.json')['passed']and read(P/'COMPONENT_POST_STORAGE_BARRIER.json')['passed']
 frozen=read(S/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
 usage=load('current_usage_only',R/'experiments/v1518_compact_parent_control/common.py').usage()
 assert usage+(8+8+512)*1024**2<15*1024**3
 put(D/'ARCHIVE_CLAIM.json',dict(unix=time.time(),runtime=runtime,archive_cap=8*1024**2,new_model_or_optimizer_calls=0))
 with(D/'IO.lock').open('a+')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  files=set()
  for folder in [C,S,R/'experiments/v2027_mppi_journal_snapshot_consistency']:
   for p in folder.rglob('*'):
    if p.is_file()and '__pycache__'not in p.parts:files.add(p)
  prior=read(P/'SOURCE_FREEZE.json')['files']
  for n,h in frozen.items():
   if prior.get(n)!=h:files.add(R/n)
  inventory=load('original_archive_inventory',R/'experiments/v1391_handoff_archive_recovery/archive.py').inventory
  items=inventory(sorted(files),{});wanted={row['path']:row for row in items};io=load('original_archive_parts',R/'experiments/v1382_weekend_campaign/storage_preserve.py')
  for n in ['SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json']+(['COMPLETION.json','RUNTIME_CLOSED_REVIEW.json']if runtime else[]):assert wanted[str((S/n).relative_to(R))]['sha256']==sha(S/n)
  class Parts(io.Parts):
   def write(self,b):
    assert self.total+len(b)<=8*1024**2,'MPPI_ARCHIVE_8MIB_CAP';return super().write(b)
  folder=D/'archive';folder.mkdir();writer=Parts(folder,'v2027-mppi-'+('runtime'if runtime else'source')+'.tar.gz')
  with gzip.GzipFile(fileobj=writer,mode='wb',compresslevel=3,mtime=0)as z,tarfile.open(fileobj=z,mode='w|')as tar:
   for row in items:
    info=tarfile.TarInfo(row['path'])
    if 'symlink'in row:info.type=tarfile.SYMTYPE;info.linkname=row['symlink'];tar.addfile(info)
    else:
     info.size=row['bytes']
     with(R/row['path']).open('rb')as f:tar.addfile(info,f)
  writer.finish();parts=[folder/row['name']for row in writer.parts];whole=hashlib.sha256()
  for p,row in zip(parts,writer.parts):assert p.stat().st_size==row['bytes']and sha(p)==row['sha256'];whole.update(p.read_bytes())
  assert whole.hexdigest()==writer.digest.hexdigest();seen=set()
  with tarfile.open(fileobj=io.Reader(parts),mode='r|gz')as tar:
   for member in tar:
    assert member.name in wanted and member.name not in seen;row=wanted[member.name]
    if 'symlink'in row:assert member.issym()and member.linkname==row['symlink']
    else:
     assert member.isfile()and member.size==row['bytes'];h=hashlib.sha256();f=tar.extractfile(member)
     for b in iter(lambda:f.read(1024**2),b''):h.update(b)
     assert h.hexdigest()==row['sha256']
    seen.add(member.name)
  assert seen==set(wanted)and all(sha(R/n)==h for n,h in frozen.items())
  put(D/'ARCHIVE_INDEX.json',dict(files=items,parts=writer.parts,archive_bytes=writer.total,archive_sha256=writer.digest.hexdigest(),local_members_and_reassembly_verified=True,scope='Current original-contract MPPI vehicle interface component; source only'if not runtime else'Actual component results, all captures/replay/audit and primary-secondary errors; transport does not assert success'))
  put(D/'FINALIZED.json',dict(passed=True,only_archive_complete=True,scientific_navigation_passed=None,archive_bytes=writer.total,members=len(items),new_model_or_optimizer_calls=0))
  print(json.dumps(read(D/'FINALIZED.json')))
def sync():
 D=SOURCE_D;assert not(D/'SOURCE_SYNC_CLAIM.json').exists();head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();put(D/'SOURCE_SYNC_CLAIM.json',dict(head=head,unix=time.time(),no_retry=True))
 proof=dict(head=head,remote_verified=False,push_executed=False)
 try:
  p=subprocess.run(['git','push','origin','HEAD:main'],cwd=R,capture_output=True,timeout=30);proof.update(push_executed=True,push_returncode=p.returncode)
  q=subprocess.run([str(R/'tools/phase_storage_20261107/vendor/gh'),'api','repos/frank8763/phase-/git/ref/heads/main'],cwd=R,capture_output=True,timeout=5,env=dict(os.environ,GODEBUG='http2client=0'))
  proof['remote_verified']=q.returncode==0 and json.loads(q.stdout)['object']['sha']==head
 except subprocess.TimeoutExpired:proof['error']='BOUNDED_PUSH_OR_REF_TIMEOUT'
 put(D/'SOURCE_SYNC_RESULT.json',proof);print(json.dumps(proof));assert proof['remote_verified']
def ref():
 assert not(RUNTIME_D/'SOURCE_SYNC_RESULT.json').exists();r=read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json');p=R/r['source_sync_result_path'];assert sha(p)==r['source_sync_result_sha256'];a=read(p);assert a['remote_verified']and a['head']==r['source_commit'];put(RUNTIME_D/'SOURCE_SYNC_RESULT.json',dict(head=a['head'],remote_verified=True,push_executed=False,ref_executed=False))
def deliver(runtime=False):
 # Reuse proven actual-byte upload/readback/cleanup; bind all roots explicitly.
 target=R/'experiments/v2007_mppi_observed_source_recovery/deliver.py';text=target.read_text()
 text=text.replace("D=S/'runtime_archives'/rid if runtime else D0","D=RUNTIME_D if runtime else SOURCE_D")
 text=text.replace("assert rid in [f'common_{i:02d}__DWA'for i in range(6,13)]","assert read(S/'COMPLETION.json')['closed']")
 text=text.replace("prior=read(D0/'remote_delivery/RELEASE.json')","prior=read(SOURCE_D/'remote_delivery/RELEASE.json')")
 text=text.replace('phase-v2006-mppi-observed-dependencies-source-20261126','phase-v2027-mppi-current-vehicle-source-20261126').replace('v2006_source','v2027_source').replace('(rid if runtime else',"('v2027_runtime'if runtime else")
 text=text.replace('4*1024**2','8*1024**2').replace('MPPI two exact observed typesupport dependencies source','MPPI current vehicle interface and prospective CPU6 owner source')
 space={'__file__':str(target),'__name__':'bound_transport'};exec(compile(text,str(target),'exec'),space)
 space.update(S=S,SOURCE_D=SOURCE_D,RUNTIME_D=RUNTIME_D)
 return space['main'](runtime=runtime)
def chain():
 D=SOURCE_D;r=read(D/'FULL_REMOTE_VERIFIED.json');assert r['passed']and read(D/'TRANSPORT_CLEANUP.json')['passed'];assert not Path('/proc',str(read(D/'remote_delivery/CLAIM.json')['pid'])).exists()
 frozen=read(S/'SOURCE_FREEZE.json')['files'];old=read(P/'SOURCE_FREEZE.json')['files'];rec=read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert rec['passed']and rec['all_frozen_members_remote_chain_covered']
 members={x['path']:x for x in read(D/'ARCHIVE_INDEX.json')['files']};assert all(old.get(n)==h or members.get(n,{}).get('sha256')==h for n,h in frozen.items());assert all(sha(R/n)==h for n,h in frozen.items());sync=read(D/'SOURCE_SYNC_RESULT.json');assert sync['remote_verified']and sync['head']==r['source_commit']
 for n in ['owner.py','pilot_entry.py','native_worker.py']:
  p=R/'experiments/v2027_mppi_journal_snapshot_consistency'/n;assert subprocess.check_output(['git','show',sync['head']+':'+str(p.relative_to(R))],cwd=R)==p.read_bytes()
 value=dict(passed=True,all_frozen_members_remote_chain_covered=True,uncovered_members=[],source_members=len(frozen),index_path=str((D/'ARCHIVE_INDEX.json').relative_to(R)),index_sha256=sha(D/'ARCHIVE_INDEX.json'),full_remote_proof_path=str((D/'FULL_REMOTE_VERIFIED.json').relative_to(R)),full_remote_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),source_commit=sync['head'],source_sync_result_path=str((D/'SOURCE_SYNC_RESULT.json').relative_to(R)),source_sync_result_sha256=sha(D/'SOURCE_SYNC_RESULT.json'),models_authorized=False)
 put(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json',value);put(S/'POST_SOURCE_STORAGE_BARRIER.json',dict(passed=True,all_frozen_SHA=True,source_recovery_sha256=sha(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json'),remote_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),cleanup_sha256=sha(D/'TRANSPORT_CLEANUP.json')));print(json.dumps(dict(passed=True,source_members=len(frozen))))
def main():
 os.sched_setaffinity(0,{5});stage=sys.argv[1]
 if stage=='archive':archive()
 elif stage=='runtime-archive':archive(True)
 elif stage=='sync':sync()
 elif stage=='ref':ref()
 elif stage=='deliver':raise SystemExit(deliver())
 elif stage=='runtime-deliver':raise SystemExit(deliver(True))
 elif stage=='chain':chain()
 else:raise AssertionError('UNKNOWN_STAGE')
if __name__=='__main__':main()
