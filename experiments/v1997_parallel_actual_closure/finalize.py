"""Runtime-only actual two-lane closure; independent from running RPP plant."""
from pathlib import Path
import hashlib,importlib.util,json,fcntl,os,time,gzip,tarfile
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name;S=R/'runs/v1993_parallel_compact_source';B=R/'runs/v1996_parallel_lock_bootstrap'
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def put(p,x):assert not p.exists();p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
 os.sched_setaffinity(0,{5});assert not(D/'ARCHIVE_CLAIM.json').exists();assert read(B/'RESULT.json')['closed'];results={}
 for lane in ['MPPI','SVG-MPPI']:
  O=S/'lanes'/lane;closed=read(O/'COMPLETION.json');assert closed['closed'];identity=read(O/'OWNED_CHILD.json');p=Path('/proc',str(identity['pid']),'stat');assert not p.exists()or p.read_text().split(') ',1)[1].split()[19]!=identity['start_ticks'];journal=read(O/'CALL_JOURNAL.json');machine=read(O/'RESULT.json')if(O/'RESULT.json').exists()else None
  results[lane]=dict(owner=closed,last_call_journal=journal,native_result=machine,canonical_native_RESULT_missing=machine is None,outer_first_error=closed['first_error'],raw_console_path=str((O/'native.console').relative_to(R)),raw_console_sha256=sha(O/'native.console'),counts_interpretation='lastjournal oneconstructorinflight/no return known/native_exit139; 1DLL; no outward solve attempt recorded; internal counts unknown'if machine is None else'1 author constructor returned, 1 solve returned, destroy1; inner kinematic total unknown',no_whole_navigation_or_Phase_vehicle_safety_claim=True)
 full=load('closed_parallel_source_composition',R/'experiments/v1993_parallel_compact_source/common.py');frozen=full.read(S/'SOURCE_FREEZE.json')['files'];assert len(frozen)==16023 and all(sha(R/n)==h for n,h in frozen.items())
 review=dict(closed=True,lanes=results,all16023frozen_source_SHA_after_both_childexit=True,physics_native=0,replay_native=0,MuJoCo_initializations=0,formal_common_assignments=0,whole_navigation_passed=False,global_RPP_REVIEW_execution_lock_or_frozen_source_not_modified=True,original_failed_preclaim_dispatch_sha256=sha(S/'PARALLEL_RESULT.json'),first_actual_resume_metadata_sha256=sha(B/'RESULT.json'),late_helper_paths_SHA256={str(p.relative_to(R)):sha(p)for folder in [C,R/'experiments/v1996_parallel_lock_bootstrap']for p in folder.glob('*')if p.is_file()},source_commit=read(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['source_commit'],scientific_disposition='SVG_NEW_NUMERIC_INPUT_PASS_MPPI_NATIVE_CONSTRUCTOR_EXIT139_UNQUALIFIED')
 put(S/'RUNTIME_CLOSED_REVIEW.json',review);put(S/'COMPLETION.json',dict(closed=True,passed=False,lanes_passed={'SVG-MPPI':True,'MPPI':False},physics_native=0,formal_common_assignments=0,review_path=str((S/'RUNTIME_CLOSED_REVIEW.json').relative_to(R)),review_sha256=sha(S/'RUNTIME_CLOSED_REVIEW.json'),no_global_RPP_review_change=True))
 used=int(__import__('subprocess').check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used+(4+4+512)*1024**2<15*1024**3;put(D/'ARCHIVE_CLAIM.json',dict(pid=os.getpid(),unix=time.time(),maximum_archive_bytes=4*1024**2,no_model=True));io=load('original_parts_stream',R/'experiments/v1382_weekend_campaign/storage_preserve.py');inventory=load('original_member_inventory',R/'experiments/v1391_handoff_archive_recovery/archive.py').inventory;paths=set()
 for folder in [S,B,R/'experiments/v1996_parallel_lock_bootstrap',C]:
  for p in folder.rglob('*'):
   if(p.is_file()or p.is_symlink())and '__pycache__'not in p.parts:paths.add(p)
 index=inventory(sorted(paths),{});wanted={r['path']:r for r in index};(D/'archive').mkdir()
 class Bounded(io.Parts):
  def write(self,data):assert self.total+len(data)<=4*1024**2;return super().write(data)
 writer=Bounded(D/'archive','v1993-parallel-actual-runtime.tar.gz')
 with gzip.GzipFile(fileobj=writer,mode='wb',compresslevel=3,mtime=0)as gz,tarfile.open(fileobj=gz,mode='w|')as tar:
  for row in index:
   info=tarfile.TarInfo(row['path'])
   if 'symlink'in row:info.type=tarfile.SYMTYPE;info.linkname=row['symlink'];tar.addfile(info)
   else:
    info.size=row['bytes']
    with(R/row['path']).open('rb')as f:tar.addfile(info,f)
 writer.finish();seen=set()
 with tarfile.open(fileobj=io.Reader([D/'archive'/r['name']for r in writer.parts]),mode='r|gz')as tar:
  for member in tar:
   row=wanted[member.name];h=hashlib.sha256();stream=tar.extractfile(member)
   for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
   assert h.hexdigest()==row['sha256'];seen.add(member.name)
 assert seen==set(wanted);put(D/'ARCHIVE_INDEX.json',dict(files=index,parts=writer.parts,archive_bytes=writer.total,archive_sha256=writer.digest.hexdigest(),local_members_and_reassembly_verified=True,remote_download_restore_verified=False,physics_native=0));put(D/'FINALIZED.json',dict(passed=True,scientific_navigation_passed=None,transport_only=True,members=len(index),archive_bytes=writer.total));put(D/'SOURCE_SYNC_RESULT.json',dict(head=review['source_commit'],remote_verified=True,push_executed=False,ref_executed=False,reused_exact_original_source_sync=True,original_recovery_path=str((S/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),original_recovery_sha256=sha(S/'CURRENT_SOURCE_REMOTE_RECOVERY.json')));print(json.dumps(dict(passed=True,members=len(index),bytes=writer.total)))
if __name__=='__main__':main()
