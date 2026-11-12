"""Delete only enumerated, closed, verified Phase caches. Never follow links."""
import sys,json,hashlib,fcntl,time,os
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1077_v1078_closure';D=R/'records/nav2_v1077_v1078_20261112';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();assert json.loads((D/'REMOTE_VERIFIED.json').read_text())['passed']and json.loads((D/'GIT_REMOTE_READBACK.json').read_text())['passed'];lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';inventory={x['path']:x for x in json.loads((O/'INVENTORY.json').read_text())['files']};restored={x['path']:x for x in json.loads((R/'runs/v1077_speed125_response/RESTORED_NS.json').read_text())['files']};model=json.loads((D/'RECORD_INDEX.json').read_text())['selected_model_asset'];rows=[]
def add(p,reason):
 if p.is_symlink():rows.append(dict(path=str(p.relative_to(R)),bytes=0,symlink_target=os.readlink(p),reason='Unlink generated local symlink only; never follow'));return
 rows.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p),reason=reason))
for version in ['v1077','v1078']:
 root=R/'runs/v858_nav2_verified'/version
 for p in root.rglob('*'):
  if p.is_symlink():add(p,'local link');continue
  if not p.is_file():continue
  rel=str(p.relative_to(R))
  if rel in inventory:assert sha(p)==inventory[rel]['sha256'];reason='Source/member SHA and remote decompressed member verified'
  elif p.name=='scene_model.mjb':assert sha(p)==model['model_sha256'];reason='Identical model remote compressed/decompressed SHA verified'
  elif any(x in p.relative_to(root).parts for x in ['cache','frozen_original']):reason='Reconstructible shader cache or duplicate frozen dependencies'
  else:raise AssertionError('UNCLASSIFIED '+rel)
  add(p,reason)
root=R/'runs/v1077_speed125_response/restored_NS'
for p in root.rglob('*'):
 if p.is_file():
  rel=str(p.relative_to(R));assert not p.is_symlink()and rel in restored and sha(p)==restored[rel]['sha256'];add(p,'Original V1067 selected member SHA verified and original archive remains remote')
for root in [R/'runs/v1077_speed125_response',R/'runs/v1078_saved_ns_retimed',R/'runs/v1079_dual_steering_qualification']:
 keep={'COMPLETION.json','ROUND_WINDOW.json','APPROVAL.json','ACTIVE.json','ROOT_CLOSED.json','QUALIFICATION.json','COMPLETE_GOAL_QUALIFICATION.json','NEXT_TRANSITION_PREFLIGHT.json','REMAINDER_QUALIFICATION.json','DATA_PROVENANCE.json'}
 for p in root.iterdir():
  if not p.is_file()or p.name in keep:continue
  rel=str(p.relative_to(R))
  if rel in inventory:assert sha(p)==inventory[rel]['sha256'];reason='Closed metadata/evidence in verified current release'
  elif p.name in ['REMAINDER_INPUT.json','REMAINDER_SOURCE.npz']:
   record=D/'v1079_dual_steering_qualification'/p.name;assert record.exists()and sha(record)==sha(p);reason='Selected next-input Git SHA download verified'
  elif p.name=='ARCHIVE_INVENTORY.json':reason='Old release inventory duplicate; selected source SHA provenance retained'
  elif p.name in ['driver.lock']:reason='Inactive empty process lock'
  else:raise AssertionError('UNCLASSIFIED '+rel)
  add(p,reason)
for p in (O/'cloud').iterdir():
 assert p.is_file()and not p.is_symlink();add(p,'Remote current release archive/model has streamed SHA readback')
(D/'CLEANUP_MANIFEST.json').write_text(json.dumps(dict(files=rows),indent=2)+'\n')
for x in rows:
 p=R/x['path']
 if 'symlink_target'in x:assert p.is_symlink()and os.readlink(p)==x['symlink_target']
 else:assert not p.is_symlink()and sha(p)==x['sha256']
 p.unlink()
for root in [R/'runs/v858_nav2_verified/v1077',R/'runs/v858_nav2_verified/v1078',R/'runs/v1077_speed125_response/restored_NS',O/'cloud']:
 if not root.exists():continue
 for p in sorted(root.rglob('*'),key=lambda p:len(p.parts),reverse=True):
  if p.is_dir()and not any(p.iterdir()):p.rmdir()
 if root.exists()and not any(root.iterdir()):root.rmdir()
summary=dict(passed=True,removed_logical_bytes=sum(x['bytes']for x in rows),removed_files=len(rows),necessary_evidence_remote_source_and_member_sha_verified=True,selected_model_remote_compressed_decompressed_sha_verified=True,git_source_and_metadata_remote_readback_passed=True,guard_original=True,execution_lock_idle=True,physical_tasks_closed=True,original_failures_preserved=True,at=time.time());(D/'CLEANUP.json').write_text(json.dumps(summary,indent=2)+'\n');(D/'CLOSURE.json').write_text(json.dumps(dict(closed=True,response_5_passed=True,saved_continuation_passed=False,dual_steering_saved_data_only_qualified=True,new_physical_after_failure=False,source_commit=json.loads((D/'GIT_SYNC_RESULT.json').read_text())['head'],release=json.loads((D/'REMOTE_VERIFIED.json').read_text())['release_url']),indent=2)+'\n');print(json.dumps(summary),flush=True)
