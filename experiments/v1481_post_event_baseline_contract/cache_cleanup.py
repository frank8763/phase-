"""Exact verified old-cache cleanup; keep latest first-event failure intact."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
R=Path(__file__).resolve().parents[2];O=R/'runs/v1481_post_event_baseline_contract'
CANDIDATES=('runs/v1472_closure_write_accounting/first_event/physics/scene_model.mjb','runs/v1474_pre_wire_resource_headroom/first_event/physics/scene_model.mjb','runs/v1474_pre_wire_resource_headroom/first_event/ACTUAL_OWNER_JOURNAL.jsonl')
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def write(p,v):
 with p.open('x')as f:f.write(json.dumps(v,indent=2)+'\n')
def allocated():return int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')],text=True,timeout=10).split()[0])
def state(path):
 s=path.lstat();assert path.is_file()and not path.is_symlink()and s.st_nlink==1 and path.parent.resolve()==path.parent
 return dict(bytes=s.st_size,allocated_bytes=s.st_blocks*512,device=s.st_dev,inode=s.st_ino,mtime_ns=s.st_mtime_ns,nlink=s.st_nlink,sha256=sha(path))
def plan():
 assert not(O/'DUPLICATE_CACHE_CLEANUP_PLAN.json').exists();rows=[]
 frozen=read(R/'runs/v1479_retirement_scope_binding/SOURCE_FREEZE.json')['files']
 latest_model=R/'runs/v1479_retirement_scope_binding/first_event/physics/scene_model.mjb';latest_sha=sha(latest_model)
 for name in CANDIDATES:
  assert name not in frozen and name.startswith(('runs/v1472_closure_write_accounting/first_event/','runs/v1474_pre_wire_resource_headroom/first_event/'))
  path=R/name;closed=path.parts[len(R.parts)+1];base=R/'runs'/closed/'actual_runtime_delivery';proofpath=base/'FULL_REMOTE_VERIFIED.json';indexpath=base/'ARCHIVE_INDEX.json';proof=read(proofpath)
  assert proof['passed']and all(proof[k]for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA'])
  assert read(R/'runs'/closed/'first_event/COMPLETION.json')['closed']and read(R/'runs'/closed/'CLOSED_REVIEW.json')['owner_exited']
  member=next(v for v in read(indexpath)['files']if v['path']==name);info=state(path);assert info['sha256']==member['sha256']and info['bytes']==member['bytes']
  if path.suffix=='.mjb':assert info['sha256']==latest_sha
  rows.append(dict(path=name,**info,archive_index_path=str(indexpath.relative_to(R)),archive_index_sha256=sha(indexpath),full_remote_verified_path=str(proofpath.relative_to(R)),full_remote_verified_sha256=sha(proofpath),release_url=proof['release_url'],reason='old closed nonlatest duplicate canonical model'if path.suffix=='.mjb'else'old closed nonlatest complete receipt raw; original failure summary and all states retained, recover full journal by verified member index'))
 value=dict(created_unix=time.time(),models=0,latest_failure_protected='runs/v1479_retirement_scope_binding/first_event',latest_model_sha256=latest_sha,rows=rows,expected_allocated_release_bytes=sum(v['allocated_bytes']for v in rows),current_source_or_latest_input_removed=False)
 write(O/'DUPLICATE_CACHE_CLEANUP_PLAN.json',value);return value

def execute():
 assert not(O/'DUPLICATE_CACHE_CLEANUP_RESULT.json').exists();parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and not parent['models_now_authorized']
 assert sha(R/'REVIEW_PENDING')==parent['review_pending_original_bytes_sha256']
 # Latest failure must itself be completely recoverable before any old cache
 # deletion; this never assumes that a source-only archive contains runtime.
 latest=read(R/'runs/v1479_retirement_scope_binding/actual_runtime_delivery/FULL_REMOTE_VERIFIED.json');assert latest['passed']and latest['every_member_SHA_and_link_text']and latest['recovery_index_download_SHA']
 value=read(O/'DUPLICATE_CACHE_CLEANUP_PLAN.json');removed=[]
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);before=allocated()
  for row in value['rows']:
   path=R/row['path'];assert state(path)=={k:row[k]for k in ['bytes','allocated_bytes','device','inode','mtime_ns','nlink','sha256']}
   assert sha(R/row['archive_index_path'])==row['archive_index_sha256']and sha(R/row['full_remote_verified_path'])==row['full_remote_verified_sha256']
  for row in value['rows']:(R/row['path']).unlink();removed.append(row['path'])
  after=allocated()
 result=dict(passed=True,models=0,removed_paths=removed,allocated_before_bytes=before,allocated_after_bytes=after,actual_allocated_release_bytes=before-after,expected_file_blocks_bytes=value['expected_allocated_release_bytes'],latest_failure_all_raw_retained=True,all_failure_denominators_and_reports_retained=True,recovery_indices_retained=True,only_exact_remote_SHA_mtime_inode_verified_closed_files_removed=True)
 write(O/'DUPLICATE_CACHE_CLEANUP_RESULT.json',result);return result
if __name__=='__main__':
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));p=argparse.ArgumentParser();p.add_argument('--plan',action='store_true');p.add_argument('--execute',action='store_true');a=p.parse_args();assert a.plan!=a.execute
 print(json.dumps(plan()if a.plan else execute()))
