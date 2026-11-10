"""Preserve the primary pre-ARM failure; completed scientific audit is unchanged."""
import importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def audit(task):
    out=Path(task['output'])
    binding=json.loads((out/'BACKEND_ENTRY_BINDING.json').read_text())if(out/'BACKEND_ENTRY_BINDING.json').exists()else{}
    assert binding.get('passed')is True and binding.get('exact_path_binding')is True,'BACKEND_ENTRY_BINDING_NOT_VERIFIED'
    p=out/'RESULT.json';n=json.loads(p.read_text())if p.exists()else{}
    if n.get('status')!='NATIVE_COMPLETE':
        result=dict(passed=False,evidence_passed=False,status=n.get('status'),reason='NO_COMPLETE_NAVIGATION_NEVER_ASSUME_REPLAY_EXISTS',
            actual_native=n.get('actual_native'),replay_native=n.get('replay_native'),private_native=n.get('private_native'),models_during_audit=0)
        (out/'INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');return result
    s=importlib.util.spec_from_file_location('v1006_unchanged_scientific_audit',R/'experiments/v1018_input_progress_night/scientific_audit.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    q=R/'experiments/v1016_saved_route_diagnosis/shaping_audit.py';spec=importlib.util.spec_from_file_location('shaping_audit',q);shape=importlib.util.module_from_spec(spec);spec.loader.exec_module(shape);sys.modules['shaping_audit']=shape
    return m.audit(task)
