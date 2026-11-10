"""Preserve the primary pre-ARM failure; completed scientific audit is unchanged."""
import importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def audit(task):
    out=Path(task['output']);p=out/'RESULT.json';n=json.loads(p.read_text())if p.exists()else{}
    if n.get('status')!='NATIVE_COMPLETE':
        result=dict(passed=False,evidence_passed=False,status=n.get('status'),reason='NO_COMPLETE_NAVIGATION_NEVER_ASSUME_REPLAY_EXISTS',
            actual_native=n.get('actual_native'),replay_native=n.get('replay_native'),private_native=n.get('private_native'),models_during_audit=0)
        (out/'INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');return result
    s=importlib.util.spec_from_file_location('v1006_unchanged_scientific_audit',R/'experiments/v1014_atomic_handoff_navigation/scientific_audit.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    return m.audit(task)
