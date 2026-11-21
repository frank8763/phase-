"""Original MPPI predecessor status, read-only and never a retry authority."""
import hashlib
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def status():
 root=R/'runs/v1370_overnight_controller_matrix'
 results=root/'PARTIAL_RESULTS.json';accounting=root/'ACCOUNTING.json'
 rows=read(results);account=read(accounting)
 main=next(x for x in rows if x['task']=='coherent_mppi_static_main')
 repeat=[x for x in rows if x['task']=='coherent_mppi_static_repeat']
 assert len(repeat)<=1
 n=main['native'];ros=main['ros'];a=main['audit']
 dependency_passed=bool(repeat and repeat[0]['attempted']is True and repeat[0]['passed']is True and repeat[0]['audit']['passed']is True)
 return dict(original_dependency='coherent_mppi_static_repeat',dependency_passed=dependency_passed,
  original_static_main_attempted=main['attempted'],original_static_main_passed=main['passed'],original_classification=main['classification'],
  original_static_main_actual_native=n['new_actual_native'],original_static_main_ownreplay_native=n['own_replay_native'],
  original_action_status=ros['action_status'],original_error_code=ros['error_code'],
  original_goal_distance_m=n['whole_goal_distance_m'],original_forward_displacement_m=n['forward_displacement_m'],
  original_audit_passed=a['passed'],original_complete_stop=a['checks']['complete_stop'],original_own_replay_passed=a['checks']['own_full_replay'],
  repeat_attempted=bool(repeat and repeat[0]['attempted']),repeat_skipped_dependency='coherent_mppi_static_repeat'in account['skipped_dependencies'],
  original_dynamic_main_skipped='coherent_mppi_horizon_m1_s01_main'in account['skipped_dependencies'],
  source_proofs={str(p.relative_to(R)):sha(p)for p in [results,accounting]},
  closed_predecessor_not_relaunched=True,new_physical_native=0,new_models=0,old_counts_not_added_to_parent=True,
  no_permission_to_erase_dependency_or_retry_static_failure=True)

def authorize_dynamic():
 proof=status()
 if not proof['dependency_passed']:raise RuntimeError('ORIGINAL_MPPI_STATIC_REPEAT_DEPENDENCY_NOT_PASSED_STATIC_MAIN_FUNCTIONAL_FAILURE')
 return proof
