"""Local event audit preserves every original whole-route outcome separately."""
import importlib.util
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1477_full_route_recorded_audit_unchanged',R/'experiments/v1456_route_closure_binding/audit.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
WHOLE_TASK_GATES={'closed_original_action_and_goal','whole_original_goal','actual_detection_and_after_detection_travel','functional_and_evidence_complete'}
def audit(task):
 out=Path(task['output']);result=json.loads((out/'RESULT.json').read_text());ros=json.loads((out/'ROS_RESULT.json').read_text())
 original=base.audit(task) # Full original science gates remain visible/unchanged.
 assert WHOLE_TASK_GATES<=set(original['checks'])
 local={k:v for k,v in original['checks'].items()if k not in WHOLE_TASK_GATES}
 receipt=result.get('live_first_event',{})
 local.update(first_actual_current_event_complete=receipt.get('complete_actual_bridge')is True and receipt.get('event_index')==0,
  bounded_scope_not_navigation_claim=result.get('partial_navigation_attempt')is True and result.get('whole_route_navigation_passed')is False,
  runtime_component_completed=result.get('runtime_component_passed')is True,
  complete_actual_ROS_cooperative_close=ros.get('closed')is True and ros.get('controller_server_exited')is True and not ros.get('evidence_write_errors'),
  source_state_first_capture_complete=result.get('fullstate_prefix_before_contact',{}).get('complete')is True,
  no_first_or_secondary_native_error=not result.get('first_error')and not result.get('save_errors'),
  exactly_one_recorded_event=len(original['event_array_proofs'])==1)
 return dict(passed=all(local.values()),scope='LIVE_FIRST_EVENT_RUNTIME_QUALIFICATION',checks=local,original_whole_route_audit=original,whole_route_navigation_passed=False,whole_route_gates_not_waived=sorted(WHOLE_TASK_GATES),partial_navigation_attempt=True,actual_reviewed=original['actual_reviewed'],models=0,physical_native=0,analytical_native=0,pair_executed=False)
