"""Once SVG numeric owner SOURCE recovery; zero numerical model calls."""
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
 os.sched_setaffinity(0,{5});assert not(O/'ARCHIVE_CLAIM.json').exists()
 parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']
 assert read(R/'runs/v1698_local_cmake_toolchain/RESULT.json')['passed']
 assert (R/'runs/v1698_local_cmake_toolchain/RUNTIME_CLOSED_REVIEW.json').is_file()
 current=load('v1533_existing_usage_only',R/'experiments/v1518_compact_parent_control/common.py')
 frozen=read(R/'runs/v1694_shared_observation_closure/SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
 assert read(R/'runs/v1676_dwa_bounded_proposal/CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 assert read(R/'runs/v1694_shared_observation_closure/POST_ROUND_STORAGE_BARRIER.json')['passed']
 tool=R/'runs/v1698_local_cmake_toolchain';manifest=read(tool/'UNPACK_MANIFEST.json');assert all(sha(R/x['path'])==x['sha256']for x in manifest['files'])
 claim=read(tool/'ONCE_CLAIM.json');assert claim['owner_sha256']==sha(R/'experiments/v1698_local_cmake_toolchain/owner.py')and claim['protocol_sha256']==sha(R/'experiments/v1698_local_cmake_toolchain/PROTOCOL.md')
 assert current.usage()+(32+32+512)*1024**2<15*1024**3,'SOURCE_RECOVERY_FULL_STORAGE_PEAK_REFUSED'
 put(O/'ARCHIVE_CLAIM.json',dict(started_unix=time.time(),models=0,archive_cap_bytes=32*1024**2,allruns_before_bytes=current.usage(),reserved_peak_bytes=current.usage()+(32+32+512)*1024**2))
 io=load('v1501_original_archive_io',R/'experiments/v1382_weekend_campaign/storage_preserve.py');inventory=load('v1501_original_inventory',R/'experiments/v1391_handoff_archive_recovery/archive.py').inventory
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
  files=set()
  folders=[C,O,R/'experiments/v1698_local_cmake_toolchain',R/'experiments/v1699_teb_local_cmake_configure']
  for folder in folders:
   for p in folder.rglob('*'):
    if(p.is_file()or p.is_symlink())and '__pycache__'not in p.parts:files.add(p)
  for p in tool.iterdir():
   if p.is_file():files.add(p)
  for name in ['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/LOCAL_CMAKE_TOOLCHAIN_V1698_REPORT.md','docs/SHARED_OBSERVATION_CLOSURE_V1694_REPORT.md','docs/ALGORITHM_COMPARISON_COMPLETION_20261123.md','runs/v1650_comparison_completion/author_intake/TEB_COMMIT.json','runs/v1650_comparison_completion/author_intake/TEB_TREE.json']:
   files.add(R/name)
  inherited=read(R/'runs/v1690_dwa_origin_source_checks/SOURCE_FREEZE.json')['files']
  for name,identity in frozen.items():
   if inherited.get(name)!=identity:files.add(R/name)
  assert all(p.is_file()or p.is_symlink()for p in files),'INVENTORY_PREFLIGHT_MISSING'
  items=inventory(sorted(files),{});wanted={v['path']:v for v in items}
  class Bounded(io.Parts):
   def write(self,data):
    assert self.total+len(data)<=32*1024**2,'SOURCE_ARCHIVE_32MIB_CAP';return super().write(data)
  folder=O/'archive';folder.mkdir();writer=Bounded(folder,'v1700-cmake-toolchain.tar.gz')
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
  put(O/'ARCHIVE_INDEX.json',dict(files=items,parts=writer.parts,archive_bytes=writer.total,archive_sha256=writer.digest.hexdigest(),local_members_and_reassembly_verified=True,remote_download_restore_verified=False,models=0,scope='Exact official CMake3.31.6 wheel+allunpackmemberSHAmanifest+one CPU4versioncheck source/tool evidence. The unpacked prefix is recoverable from the byteexact retained wheel, not duplicated in archive. No systeminstall, TEBconfigure/optimizer/model/physics/replay or algorithmcontrol. TransportPASS not methodPASS.'))
  proof=dict(passed=True,scientific_navigation_passed=None,models=0,physical_native=0,optimizer_calls_during_archive=0,archive_bytes=writer.total,members=len(items),physical_admission=False,only_archive_complete=True)
  put(O/'FINALIZED.json',proof);print(json.dumps(proof))
if __name__=='__main__':main()
