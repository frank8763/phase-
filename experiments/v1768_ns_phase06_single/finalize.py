"""Once fixed-WE comparison and source-interface recovery; zero model calls."""
import fcntl,gzip,hashlib,importlib.util,json,os,tarfile,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--assignment',required=True);parser.add_argument('--sync',action='store_true');arguments=parser.parse_args()
FORMAL=R/'runs/v1643_formal_parent_metadata'
registered=json.loads((FORMAL/'TASKS_LOCKED.json').read_text())
assert arguments.assignment in[a['assignment_id']for row in registered['tasks']if row['task']['case_id']=='NORTH_SOUTH'for a in row['assignments']]
ROUND=FORMAL/'rounds'/arguments.assignment
_admission=json.loads((ROUND/'FORMAL_ADMISSION.json').read_text())
_source_relative=Path(_admission['source_version_root'])
assert not _source_relative.is_absolute() and '..' not in _source_relative.parts
SOURCE=R/_source_relative
assert SOURCE.parent==R/'runs' and SOURCE.name=='v1765_ns_formal_binding'
assert hashlib.sha256((SOURCE/'SOURCE_FREEZE.json').read_bytes()).hexdigest()==_admission['source_freeze_sha256']
O=R/'runs'/C.name/arguments.assignment;O.mkdir(parents=True,exist_ok=True)

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
 os.sched_setaffinity(0,{5});assert not(O/'ARCHIVE_CLAIM.json').exists()
 parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']
 assert read(SOURCE/'SOURCE_QUALIFICATION.json')['passed']
 assert read(ROUND/'COMPLETION.json')['closed']and read(ROUND/'RUNTIME_CLOSED_REVIEW.json')['closed']
 now=read(R/'CURRENT_EXPERIMENT.json');assert now['active_round']is None and not now['models_now_authorized']
 if not(ROUND/'actual/RESULT.json').exists():assert read(ROUND/'CONSOLE_RECOVERED_FAILURE_RECORD.json')['machine_RESULT_missing']
 current=load('v1533_existing_usage_only',R/'experiments/v1518_compact_parent_control/common.py')
 frozen=read(SOURCE/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
 assert read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 assert current.usage()+(240+32+512)*1024**2<15*1024**3,'SOURCE_RECOVERY_FULL_STORAGE_PEAK_REFUSED'
 put(O/'ARCHIVE_CLAIM.json',dict(started_unix=time.time(),models=0,archive_cap_bytes=240*1024**2,allruns_before_bytes=current.usage(),reserved_peak_bytes=current.usage()+(240+32+512)*1024**2))
 io=load('v1501_original_archive_io',R/'experiments/v1382_weekend_campaign/storage_preserve.py');inventory=load('v1501_original_inventory',R/'experiments/v1391_handoff_archive_recovery/archive.py').inventory
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
  files=set()
  folders=[C,O,ROUND]
  for folder in folders:
   for p in folder.rglob('*'):
    if(p.is_file()or p.is_symlink())and '__pycache__'not in p.parts and 'live_io'not in p.parts:files.add(p)
  for name in ['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/NS_PHASE06_V1768_REPORT.md','runs/v1620_mechanism_boundary/UNATTENDED_CONTINUATION_AUTHORIZATION_20261123.json']:
   files.add(R/name)
  for name in ['SOURCE_FREEZE.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','CURRENT_SOURCE_REMOTE_RECOVERY.json']:files.add(SOURCE/name)
  for name in ['TASKS_LOCKED.json','LIMITS.json','FORMAL_LEDGER.json']:files.add(FORMAL/name)
  if(ROUND/'CONSOLE_RECOVERED_FAILURE_RECORD.json').exists():files.add(ROUND/'CONSOLE_RECOVERED_FAILURE_RECORD.json')
  items=inventory(sorted(files),{});wanted={v['path']:v for v in items}
  class Bounded(io.Parts):
   def write(self,data):
    assert self.total+len(data)<=240*1024**2,'RUNTIME_ARCHIVE_240MIB_CAP';return super().write(data)
  folder=O/'archive';folder.mkdir();writer=Bounded(folder,'v1768-'+arguments.assignment+'-runtime.tar.gz')
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
  put(O/'ARCHIVE_INDEX.json',dict(files=items,parts=writer.parts,archive_bytes=writer.total,archive_sha256=writer.digest.hexdigest(),local_members_and_reassembly_verified=True,remote_download_restore_verified=False,models=0,scope='Registered formal original-contract phase comparison '+arguments.assignment+'. Closed machine and independent evidence outcomes are stored without relabeling failure/unknown.0newmodel-native-physical-replay duringarchive;only bounded artifact preservation. Allraw retained aftereveryactualremote block/member/whole/indexSHA andexacttransportcleanup.'))
  proof=dict(passed=True,scientific_navigation_passed=None,scientific_outcome_path=str((ROUND/'RUNTIME_CLOSED_REVIEW.json').relative_to(R)),models=0,physical_native=0,optimizer_calls_during_archive=0,archive_bytes=writer.total,members=len(items),physical_admission=False,only_archive_complete=True)
  put(O/'FINALIZED.json',proof);print(json.dumps(proof))
if __name__=='__main__':main()
