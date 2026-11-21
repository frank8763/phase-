"""Bounded public binary artifact capture; never import or extract a wheel."""
import hashlib
import json
import math
import os
from pathlib import Path,PurePosixPath
import signal
import time
import traceback
import urllib.request
import zipfile
R=Path(__file__).resolve().parents[2];O=R/'runs/v1489_priest_wheel_capture'

def put(p,v):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');t.replace(p)
def usage():
 seen=set();total=0
 for root,dirs,files in os.walk(R/'runs',followlinks=False):
  for p in [Path(root)]+[Path(root)/n for n in files]:
   s=p.lstat();key=(s.st_dev,s.st_ino)
   if key not in seen:seen.add(key);total+=s.st_blocks*512
 return total

def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 scope=json.loads((O/'WHEEL_SCOPE.json').read_text());assert not(O/'ONCE_CLAIM.json').exists()
 with(O/'ONCE_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),started_unix=time.time(),models=0),f)
 def expired(*_):raise TimeoutError('WHEEL_CAPTURE_WALL_LIMIT')
 signal.signal(signal.SIGALRM,expired);started=time.monotonic();records=[]
 try:
  parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text());assert parent['active_round']is None and not parent['models_now_authorized']
  source=R/scope['source_metadata'];assert hashlib.sha256(source.read_bytes()).hexdigest()==scope['source_metadata_sha256']
  selected=json.loads(source.read_text())['wheels'];assert len(selected)==5
  before=usage();reserve=sum(scope[k]for k in ['evidence_cap_bytes','archive_cap_bytes','readback_reserve_bytes','root_reserve_bytes']);assert before+reserve<scope['all_runs_limit_bytes'],'FULL_ACQUISITION_PEAK_REFUSED'
  put(O/'STORAGE_ADMISSION.json',dict(allruns_before_bytes=before,complete_reserved_peak_bytes=before+reserve,limit_bytes=scope['all_runs_limit_bytes'],models=0,not_numeric_admission=True))
  folder=O/'wheels';folder.mkdir();emitted=0
  for row in selected:
   assert time.time()<scope['root_deadline_unix'];signal.alarm(min(60,max(1,int(300-(time.monotonic()-started)))))
   assert row['wheel_url'].startswith('https://files.pythonhosted.org/')and row['bytes']>0
   p=folder/row['filename'];h=hashlib.sha256();count=0
   with urllib.request.urlopen(row['wheel_url'],timeout=20)as response,p.open('xb')as stream:
    assert response.status==200 and response.geturl()==row['wheel_url']
    while True:
     block=response.read(1024**2)
     if not block:break
     assert count+len(block)<=row['bytes']and emitted+len(block)<=scope['evidence_cap_bytes']
     stream.write(block);h.update(block);count+=len(block);emitted+=len(block)
   assert count==row['bytes']and h.hexdigest()==row['sha256'],'EXACT_PUBLIC_WHEEL_SHA_REFUSED'
   members=[];names=set();logical=0;allocated=0
   with zipfile.ZipFile(p)as z:
    assert len(z.infolist())<20000
    for info in z.infolist():
     name=PurePosixPath(info.filename);assert not name.is_absolute()and '..'not in name.parts and info.filename not in names
     assert (info.external_attr>>16)&0o170000!=0o120000,'WHEEL_SYMLINK_REFUSED'
     names.add(info.filename)
     if info.is_dir():continue
     logical+=info.file_size;allocated+=4096*math.ceil(info.file_size/4096);assert logical<=512*1024**2,'WHEEL_EXPANSION_BOUND'
     digest=hashlib.sha256();n=0
     with z.open(info)as member:
      for block in iter(lambda:member.read(1024**2),b''):digest.update(block);n+=len(block)
     assert n==info.file_size
     members.append(dict(path=info.filename,bytes=n,sha256=digest.hexdigest(),zip_crc32=info.CRC))
   record=dict(row,local_path=str(p.relative_to(R)),all_ZIP_members_streamed_SHA_CRC_verified=True,uncompressed_logical_bytes=logical,uncompressed_file_allocated_upper_bytes=allocated,members=members)
   records.append(record);put(O/'PARTIAL_WHEEL_INDEX.json',dict(wheels=records,raw_bytes=emitted,models=0))
  put(O/'WHEEL_INDEX.json',dict(wheels=records,total_raw_bytes=emitted,uncompressed_logical_bytes=sum(r['uncompressed_logical_bytes']for r in records),uncompressed_file_allocated_upper_bytes=sum(r['uncompressed_file_allocated_upper_bytes']for r in records),extraction_executed=False,imports_executed=False,source_metadata_sha256=scope['source_metadata_sha256'],models=0))
  put(O/'COMPLETION.json',dict(passed=True,closed=True,scope=scope['scope'],requests=5,raw_bytes=emitted,all_artifact_and_member_SHA_CRC_verified=True,install_executed=False,extraction_executed=False,JAX_or_author_imported=False,optimizer_calls=0,models=0,physical_native=0,runtime_qualified=False,remote_Phase_recovery_pending=True,closed_unix=time.time()))
 except BaseException as e:
  put(O/'FIRST_ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),completed_wheels=len(records),models=0))
  put(O/'COMPLETION.json',dict(passed=False,closed=True,completed_wheels=len(records),models=0,runtime_qualified=False));raise
 finally:signal.alarm(0)
if __name__=='__main__':main()
