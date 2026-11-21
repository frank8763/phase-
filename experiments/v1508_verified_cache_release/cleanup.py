"""One exact cleanup of already verified transport and nonlatest model copies."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as stream:
  for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
 return h.hexdigest()
def put(p,value):
 with p.open('x')as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
def state(p):
 st=p.lstat();assert p.is_file()and not p.is_symlink()and st.st_nlink==1 and p.parent.resolve()==p.parent
 return dict(bytes=st.st_size,allocated_bytes=st.st_blocks*512,device=st.st_dev,inode=st.st_ino,mtime_ns=st.st_mtime_ns,nlink=st.st_nlink,sha256=sha(p))
def allocated():
 seen=set();total=0
 for root,ds,fs in os.walk(R/'runs',followlinks=False):
  for p in [Path(root)]+[Path(root)/n for n in fs]:
   st=p.lstat();key=(st.st_dev,st.st_ino)
   if key not in seen:seen.add(key);total+=st.st_blocks*512
 return total

def plan():
 assert not(O/'PLAN.json').exists();frozen=read(R/'runs/v1507_priest_response_evidence/SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items());rows=[]
 root=R/'records/nav2_v856_20261107';index_path=root/'RECORD_INDEX.json';asset_path=root/'ASSET_REMOTE_VERIFICATION.json';proof_path=root/'FULL_REMOTE_VERIFIED.json';restore_path=R/'runs/v866_margin_qualification/runtime_RESTORED.json';index=read(index_path);assets=read(asset_path);proof=read(proof_path);restore=read(restore_path)
 assert proof['passed']and proof['all_server_digests_matched']and proof['all_streamed_download_sha_verified']and restore['passed']and restore['whole_and_members_sha_verified']and restore['restored_members']==restore['all_group_members']==6100
 group=next(v for v in index['archives']if v['group']=='v856-ros-runtime');assert group['source_sha_and_decompressed_member_sha_verified']and group['part_reassembly_sha_verified']and group['source_files']==6100
 for part in group['parts']:
  path=R/'runs/v866_margin_qualification/verified_transport_cache/phase-nav2-v856-20261107'/part['name'];name=str(path.relative_to(R));asset=next(v for v in assets if v['name']==part['name']);info=state(path)
  assert name not in frozen and info['sha256']==part['sha256']==asset['sha256']and info['bytes']==part['bytes']==asset['bytes']and asset['streamed_download_sha_verified']and asset['server_digest']=='sha256:'+info['sha256']
  rows.append(dict(path=name,**info,reason='old recovered compressed ROS transport copy, immutable extracted runtime untouched',remote_member=part,release_url=proof['release_url'],anchors={str(v.relative_to(R)):sha(v)for v in [index_path,asset_path,proof_path,restore_path]}))
 retained=R/'runs/v1479_retirement_scope_binding/first_event/physics/scene_model.mjb';model_sha=sha(retained)
 for name,base,completion in [
  ('runs/v1451_native_closure_qualification/zero200/physics/scene_model.mjb','runs/v1451_native_closure_qualification/actual_closure_delivery','runs/v1451_native_closure_qualification/COMPLETION.json'),
  ('runs/v1467_initializer_byte_grant/first_event/physics/scene_model.mjb','runs/v1467_initializer_byte_grant/actual_runtime_delivery','runs/v1467_initializer_byte_grant/first_event/COMPLETION.json')]:
  path=R/name;info=state(path);ip=R/base/'ARCHIVE_INDEX.json';pp=R/base/'FULL_REMOTE_VERIFIED.json';proof=read(pp);assert read(R/completion)['closed']and proof['passed']and all(proof[k]for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA'])
  member=next(v for v in read(ip)['files']if v['path']==name);assert name not in frozen and info['sha256']==member['sha256']==model_sha and info['bytes']==member['bytes']
  rows.append(dict(path=name,**info,reason='closed nonlatest duplicate compiled model, retained latest model byte-identical',remote_member=member,release_url=proof['release_url'],anchors={str(v.relative_to(R)):sha(v)for v in [ip,pp,R/completion]}))
 assert not subprocess.check_output(['git','ls-files','--',*[v['path']for v in rows]],cwd=R).strip()
 value=dict(created_unix=time.time(),rows=rows,expected_allocated_release_bytes=sum(v['allocated_bytes']for v in rows),frozen_manifest_sha256=sha(R/'runs/v1507_priest_response_evidence/SOURCE_FREEZE.json'),frozen_manifest='runs/v1507_priest_response_evidence/SOURCE_FREEZE.json',retained_latest_model_sha256=model_sha,models=0,physical_native=0,old_workers_not_restarted=True)
 put(O/'PLAN.json',value);return value

def execute():
 assert not(O/'RESULT.json').exists()and time.time()<1795395600;parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json');assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized'];assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 latest=read(R/'runs/v1504_priest_namespace_worker/actual_runtime_delivery/FULL_REMOTE_VERIFIED.json');assert latest['passed']and all(latest[k]for k in ['every_asset_actual_download_SHA','every_member_SHA_and_link_text','whole_archive_SHA','recovery_index_download_SHA'])
 value=read(O/'PLAN.json');assert sha(R/value['frozen_manifest'])==value['frozen_manifest_sha256'];frozen=read(R/value['frozen_manifest'])['files']
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert all(sha(R/n)==h for n,h in frozen.items());before=allocated()
  for row in value['rows']:
   assert row['path']not in frozen and state(R/row['path'])=={k:row[k]for k in ['bytes','allocated_bytes','device','inode','mtime_ns','nlink','sha256']}
   assert all(sha(R/n)==h for n,h in row['anchors'].items())
  for row in value['rows']:(R/row['path']).unlink()
  after=allocated();assert all(sha(R/n)==h for n,h in frozen.items())
 result=dict(passed=True,removed=[v['path']for v in value['rows']],expected_file_blocks_released=value['expected_allocated_release_bytes'],allruns_before_bytes=before,allruns_after_bytes=after,allocated_released_bytes=before-after,all_frozen_sources_unchanged=True,latest_input_failures_success_anchors_and_raw_preserved=True,old_removed_cache_now_remote_only=True,recover_by_exact_indices_before_reuse=True,all_recovery_indices_preserved=True,models=0,physical_native=0,full616MiB_future_peak_bytes=after+616*1024**2,storage_limit_bytes=10*1024**3,storage_snapshot_not_admission=True)
 put(O/'RESULT.json',result);return result
if __name__=='__main__':
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 assert sys.argv[1:]in [['--plan'],['--execute']];print(json.dumps(plan()if '--plan'in sys.argv else execute()))
