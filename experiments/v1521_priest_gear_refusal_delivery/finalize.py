"""Once zero-model recovery: failedV1498 raw and frozenV1500 new source/input."""
import fcntl,gzip,hashlib,importlib.util,json,os,tarfile,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;E=R/'runs/v1518_compact_parent_control';O=E/'actual_runtime_delivery'
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def put(p,v):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');t.replace(p)
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 os.sched_setaffinity(0,{5});assert time.time()<1795395600 and not(O/'ARCHIVE_CLAIM.json').exists()
 parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']
 assert read(E/'COMPLETION.json')['closed']and not read(E/'COMPLETION.json')['passed']and read(E/'CLOSED_REVIEW.json')['generation_analytic_native']==200
 current=load('v1515_closed_sources',R/'experiments/v1518_compact_parent_control/common.py');frozen=current.sources();assert all(sha(R/n)==h for n,h in frozen.items())
 put(O/'ARCHIVE_CLAIM.json',dict(started_unix=time.time(),models=0,archive_cap_bytes=8*1024**2))
 io=load('v1501_original_archive_io',R/'experiments/v1382_weekend_campaign/storage_preserve.py');inventory=load('v1501_original_inventory',R/'experiments/v1391_handoff_archive_recovery/archive.py').inventory
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
  files=set()
  for folder in [E,C,R/'experiments/v1520_priest_direction_diagnosis',R/'runs/v1520_priest_direction_diagnosis']:
   for p in folder.rglob('*'):
    if(p.is_file()or p.is_symlink())and '__pycache__'not in p.parts and not p.is_relative_to(O):files.add(p)
  files.add(O/'ARCHIVE_CLAIM.json');files.add(R/'docs/PRIEST_DIRECTION_V1520_REPORT.md')
  for name in ['docs/PRIEST_GEAR_REFUSAL_V1518_REPORT.md','runs/v1519_compact_response_source_recovery/ARCHIVE_INDEX.json','runs/v1519_compact_response_source_recovery/FULL_REMOTE_VERIFIED.json','runs/v1519_compact_response_source_recovery/TRANSPORT_CLEANUP.json']:files.add(R/name)
  items=inventory(sorted(files),{});wanted={v['path']:v for v in items}
  class Bounded(io.Parts):
   def write(self,data):
    assert self.total+len(data)<=8*1024**2,'SOURCE_ARCHIVE_8MIB_CAP';return super().write(data)
  folder=O/'archive';folder.mkdir();writer=Bounded(folder,'v1518-priest-gear-request-refused.tar.gz')
  with gzip.GzipFile(fileobj=writer,mode='wb',compresslevel=3,mtime=0)as compressor,tarfile.open(fileobj=compressor,mode='w|')as tar:
   for row in items:
    info=tarfile.TarInfo(row['path'])
    if 'symlink'in row:info.type=tarfile.SYMTYPE;info.linkname=row['symlink'];tar.addfile(info)
    else:
     info.size=row['bytes']
     with(R/row['path']).open('rb')as f:tar.addfile(info,f)
  writer.finish();parts=[folder/row['name']for row in writer.parts];whole=hashlib.sha256()
  for p,row in zip(parts,writer.parts):
   assert row['bytes']<=32*1024**2 and sha(p)==row['sha256']
   with p.open('rb')as f:
    for b in iter(lambda:f.read(1024**2),b''):whole.update(b)
  assert whole.hexdigest()==writer.digest.hexdigest();seen=set()
  with tarfile.open(fileobj=io.Reader(parts),mode='r|gz')as tar:
   for member in tar:
    assert member.name in wanted and member.name not in seen;row=wanted[member.name]
    if 'symlink'in row:assert member.issym()and member.linkname==row['symlink']
    else:
     assert member.isfile()and member.size==row['bytes'];h=hashlib.sha256();stream=tar.extractfile(member)
     for b in iter(lambda:stream.read(1024**2),b''):h.update(b)
     assert h.hexdigest()==row['sha256']
    seen.add(member.name)
  assert seen==set(wanted)and all(sha(R/n)==h for n,h in frozen.items())
  put(O/'ARCHIVE_INDEX.json',dict(files=items,parts=writer.parts,archive_bytes=writer.total,archive_sha256=writer.digest.hexdigest(),local_members_and_reassembly_verified=True,remote_download_restore_verified=False,models=0,scope='V1518onceCPU2savedinputresponse REFUSED at original declaredgear signgate;1explicitPredictor1copy200analytic unknownfalse/1complete201state200ctrl stop tube.4429581147519787 produceronly/0nominal/audit0unexecuted/0physical-MuJoCo-optimizer-independentAllocator-replay. All14originchecks and modeledinitial saved; V1520sourceASTdiagnosis not recordedruntime request; finiteengineeringadaptation refusal not author D-PRIEST reproduction or navigationPASS'))
  proof=dict(passed=True,scientific_navigation_passed=False,models=0,physical_native=0,optimizer_calls_during_archive=0,archive_bytes=writer.total,members=len(items),physical_admission=False,only_archive_complete=True)
  put(O/'FINALIZED.json',proof);print(json.dumps(proof))
if __name__=='__main__':main()
