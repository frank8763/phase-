"""One bounded local archive; source and qualification freeze rechecked."""
import importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=R/'experiments/v1061_three_route_readiness';O=R/'runs/v1061_three_route_readiness';D=R/'records/nav2_v1061_20261111';sys.path.insert(0,str(C));import archive as arc

def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
freeze=json.loads((C/'SOURCE_FREEZE.json').read_text());assert all(arc.sha(R/p)==h for p,h in freeze['files'].items());assert json.loads((D/'FINAL_INDEPENDENT_AUDIT.json').read_text())['passed'];assert not(O/'cloud').exists();assert sum(p.stat().st_size for p in arc.walk(O))<2*1024**3
files={R/p for p in freeze['files']};files.update(arc.walk(C));files.update(arc.walk(O));files.update(arc.walk(D));files.update(arc.walk(Path(__file__).parent));files.update([R/'CURRENT_EXPERIMENT.json',R/'RESEARCH_STATUS.md',R/'docs/RPCCR_THREE_ROUTE_READINESS_V1061_REPORT.md']);record,inventory=arc.package(R,files,O/'cloud','v1061-three-route-software',lambda:sum(p.stat().st_size for p in arc.walk(O))<2*1024**3)
dump(D/'RECORD_INDEX.json',dict(repository='frank8763/phase-',release_tag='phase-three-route-software-v1061-20261111',archives=[record],restore_script='experiments/v1061_preparation_delivery/restore.py',original_physical_dependencies=['phase-fresh-route-v1056-20261111','phase-fresh-repeat-v1058-20261111'],all_current_software_inputs_and_outputs_included=True));dump(D/'FINALIZED.json',dict(passed=True,scope='SOFTWARE_PREPARATION_ONLY',local_source_and_all_decompressed_members_verified=True,physical_trials_executed=0,models_authorized=False,remote_delivery_pending=True));print(json.dumps(record))
