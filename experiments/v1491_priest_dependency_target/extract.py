"""Exact manifested extraction after full remote recovery; no installed imports."""
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path,PurePosixPath
import signal
import sys
import time
import traceback
import zipfile
R=Path(__file__).resolve().parents[2];O=R/'runs/v1491_priest_dependency_target';W=R/'runs/v1489_priest_wheel_capture';D=R/'runs/v1490_priest_dependency_recovery'

def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def put(p,v):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');t.replace(p)
def usage():
 seen=set();total=0
 for root,dirs,files in os.walk(R/'runs',followlinks=False):
  for p in [Path(root)]+[Path(root)/n for n in files]:
   st=p.lstat();key=(st.st_dev,st.st_ino)
   if key not in seen:seen.add(key);total+=st.st_blocks*512
 return total

def plan():
 index=json.loads((W/'WHEEL_INDEX.json').read_text());scope=json.loads((O/'SCOPE.json').read_text());before=usage();paths=set();directories={'.'};rows=[];increase=0;peak=0
 for row in sorted(index['wheels'],key=lambda x:-x['bytes']):
  p=R/row['local_path'];st=p.lstat();assert not p.is_symlink()and st.st_nlink==1 and st.st_size==row['bytes']and sha(p)==row['sha256']
  for member in row['members']:
   path=PurePosixPath(member['path']);assert not path.is_absolute()and '..'not in path.parts and str(path)not in paths
   paths.add(str(path));directories.update(str(v)for v in path.parents)
  increase+=row['uncompressed_file_allocated_upper_bytes'];peak=max(peak,increase)
  # Credit only planned post-extraction SHA-verified duplicate deletion.
  increase-=st.st_blocks*512
  rows.append(dict(raw_path=row['local_path'],sha256=row['sha256'],stat=[st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_nlink],allocated_bytes=st.st_blocks*512,file_allocation_cap=row['uncompressed_file_allocated_upper_bytes']))
 reserve=scope['metadata_error_cap_bytes']+scope['download_reserve_bytes']+scope['root_reserve_bytes']+4096*len(directories)
 full_peak=before+peak+reserve;assert full_peak<scope['limit_bytes'],'EXTRACTION_FULL_PEAK_REFUSED'
 result=dict(scope=scope['scope'],wheel_index_sha256=sha(W/'WHEEL_INDEX.json'),allruns_before_bytes=before,maximum_additional_files_before_verified_raw_removal_bytes=peak,directory_allocation_cap_bytes=4096*len(directories),metadata_error_cap_bytes=scope['metadata_error_cap_bytes'],complete_reserved_peak_bytes=full_peak,headroom_bytes=scope['limit_bytes']-full_peak,rows=rows,models=0,imports=False,created_unix=time.time())
 put(O/'EXTRACTION_PLAN.json',result);return result

def execute():
 assert not(O/'ONCE_CLAIM.json').exists()
 full=json.loads((D/'FULL_REMOTE_VERIFIED.json').read_text());assert full['passed']and json.loads((D/'TRANSPORT_CLEANUP.json').read_text())['passed']
 parent=json.loads((R/'runs/v1382_weekend_campaign/LEDGER.json').read_text());assert parent['active_round']is None and not parent['models_now_authorized']
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 prior=json.loads((O/'EXTRACTION_PLAN.json').read_text());scope=json.loads((O/'SCOPE.json').read_text());assert sha(W/'WHEEL_INDEX.json')==prior['wheel_index_sha256']and time.time()<scope['root_deadline_unix']
 # Recompute actual footprint using original saved raw identities; do not grant
 # more than the same frozen exact source plan or relax the reserve.
 before=usage();assert before+prior['maximum_additional_files_before_verified_raw_removal_bytes']+prior['directory_allocation_cap_bytes']+scope['metadata_error_cap_bytes']+scope['download_reserve_bytes']+scope['root_reserve_bytes']<scope['limit_bytes']
 with(O/'ONCE_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),plan_sha256=sha(O/'EXTRACTION_PLAN.json'),started_unix=time.time(),models=0),f)
 def expired(*_):raise TimeoutError('EXACT_EXTRACTION_SCOPE_EXPIRED')
 signal.signal(signal.SIGALRM,expired);signal.alarm(240);completed=[];removed=[]
 try:
  root=O/'site';root.mkdir();idx=json.loads((W/'WHEEL_INDEX.json').read_text());by_name={w['local_path']:w for w in idx['wheels']};actual_index=[]
  for row in prior['rows']:
   p=R/row['raw_path'];st=p.lstat();assert not p.is_symlink()and [st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_nlink]==row['stat']and sha(p)==row['sha256']
   wheel=by_name[row['raw_path']];wanted={x['path']:x for x in wheel['members']};seen=set()
   with zipfile.ZipFile(p)as z:
    for info in z.infolist():
     if info.is_dir():continue
     assert info.filename in wanted and info.filename not in seen;member=wanted[info.filename];name=PurePosixPath(info.filename);assert not name.is_absolute()and '..'not in name.parts
     target=root.joinpath(*name.parts);assert not target.exists()and target.resolve().is_relative_to(root.resolve())
     target.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256();count=0
     with z.open(info)as source,target.open('xb')as out:
      for block in iter(lambda:source.read(1024**2),b''):
       count+=len(block);assert count<=member['bytes'];out.write(block);h.update(block)
     assert count==member['bytes']and h.hexdigest()==member['sha256']and sha(target)==member['sha256'];seen.add(info.filename)
     actual_index.append(dict(path=str(target.relative_to(R)),bytes=count,sha256=member['sha256']))
   assert seen==set(wanted)
   st=p.lstat();assert [st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_nlink]==row['stat']and sha(p)==row['sha256']
   # Only these fully restored, fully remote verified duplicate artifacts.
   p.unlink();removed.append(row);completed.append(wheel['name'])
   put(O/'PROGRESS.json',dict(completed=completed,removed_duplicate_raw=removed,imports=False,models=0))
  put(O/'EXTRACTED_INDEX.json',dict(files=actual_index,original_wheel_index_sha256=prior['wheel_index_sha256'],remote_recovery_proof_sha256=sha(D/'FULL_REMOTE_VERIFIED.json'),imports=False,models=0))
  current=usage();assert current+scope['download_reserve_bytes']+scope['root_reserve_bytes']<scope['limit_bytes']
  put(O/'COMPLETION.json',dict(passed=True,closed=True,scope=scope['scope'],files=len(actual_index),removed_raw_wheels=removed,raw_wheels_now_remote_only=True,all_extracted_file_SHA_verified=True,dependency_imported=False,optimizer_calls=0,models=0,physical_native=0,runtime_qualified=False,allruns_after_bytes=current,closed_unix=time.time()))
 except BaseException as e:
  put(O/'FIRST_ERROR.json',dict(error=repr(e),traceback=traceback.format_exc(),completed=completed,removed_duplicate_raw=removed,models=0))
  put(O/'COMPLETION.json',dict(passed=False,closed=True,completed=completed,removed_duplicate_raw=removed,imports=False,models=0));raise
 finally:signal.alarm(0)

if __name__=='__main__':
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if '--execute'in sys.argv:execute()
  else:print(json.dumps({k:v for k,v in plan().items()if k!='rows'}))
