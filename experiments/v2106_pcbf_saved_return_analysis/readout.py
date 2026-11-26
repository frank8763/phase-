"""Pure saved-array math, no solver or Phase model imports."""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json,math,os,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name
D=R/'runs/v2105_svg03_exact_transport_parent/math'
def read(p):return json.loads(p.read_text())
def main():
 os.sched_setaffinity(0,{4});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 assert not(S/'RESULT.json').exists();start=time.monotonic()
 diagnostic=read(D/'RESULT.json');raw=read(D/'AUXILIARY_RAW_RETURN.json');initial=read(D/'AUXILIARY_INITIAL.json')
 assert diagnostic['closed']and diagnostic['NLP_attempts']==diagnostic['NLP_returns']==1
 assert diagnostic['original_failure_reproduced']and initial['method']=='SLSQP'and initial['options']==dict(maxiter=400,ftol=1e-10,disp=False)
 assert not diagnostic['passed']and not raw['solver_success_and_residual_accepted']
 z=raw['x'];assert len(z)==25 and all(math.isfinite(v)for v in z)
 states=[[1.4,0.,0.]]
 for i in range(8):
  x,y,yaw=states[-1];v,w=z[2*i:2*i+2];states.append([x+.1*v*math.cos(yaw),y+.1*v*math.sin(yaw),yaw+.1*w])
 slacks=z[16:];residual=[states[i][0]**2+states[i][1]**2-1.+.005*i-slacks[i]for i in range(8)]+[states[-1][0]**2+states[-1][1]**2-.25**2-slacks[8]]
 computed_objective=sum(slacks[:8])+100*slacks[8]
 bound_violation=max([abs(v)-.25 for v in z[:16]]+[-v for v in slacks])
 maximum_residual=max(residual)
 assert abs(computed_objective-raw['fun'])<=1e-7 and max(abs(a+b)for a,b in zip(residual,raw['inequality_at_return']))<=1e-7
 exact_stage=[(F(7,5)-F(i,40))**2-1+F(i,200)for i in range(8)];exact_terminal=(F(7,5)-F(8,40))**2-F(1,4)**2
 assert min(exact_stage)>0 and exact_terminal>0
 optimum=sum(exact_stage)+100*exact_terminal
 witness_states=[[float(F(7,5)-F(i,40)),0.,0.]for i in range(9)]
 witness_slacks=[float(v)for v in exact_stage]+[float(exact_terminal)]
 gap=computed_objective-float(optimum)
 feasible=maximum_residual<=1e-7 and bound_violation<=1e-7
 near=feasible and abs(gap)<=1e-5
 if near and not raw['success']:finding='ORIGINAL_NATIVE_SUCCESS_STATUS_REFUSED_DESPITE_FEASIBLE_NEAR_GLOBAL_LOWER_BOUND_RETURN'
 elif not feasible:finding='RETURNED_POINT_VIOLATES_ORIGINAL_PRIMAL_OR_INPUT_BOUNDS'
 else:finding='NATIVE_ACCEPTANCE_FAILED_WITHOUT_ESTABLISHED_NEAR_OPTIMALITY'
 value=dict(closed=True,analysis_completed=True,models=0,solver_calls=0,physics=0,replay=0,formal_trials=0,original_algorithm_acceptance_passed=False,original_primary_preserved=True,Phase_vehicle_qualified=False,new_acceptance_gate_created=False,finding=finding,status=raw['status'],message=raw['message'],iterations=raw['nit'],solver_success=raw['success'],maximum_independent_primal_residual=maximum_residual,maximum_input_or_slack_bound_violation=bound_violation,original_primal_tolerance=1e-7,independent_objective=computed_objective,exact_global_lower_bound_fraction=str(optimum),exact_global_lower_bound=float(optimum),objective_gap_to_global_lower_bound=gap,within_original_primal_tolerance=feasible,near_optimal_for_diagnosis_only=near,mathematical_auxiliary_infeasibility_excluded_for_this_fixture=True,algebraic_witness=dict(inputs=[[-.25,0.]]*8,states=witness_states,slacks=witness_slacks),scope='EXPOSED_NON_PHASE_COLLINEAR_UNICYCLE_FIXTURE_ONLY',old_v2101_solver_status_still_unknown=True,input_SHA256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [D/'RESULT.json',D/'AUXILIARY_RAW_RETURN.json',D/'AUXILIARY_INITIAL.json',R/'experiments/v2101_parallel_priest_vehicle/nonlinear_filter.py']},late_local_analysis_not_in_previously_sealed_source_archive=True,wall_s=time.monotonic()-start)
 data=json.dumps(value,indent=2,allow_nan=False).encode()+b'\n';assert len(data)<=1024**2 and time.monotonic()-start<60;(S/'RESULT.json').write_bytes(data);print(json.dumps({k:value[k]for k in ['finding','status','iterations','maximum_independent_primal_residual','objective_gap_to_global_lower_bound','original_algorithm_acceptance_passed']}))
if __name__=='__main__':main()
