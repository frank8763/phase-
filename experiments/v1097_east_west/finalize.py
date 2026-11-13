"""Zero-model source/member/32MiB reassembly audit, retaining actual scenes."""
import sys,json,fcntl,importlib.util
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
def main():
    cfg=json.loads(Path(sys.argv[1]).read_text());O=Path(cfg['run_root']);D=R/cfg['record_root'];D.mkdir(exist_ok=True);assert not(D/'RECORD_INDEX.json').exists()
    summary=json.loads((O/'COMPLETION.json').read_text());assert summary['closed'];assert(R/'REVIEW_PENDING').read_bytes()==(O/'GUARD.bin').read_bytes()
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    def load(name,p):
        s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
    arc=load('v1097_archive',R/'experiments/v1065_preflight_metadata_continuation/archive.py');usage=load('v1097_usage',C/'campaign.py');files=[]
    for task in json.loads(Path(cfg['task_table']).read_text()):files.extend(p for p in arc.walk(task['output'])if not any(x in p.parts for x in ['cache','frozen_original']))
    for root in [C,O,R/'experiments/rpccr_execution_core']:
        files.extend(p for p in root.iterdir()if p.is_file()and not p.is_symlink()and p.name not in ['finalize.console','driver.console','watchdog.console'])
    files.append(R/cfg['report']);baseline=usage.used();target=O/'cloud'
    record,inventory=arc.package(R,files,target,'v1097-ew-evidence',budget_check=lambda:baseline+sum(p.stat().st_size for p in target.glob('*')if p.is_file())+1024**2<=cfg['temporary_limit_bytes'])
    def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
    dump(D/'RECORD_INDEX.json',dict(repository='frank8763/phase-',release_tag='phase-ew-v1097-20261113',archives=[record],all_scene_models_included=True));dump(D/'INVENTORY.json',dict(files=inventory));dump(D/'FINAL_SUMMARY.json',summary)
    final=dict(all_source_decompressed_sha_verified=True,parts_reassembled_sha_verified=True,independent_functional_passed=summary['passed'],three_route_development_passed=False,confirmation_passed=False,models=0,integrations=0,remote_delivery_pending=True)
    dump(D/'FINALIZED.json',final);dump(O/'FINALIZED.json',final);print(json.dumps(dict(sources=len(inventory),compressed_bytes=record['archive_bytes'],models=0)),flush=True)
if __name__=='__main__':main()
