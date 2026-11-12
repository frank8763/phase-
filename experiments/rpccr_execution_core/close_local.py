"""Shared zero-model immutable evidence closure; remote transfer remains bounded."""
import sys,json,fcntl
from pathlib import Path
CORE=Path(__file__).resolve().parent;R=CORE.parents[1];sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(CORE));from physical_ops import dump
from kernel import load
cfg=json.loads(Path(sys.argv[1]).read_text());O=Path(cfg['run_root']);summary=json.loads((O/'COMPLETION.json').read_text());assert summary['closed'];assert(R/'REVIEW_PENDING').read_bytes()==(O/'GUARD.bin').read_bytes();lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);D=R/cfg['record_root'];D.mkdir(exist_ok=True);assert not(D/'RECORD_INDEX.json').exists();arc=load('shared_execution_archive',R/'experiments/v1065_preflight_metadata_continuation/archive.py');files=[]
for task in json.loads(Path(cfg['task_table']).read_text()):
 for p in arc.walk(task['output']):
  if any(x in p.relative_to(Path(task['output'])).parts for x in ['cache','frozen_original']):continue
  if p.name=='scene_model.mjb':assert arc.sha(p)=='412f0616d1160dad61bb395919d9442372108ad094e07a5122274df5b29201f8';continue
  files.append(p)
for root in [CORE,Path(cfg['batch_source']),O]:
 for p in root.iterdir():
  if p.is_file()and not p.is_symlink()and p.name!='closure.console':files.append(p)
files.append(R/cfg['report']);record,inventory=arc.package(R,files,O/'cloud',cfg['version']+'-braking-reserve');dump(D/'RECORD_INDEX.json',dict(repository='frank8763/phase-',release_tag='phase-braking-reserve-'+cfg['version']+'-20261112',archives=[record],canonical_model_reference='records/nav2_v1077_v1078_20261112/RECORD_INDEX.json'));dump(D/'INVENTORY.json',dict(files=inventory));dump(D/'FINAL_SUMMARY.json',summary);dump(D/'FINALIZED.json',dict(all_source_decompressed_sha_verified=True,parts_reassembled_sha_verified=True,independent_functional_passed=summary['passed'],remote_delivery_pending=True,models=0,integrations=0));print(json.dumps(dict(local_archived=True,sources=len(inventory),compressed_bytes=record['archive_bytes'],functional_passed=summary['passed'],raw_retained=True)),flush=True)
