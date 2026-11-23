"""Distinct closed numeric runtime recovery; no new optimizer execution."""
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
 assert read(R/'runs/v1672_svg_direct_live_component/COMPLETION.json')['closed']
 assert (R/'runs/v1672_svg_direct_live_component/RUNTIME_CLOSED_REVIEW.json').is_file()
 current=load('v1533_existing_usage_only',R/'experiments/v1518_compact_parent_control/common.py')
 frozen=read(R/'runs/v1672_svg_direct_live_component/SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
 assert read(R/'runs/v1656_svg_solver_interface/CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 assert current.usage()+(16+32+512)*1024**2<15*1024**3,'RUNTIME_RECOVERY_FULL_STORAGE_PEAK_REFUSED'
 put(O/'ARCHIVE_CLAIM.json',dict(started_unix=time.time(),models=0,archive_cap_bytes=240*1024**2,allruns_before_bytes=current.usage(),reserved_peak_bytes=current.usage()+(16+32+512)*1024**2))
 io=load('v1501_original_archive_io',R/'experiments/v1382_weekend_campaign/storage_preserve.py');inventory=load('v1501_original_inventory',R/'experiments/v1391_handoff_archive_recovery/archive.py').inventory
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
  files=set()
  folders=[C,O,R/'experiments/v1672_svg_direct_live_component',R/'runs/v1672_svg_direct_live_component',R/'runs/v1673_svg_live_source_recovery']
  for folder in folders:
   for p in folder.rglob('*'):
    if(p.is_file()or p.is_symlink())and '__pycache__'not in p.parts:files.add(p)
  for name in ['CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/SVG_BOUNDED_NUMERIC_V1658_REPORT.md']:
   files.add(R/name)
  inherited=frozen.copy()
  for name,identity in frozen.items():
   if inherited.get(name)!=identity:files.add(R/name)
  assert all(p.is_file()or p.is_symlink()for p in files),'INVENTORY_PREFLIGHT_MISSING'
  items=inventory(sorted(files),{});wanted={v['path']:v for v in items}
  class Bounded(io.Parts):
   def write(self,data):
    assert self.total+len(data)<=240*1024**2,'ACTUAL_RUNTIME_ARCHIVE_240MIB_CAP';return super().write(data)
  folder=O/'archive';folder.mkdir();writer=Bounded(folder,'v1674-svg-live-runtime.tar.gz')
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
  put(O/'ARCHIVE_INDEX.json',dict(files=items,parts=writer.parts,archive_bytes=writer.total,archive_sha256=writer.digest.hexdigest(),local_members_and_reassembly_verified=True,remote_download_restore_verified=False,models=0,scope='Distinct V1672 fresh canonical SVG-MPPI original actuator component runtime. Exact original RESULT/COMPLETION/RUNTIME_CLOSED_REVIEW determine actual/replay/primary-secondary/unknown modelwork outcomes. Not common benchmark or whole navigation. Preserve all input/raw/control/certificate/contact/sensor/Nplus1/model/progress/closure files,successes and failures. No new factory/model/optimizer/audit/replay during archive.'))
  proof=dict(passed=True,scientific_navigation_passed=None,models=0,physical_native=0,optimizer_calls_during_archive=0,archive_bytes=writer.total,members=len(items),physical_admission=False,only_archive_complete=True)
  put(O/'FINALIZED.json',proof);print(json.dumps(proof))
if __name__=='__main__':main()
