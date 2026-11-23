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
 os.sched_setaffinity(0,{5});assert not(O/'ARCHIVE_CLAIM.json').exists()
 parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']
 assert read(R/'runs/v1656_svg_solver_interface/SOURCE_QUALIFICATION.json')['passed']
 current=load('v1533_existing_usage_only',R/'experiments/v1518_compact_parent_control/common.py')
 frozen=read(R/'runs/v1656_svg_solver_interface/SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
 assert read(R/'runs/v1649_error_stop_sensor_capture/CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 assert current.usage()+(16+32+512)*1024**2<15*1024**3,'SOURCE_RECOVERY_FULL_STORAGE_PEAK_REFUSED'
 put(O/'ARCHIVE_CLAIM.json',dict(started_unix=time.time(),models=0,archive_cap_bytes=16*1024**2,allruns_before_bytes=current.usage(),reserved_peak_bytes=current.usage()+(16+32+512)*1024**2))
 io=load('v1501_original_archive_io',R/'experiments/v1382_weekend_campaign/storage_preserve.py');inventory=load('v1501_original_inventory',R/'experiments/v1391_handoff_archive_recovery/archive.py').inventory
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
  files=set()
  folders=[C,O,R/'runs/v1650_comparison_completion/author_intake',R/'experiments/v1652_author_vehicle_mapping',R/'runs/v1652_author_vehicle_mapping']
  for name in ['v1654_svg_cpu_core','v1655_svg_original_build_flags','v1656_svg_solver_interface']:
   folders.extend([R/'experiments'/name,R/'runs'/name])
  for folder in folders:
   for p in folder.rglob('*'):
    if(p.is_file()or p.is_symlink())and '__pycache__'not in p.parts:files.add(p)
  for name in ['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/SVG_AUTHOR_CPU_CORE_V1656_REPORT.md','runs/v1643_formal_parent_metadata/SOURCE_FREEZE.json','runs/v1646_prefix_audit_scope/CURRENT_SOURCE_REMOTE_RECOVERY.json','runs/v1643_formal_parent_metadata/FORMAL_LEDGER.json','runs/v1643_formal_parent_metadata/rounds/phase_01__full/RUNTIME_CLOSED_REVIEW.json','runs/v1643_formal_parent_metadata/rounds/phase_01__full/POST_ROUND_STORAGE_BARRIER.json','runs/v1643_formal_parent_metadata/rounds/phase_01__full/FUNCTIONAL_BOUNDARY_DIAGNOSIS.json','runs/v1645_formal_runtime_recovery/phase_01__full/ARCHIVE_INDEX.json','runs/v1645_formal_runtime_recovery/phase_01__full/FULL_REMOTE_VERIFIED.json','runs/v1645_formal_runtime_recovery/phase_01__full/TRANSPORT_CLEANUP.json','runs/v1643_formal_parent_metadata/rounds/phase_01__no_onward/POST_ROUND_STORAGE_BARRIER.json','runs/v1648_source_bound_formal_recovery/phase_01__no_onward/ARCHIVE_INDEX.json','runs/v1648_source_bound_formal_recovery/phase_01__no_onward/FULL_REMOTE_VERIFIED.json','runs/v1648_source_bound_formal_recovery/phase_01__no_onward/TRANSPORT_CLEANUP.json']:
   files.add(R/name)
  inherited=read(R/'runs/v1649_error_stop_sensor_capture/SOURCE_FREEZE.json')['files']
  for name,identity in frozen.items():
   if inherited.get(name)!=identity:files.add(R/name)
  items=inventory(sorted(files),{});wanted={v['path']:v for v in items}
  class Bounded(io.Parts):
   def write(self,data):
    assert self.total+len(data)<=16*1024**2,'SOURCE_ARCHIVE_16MIB_CAP';return super().write(data)
  folder=O/'archive';folder.mkdir();writer=Bounded(folder,'v1657-svg-source.tar.gz')
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
  put(O/'ARCHIVE_INDEX.json',dict(files=items,parts=writer.parts,archive_bytes=writer.total,archive_sha256=writer.digest.hexdigest(),local_members_and_reassembly_verified=True,remote_download_restore_verified=False,models=0,scope='Exact SVG-MPPI authorCPUcore and originalgrid_map/Eigen sources; failedV1654 compilerconfiguration kept, V1655 officialEigenpluginflags buildPASSED, V1656 CABI build/SOURCE passed withoneexplicitCDLLload and10metadata/errorcalls,0authorconstructors/optimizer/physical/replay. Source13797 fullysaved bydelta+verifiedV1649chain. No scientific navigation or comparisonPASS from thisarchive.'))
  proof=dict(passed=True,scientific_navigation_passed=False,models=0,physical_native=0,optimizer_calls_during_archive=0,archive_bytes=writer.total,members=len(items),physical_admission=False,only_archive_complete=True)
  put(O/'FINALIZED.json',proof);print(json.dumps(proof))
if __name__=='__main__':main()
