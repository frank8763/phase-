"""Immutable supplementary review archive and previously closed actual archive."""
import sys,json,hashlib,importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=R/'runs/navigation_review_20261112';D=R/'records/navigation_review_20261112';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
s=importlib.util.spec_from_file_location('navigation_review_stream_archive',R/'experiments/v1065_preflight_metadata_continuation/archive.py');arc=importlib.util.module_from_spec(s);s.loader.exec_module(arc)
def main():
 assert not(D/'RECORD_INDEX.json').exists();files=[]
 for n in ['README.md','CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/PHASE_NAVIGATION_CURRENT.md','docs/PHASE_NAVIGATION_FULL_REVIEW_20261112.md','docs/RPCCR_TURN_RETURN_V1080_REPORT.md','docs/RPCCR_SPEED_GUARD_V1082_REPORT.md','docs/history/README_BEFORE_NAVIGATION_REVIEW_20261112.md']:files.append(R/n)
 for root in [R/'experiments/navigation_review_20261112',D]:files.extend(p for p in root.iterdir()if p.is_file()and not p.is_symlink())
 for p in O.iterdir():
  if p.is_file()and p.name!='package.console':files.append(p)
 latest=R/'records/nav2_v1080_v1082_20261112';files.extend(p for p in latest.iterdir()if p.is_file()and not p.is_symlink());record,inventory=arc.package(R,files,O/'cloud','navigation-full-review-supplement');old=json.loads((latest/'RECORD_INDEX.json').read_text());index=dict(repository='frank8763/phase-',release_tag=old['release_tag'],archives=[*old['archives'],record],prior_model_restore='records/nav2_v1077_v1078_20261112/RECORD_INDEX.json');(D/'RECORD_INDEX.json').write_text(json.dumps(index,indent=2)+'\n');(D/'SUPPLEMENT_INVENTORY.json').write_text(json.dumps(dict(files=inventory),indent=2)+'\n');print(json.dumps(dict(sources=len(inventory),raw_bytes=record['raw_bytes'],compressed_bytes=record['archive_bytes'],both_batches_still_failed=True,models=0,integrations=0)),flush=True)
if __name__=='__main__':main()
