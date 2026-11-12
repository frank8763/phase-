"""Archive all task scenes explicitly, without a cross-route model exclusion."""
import sys,json,fcntl,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
from resource_policy import apply
apply()
def finalize(cfg):
 O=Path(cfg['run_root']);D=R/cfg['record_root'];D.mkdir(exist_ok=True);assert not(D/'RECORD_INDEX.json').exists();summary=json.loads((O/'COMPLETION.json').read_text());assert summary['closed'];assert(R/'REVIEW_PENDING').read_bytes()==(O/'GUARD.bin').read_bytes()
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 spec=importlib.util.spec_from_file_location('night_full_scene_archive',R/'experiments/v1065_preflight_metadata_continuation/archive.py');arc=importlib.util.module_from_spec(spec);spec.loader.exec_module(arc);files=[]
 for task in json.loads(Path(cfg['task_table']).read_text()):
  files.extend(p for p in arc.walk(task['output'])if not any(x in p.parts for x in ['cache','frozen_original']))
 for root in [C,O,R/'experiments/rpccr_execution_core']:
  files.extend(p for p in root.iterdir()if p.is_file()and not p.is_symlink()and p.name not in ['finalize.console','driver.console'])
 files.append(R/cfg['report'])
 # Streaming output cannot exceed the night's explicit disk ceiling either.
 spec2=importlib.util.spec_from_file_location('night_archive_usage',C/'campaign.py');usage=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(usage);baseline=usage.used();target=O/'cloud'
 def budget():return baseline+sum(p.stat().st_size for p in target.glob('*')if p.is_file())+1024**2<=cfg['temporary_limit_bytes']
 record,inventory=arc.package(R,files,target,'v1089-night-route-evidence',budget_check=budget)
 def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
 dump(D/'RECORD_INDEX.json',dict(repository='frank8763/phase-',release_tag='phase-night-route-v1089-20261112',archives=[record],all_scene_models_included=True));dump(D/'INVENTORY.json',dict(files=inventory));dump(D/'FINAL_SUMMARY.json',summary);dump(D/'FINALIZED.json',dict(all_source_decompressed_sha_verified=True,parts_reassembled_sha_verified=True,independent_functional_passed=summary['passed'],three_route_development_passed=summary['three_route_development_passed'],confirmation_passed=summary['confirmation_passed'],models=0,integrations=0,remote_delivery_pending=True));print(json.dumps(dict(sources=len(inventory),compressed_bytes=record['archive_bytes'],models=0)),flush=True)
if __name__=='__main__':finalize(json.loads(Path(sys.argv[1]).read_text()))
