"""Report rejected diagnostic hypotheses without changing prior FAIL or rerunning solver."""
from pathlib import Path
import json,math,sys,hashlib,os
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
assert os.sched_getaffinity(0)=={4};pins={}
def read(p):
 p=Path(p);raw=p.read_bytes();pins[str(p.relative_to(R))]=hashlib.sha256(raw).hexdigest();return json.loads(raw)
O=R/'runs/v2122_priest_quiescent_handoff/vehicle/actual';req=read(O/'PRIEST_OPTIMIZER_REQUEST.json');shadow=read(O/'cycle_000000_shadow.json');body=read(O/'cycle_000000_origin.json')['receipt']['packet']['body'][:2];rear=req['initial_state'][:2];rad=req['constructor_kwargs']['a_obs_1']
old=[sum((x-y)**2 for x,y in zip(rear,p))/rad**2 for p in req['static_points_world']]
radius=math.hypot(.44,.375)+shadow['required_raw_m']+.05/math.sqrt(2);candidate=[sum((x-y)**2 for x,y in zip(body,p))/radius**2 for p in req['static_points_world']]
P=R/'experiments/v2131_filter_measured_current';sys.path.insert(0,str(P));from context import read as source_read,load
files=source_read(R/'runs/v2131_filter_measured_current/SOURCE_FREEZE.json')['files'];dep=load('saved_kinematic_constraints_only',P/'filter_scope.py')
O=R/'runs/v2131_filter_measured_current/components/PCBF/actual';frame=read(O/'FILTER_QUERY_002_INPUT.json');raw=read(O/'FILTER_QUERY_002_RESULT.json');case=frame['request']['case'];known=frame['request']['public_known'];row=raw['answer']['returns'][0]
with dep.scope(files)as modules:
 values,_,labels=modules.filter.values_jac([.05,0.]*8,case,known,'PCBF')
 maxvalue=max(values);worst=labels[values.index(maxvalue)];n=len(values);width=n//9;slack=[max(v,0.)for v in values];weight=[1.]*(n-width)+[100.]*width
 # This is the exact feasible slack assignment at the declared INITIAL control,
 # no optimizer invocation or claim of optimality. All original functions unchanged.
 feasible_residual=max(v-s for v,s in zip(values,slack));assert feasible_residual<=0
 objective=sum(w*s for w,s in zip(weight,slack));old_objective=sum(w*(s+.01)for w,s in zip(weight,slack))
answer=dict(closed=True,models=0,solver_calls=0,physical_native=0,old_diagnostic_ASSERT_failures_retained=True,PRIEST=dict(old_initial_ellipse_violations=sum(x<1 for x in old),minimum_old_normalized_squared_distance=min(old),body_center_circle_candidate_initial_violations=sum(x<1 for x in candidate),minimum_candidate_normalized_squared_distance=min(candidate),body_center_candidate_radius=radius,body_center_circle_does_NOT_solve_input_feasibility=True,next_requirement='orientation-aware body representation or independently justified conservative decomposition and matching polynomial reference; do not launch until initial-boundary feasibility passes',original_fullstop_deficit_m=shadow['required_raw_m']-shadow['minimum_raw_m']),PCBF=dict(original_status=row['status'],original_success=row['success'],original_objective=row['objective'],original_residual=row['maximum_constraint_residual'],fixed_zero_slack_witness_NOT_feasible=True,fixed_witness_maximum_residual=maxvalue,fixed_witness_worst_constraint=worst,initial_exact_nonnegative_slack_residual=feasible_residual,initial_exact_nonnegative_slack_objective=objective,old_interior_slack_objective=old_objective,no_global_optimality_or_zero_slack_claim=True,proposed_future_initialization='slack=max(initial constraint,0) removes unnecessary artificial .01 slack, only as separately qualified new development variant',no_solver_retry_or_status_relaxation=True),input_sha256=pins)
assert all(hashlib.sha256((R/n).read_bytes()).hexdigest()==h for n,h in pins.items());assert not(S/'REJECTED_HYPOTHESES_SUPPLEMENT.json').exists();(S/'REJECTED_HYPOTHESES_SUPPLEMENT.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps({k:v for k,v in answer.items()if k!='input_sha256'}))
