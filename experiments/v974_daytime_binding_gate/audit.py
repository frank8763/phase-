"""Unchanged full route audit plus the selected actual true-t0 factory contract."""
import importlib.util,json
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
spec=importlib.util.spec_from_file_location('v974_full_original_audit',R/'experiments/v968_rpp_closed_loop_night/audit.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
def audit(task):
 out=Path(task['output']);result=base.audit_route(task)
 try:
  selected=json.loads((out/'physics/SELECTED_NATIVE_BINDING.json').read_text());ok=selected['passed']and selected['native_tick']==0 and selected['integrations']==0 and selected['control_source']=='experiments/v958_hold_steering_contract/vehicle_control.py'
  result['selected_true_t0_native_binding']=ok;result['evidence_passed']=bool(result.get('evidence_passed')and ok);result['passed']=bool(result['passed']and ok)
 except Exception as e:result.update(passed=False,evidence_passed=False,selected_binding_error=repr(e))
 (out/'INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');return result
