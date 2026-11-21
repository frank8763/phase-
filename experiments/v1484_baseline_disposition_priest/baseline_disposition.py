"""Saved classification synthesis; no closed audit/model/qualification reruns."""
import hashlib
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def read(path):return json.loads(Path(path).read_text())
def proof(path):
 p=R/path;return dict(path=path,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def disposition():
 root='runs/v1370_overnight_controller_matrix/'
 rows=read(R/(root+'PARTIAL_RESULTS.json'));account=read(R/(root+'ACCOUNTING.json'));complete=read(R/(root+'COMPLETED.json'))
 byname={r['task']:r for r in rows};m=byname['coherent_mppi_static_main'];a=m['audit'];n=m['native'];ros=m['ros']
 assert m['attempted']is True and m['passed']is False and m['classification']==complete[m['task']]=='FUNCTIONAL_FAILURE_SAFE_COMPLETE'
 assert all(a['checks'][k]is True for k in ['fully_recorded','actual_clearance','bad_contacts_zero','own_full_replay','independent_allocation','complete_stop','sources_unchanged'])
 assert not a['passed']and not a['checks']['independent_whole_goal']and n['replay']['maximum_qpos_qvel_ctrl_mocap_error']==0.
 skipped=['coherent_mppi_static_repeat','coherent_mppi_horizon_m1_s01_main','coherent_mppi_horizon_m1_s01_repeat']
 assert all(k in account['skipped_dependencies']and k not in byname for k in skipped)
 rpp=read(R/'runs/v1479_retirement_scope_binding/CLOSED_REVIEW.json')
 assert rpp['closed']and not rpp['passed']and rpp['no_relaunch_or_frozen_edit']and rpp['no_infinite_RPP_rescue']and not rpp['whole_route_passed']
 return dict(scope='DEVELOPMENT_BASELINE_DISPOSITION_NO_NEW_TRIALS',rows=[
  dict(method='Original engineering coherent/deadband MPPI in frozen shared skeleton',stage='V1370 static main',attempted=True,outcome='FUNCTIONAL_FAILURE_SAFE_COMPLETE',saved_audit_passed=False,actual_native=n['new_actual_native'],ownreplay_native=n['own_replay_native'],action_status=ros['action_status'],error_code=ros['error_code'],goal_distance_m=n['whole_goal_distance_m'],recovery_component_success_does_not_override_static_main_failure=True),
  dict(method='Same original MPPI task dependency chain',stage='V1370 static repeat and dynamic main/repeat',attempted=False,outcome='SKIPPED_DEPENDENCY',tasks=skipped,not_counted_as_executed_failure=True),
  dict(method='Disclosed shared skeleton + original RPP + current-event witness',stage='V1479 live first-event qualification',attempted=True,outcome='CURRENT_MODEL_WITNESS_REFUSED',actual_native=rpp['actual_native'],ownreplay_native=rpp['own_replay_native'],actual_notice_reached=rpp['first_actual_event_notice_reached'],actual_bridge_applied=rpp['event_bridge_actual_execution'],whole_route_passed=False,independent_full_actual_audit_unexecuted=rpp['independent_recorded_audit_unexecuted']),
  dict(method='New engineering MPPI current-event adapter',stage='V1483 draft',attempted=False,outcome='SOURCE_PREPARATION_UNQUALIFIED',revision_registered=6,static_dependency_not_passed=True),
  dict(method='PRIEST pinned author implementation / Phase adaptation',stage='V1484 author-source inspection',attempted=False,outcome='NOT_REPRODUCED_NOT_RUNTIME_ADMITTED')],
  decision='Retain finite MPPI static non-success and original dynamic unexecuted dependency. Do not run more closed MPPI/RPP tasks or finish an unused runtime only to spend its draft. Proceed with author-source and explicit causal/Ackermann/full-footprint adaptation requirements for PRIEST; any executable new method needs separate preregistration and bounded qualification.',
  formal_matched_comparison_completed=False,statistical_or_algorithm_universal_superiority_established=False,independent_unseen_trials_added=0,new_models=0,new_physical_native=0,old_counts_added_to_parent=False,
  source_proofs=[proof(p)for p in [root+'PARTIAL_RESULTS.json',root+'ACCOUNTING.json',root+'COMPLETED.json','experiments/v1370_overnight_controller_matrix/relay_policy.py','runs/v1479_retirement_scope_binding/CLOSED_REVIEW.json','runs/v1483_mppi_current_event_backend/ORIGINAL_DEPENDENCY_STATUS.json']])

if __name__=='__main__':print(json.dumps(disposition(),indent=2,allow_nan=False))
