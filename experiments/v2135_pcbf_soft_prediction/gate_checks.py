"""Saved numerical candidates, zero new solver/physics."""
from context import R,C,SOURCE as S,read,put,sha
from proposal_gate import admissible
import copy,json,ast
matrix=read(R/'runs/v2134_pcbf_remaining_numeric/math/RESULT.json');rows=[r for r in matrix['rows']if r['variant']=='minimal_feasible_slack'and r['role']=='POSITIVE_COMPONENT_INPUT'];checks=[]
for row in rows:
 a=row['answer'];assert a['passed']and all(x['success']and x['maximum_constraint_residual']<=1e-7 for x in row['returns'])
 assert admissible(a);checks.append(dict(case=row['case_id'],maximum_prediction_slack=a['maximum_slack'],ideal_future_hard_geometry_passed=a['original_hard_geometry_passed'],numerical_proposal_eligible=True,physical_execution_permitted=False))
assert any(x['maximum_prediction_slack']>1e-7 for x in checks)
base=copy.deepcopy(rows[0]['answer']);bad=dict(base,passed=False);assert not admissible(bad);assert not admissible(dict(base,original_hard_geometry_passed=False));assert not admissible(dict(base,maximum_command_domain_violation=1e-4));assert not admissible(dict(base,maximum_command_domain_violation=float('nan')))
for n in ['response.py','navigation.py','work.py','error_stop.py','capture.py','quota.py','base_quota.py','granted_quota.py']:
 assert(C/n).read_bytes()==(R/'experiments/v2131_filter_measured_current'/n).read_bytes(),n
nav=ast.parse((C/'navigation.py').read_text());assert "assert shadow['passed']"in ast.unparse(nav)and "assert admission['passed']"in ast.unparse(nav)
put(S/'SOFT_PREDICTION_GATE_PROOF.json',dict(passed=True,models=0,optimizer_queries=0,physics=0,cases=checks,negative_cases=['failed_numerical_status','ideal_hard_geometry_refused','illegal_raw_domain','nonfinite_domain'],original_physical_prediction_and_actual_gates_byte_exact=True,extra_zero_slack_ideal_future_gate_removed=True,predicted_slack_not_mistaken_for_unsafe_actual_permission=True))
print(json.dumps(dict(passed=True,cases=checks,models=0,optimizer_queries=0)))
