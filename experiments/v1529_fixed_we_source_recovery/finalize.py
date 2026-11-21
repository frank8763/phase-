"""Once fixed-WE comparison and source-interface recovery; zero model calls."""
import fcntl,gzip,hashlib,importlib.util,json,os,tarfile,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
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
 assert read(R/'runs/v1528_fixed_we_evaluation_contract/ENTRY_QUALIFICATION.json')['passed']
 for name in ['v1526_fixed_route_comparison_eligibility','v1527_fixed_we_model_ownership']:
  assert all(sha(R/n)==h for n,h in read(R/'runs'/name/'CLOSED_SOURCE_INDEX.json').items())
 current=load('v1529_existing_usage_only',R/'experiments/v1518_compact_parent_control/common.py')
 frozen=read(R/'runs/v1528_fixed_we_evaluation_contract/SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
 assert read(R/'runs/v1518_compact_parent_control/CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 assert current.usage()+(8+32+512)*1024**2<10*1024**3,'SOURCE_RECOVERY_FULL_STORAGE_PEAK_REFUSED'
 put(O/'ARCHIVE_CLAIM.json',dict(started_unix=time.time(),models=0,archive_cap_bytes=8*1024**2,allruns_before_bytes=current.usage(),reserved_peak_bytes=current.usage()+(8+32+512)*1024**2))
 io=load('v1501_original_archive_io',R/'experiments/v1382_weekend_campaign/storage_preserve.py');inventory=load('v1501_original_inventory',R/'experiments/v1391_handoff_archive_recovery/archive.py').inventory
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
  files=set()
  for folder in [R/'experiments/v1526_fixed_route_comparison_eligibility',R/'runs/v1526_fixed_route_comparison_eligibility',R/'experiments/v1527_fixed_we_model_ownership',R/'runs/v1527_fixed_we_model_ownership',R/'experiments/v1528_fixed_we_evaluation_contract',R/'runs/v1528_fixed_we_evaluation_contract',C,O]:
   for p in folder.rglob('*'):
    if(p.is_file()or p.is_symlink())and '__pycache__'not in p.parts:files.add(p)
  for name in ['docs/FIXED_ROUTE_COMPARISON_ELIGIBILITY_V1526.md','docs/FIXED_WE_SOURCE_OWNERSHIP_V1527_REPORT.md','docs/FIXED_WE_EVALUATION_CONTRACT_V1528_REPORT.md','CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','runs/v1382_weekend_campaign/LEDGER.json','runs/v1518_compact_parent_control/SOURCE_FREEZE.json','runs/v1518_compact_parent_control/CURRENT_SOURCE_REMOTE_RECOVERY.json','runs/v1479_retirement_scope_binding/actual_runtime_delivery/ARCHIVE_INDEX.json','runs/v1479_retirement_scope_binding/actual_runtime_delivery/FULL_REMOTE_VERIFIED.json','runs/v1499_priest_saved_source_recovery/ARCHIVE_INDEX.json','runs/v1499_priest_saved_source_recovery/FULL_REMOTE_VERIFIED.json','runs/v1497_priest_complete_response/ENTRY_QUALIFICATION.json','runs/v1524_priest_source_capture_recovery/RECOVERY_CHAIN.json','runs/v1524_priest_source_capture_recovery/ARCHIVE_INDEX.json','runs/v1524_priest_source_capture_recovery/FULL_REMOTE_VERIFIED.json']:files.add(R/name)
  items=inventory(sorted(files),{});wanted={v['path']:v for v in items}
  class Bounded(io.Parts):
   def write(self,data):
    assert self.total+len(data)<=8*1024**2,'SOURCE_ARCHIVE_8MIB_CAP';return super().write(data)
  folder=O/'archive';folder.mkdir();writer=Bounded(folder,'v1529-fixed-we-source-interface.tar.gz')
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
  put(O/'ARCHIVE_INDEX.json',dict(files=items,parts=writer.parts,archive_bytes=writer.total,archive_sha256=writer.digest.hexdigest(),local_members_and_reassembly_verified=True,remote_download_restore_verified=False,models=0,scope='V1526comparison eligibility/V1527ownership/V1528once recorded-source interface only; historical V1159 bounded-load model differs plain shared V1114 and epoch/equivalence unqualified.0models-integrations-Allocator-optimizer-physics-replay/newscience. Inherited prior source and actual-runtime chains linked, not duplicated. Archive complete is not scientific or navigation PASS'))
  proof=dict(passed=True,scientific_navigation_passed=False,models=0,physical_native=0,optimizer_calls_during_archive=0,archive_bytes=writer.total,members=len(items),physical_admission=False,only_archive_complete=True)
  put(O/'FINALIZED.json',proof);print(json.dumps(proof))
if __name__=='__main__':main()
