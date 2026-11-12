"""Bounded zero-model closed evidence archive; remote cleanup is separately verified."""
import sys,json,fcntl,time
from pathlib import Path
from common import *
paths();from resource_policy import apply
apply()
def main():
 assert json.loads((O/'COMPLETION.json').read_text())['closed'];assert(R/'REVIEW_PENDING').read_bytes()==(O/'GUARD.bin').read_bytes();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);D=R/'records/nav2_v1080_v1082_20261112';D.mkdir(exist_ok=True);assert not(D/'RECORD_INDEX.json').exists();arc=load('v1082_closed_stream_archive',R/'experiments/v1065_preflight_metadata_continuation/archive.py');files=[];models=[]
 for version in ['v1080','v1082']:
  root=R/'runs/v858_nav2_verified'/version
  for p in arc.walk(root):
   if any(x in p.relative_to(root).parts for x in ['cache','frozen_original']):continue
   if p.name=='scene_model.mjb':
    assert arc.sha(p)=='412f0616d1160dad61bb395919d9442372108ad094e07a5122274df5b29201f8';models.append(dict(path=str(p.relative_to(R)),sha256=arc.sha(p),restore_index='records/nav2_v1077_v1078_20261112/RECORD_INDEX.json',asset='canonical-ns-412f0616d1160dad.mjb.zst'));continue
   files.append(p)
 for name in ['v1080_turn_return_remaining','v1081_transient_speed_guard','v1082_guarded_saved_continuation']:
  root=R/'runs'/name
  for p in root.iterdir():
   if p.is_file()and not p.is_symlink()and p.name not in ['closure.console','ARCHIVE_ERROR.json']:files.append(p)
 for root in [C,R/'experiments/v1080_turn_return_remaining',R/'experiments/v1081_transient_speed_guard']:
  files.extend(p for p in root.iterdir()if p.is_file()and not p.is_symlink())
 for n in ['RPCCR_TURN_RETURN_V1080_REPORT.md','RPCCR_SPEED_GUARD_V1082_REPORT.md']:
  p=R/'docs'/n
  if p.exists():files.append(p)
 summary=json.loads((O/'COMPLETION.json').read_text());dump(D/'FINAL_SUMMARY.json',dict(v1080=json.loads((R/'runs/v1080_turn_return_remaining/COMPLETION.json').read_text()),v1082=summary,models_restore=models,new_whole_route_or24_passed=False));record,inventory=arc.package(R,files,O/'cloud','v1080-v1082-speed-guard-evidence');dump(D/'RECORD_INDEX.json',dict(repository='frank8763/phase-',release_tag='phase-speed-guard-v1080-v1082-20261112',archives=[record]));dump(D/'INVENTORY.json',dict(files=inventory));dump(D/'FINALIZED.json',dict(local_archive_source_decompressed_sha_verified=True,part_reassembly_verified=True,independent_actual_continuation_audit_passed=summary['passed'],scope='Closed evidence archive, functional pass is separate',remote_delivery_pending=True,models=0,integrations=0));print(json.dumps(dict(local_archived=True,source_files=len(inventory),raw_bytes=record['raw_bytes'],compressed_bytes=record['archive_bytes'],functional_pass=summary['passed'],remote_delivery_pending=True)),flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as e:dump(O/'ARCHIVE_ERROR.json',dict(error=repr(e),raw_retained=True,models=0));raise
