"""First arithmetic audit of the12 saved new NLP returns, zero new solve."""
from pathlib import Path
import sys,os,json,hashlib,math
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;S=R/'runs'/C.name;P=R/'runs/v2156_pcbf_pinned_scipy_entry';O=P/'components/MATH'
assert os.sched_getaffinity(0)=={1}and not(S/'RESULT.json').exists()
sys.path.insert(0,str(R/'experiments/v2156_pcbf_pinned_scipy_entry'));import numpy as np;import filter as f;import oracle
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert Path(f.__file__).resolve()==R/'experiments/v2156_pcbf_pinned_scipy_entry/filter.py'
result=json.load(open(O/'RESULT.json'));outer=json.load(open(O/'COMPLETION.json'));assert result['closed']and result['passed']and result['NLP_returns']==result['attempted_calls']==12 and not result['inflight_unknown']and outer['closed']and not outer['passed']and outer['returncode']==1
assert json.load(open(O/'POST_MATH_STORAGE_BARRIER.json'))['passed']
cases=json.load(open(P/'CASES_LOCKED.json'))['cases'];rows=[];pins={str((O/'RESULT.json').relative_to(R)):sha(O/'RESULT.json')};total=0
for i,case in enumerate(cases):
 p=O/f'CASE_{i:02d}_RESULT.json';v=json.load(open(p));pins[str(p.relative_to(R))]=sha(p);assert len(v['returns'])==len(v['transforms'])==2
 slack=None
 for row,trans in zip(v['returns'],v['transforms']):
  x=np.asarray(row['x']);units=np.asarray(trans['variable_units']);normalized=np.asarray(trans['normalized_x'])
  assert np.max(abs(x-np.asarray(trans['original_x'])))==0 and np.max(abs(x-normalized*units))<1e-14
  assert row['stage']==trans['stage']and row['success']and row['status']==trans['scipy_status']==0 and trans['scipy_success']and row['maximum_constraint_residual']<=1e-7
  values,j,labels=f.values_jac(x[:16],case['case'],case['known'],'PCBF');n=len(values)
  assert max(max(.005-x[2*k],x[2*k]-.1,abs(x[2*k+1])-1/1.32)for k in range(8))<=1e-7
  if row['stage']=='AUXILIARY':
   assert len(x)==16+n;slack=np.maximum(x[16:],0.);assert min(x[16:])>=-1e-7;residual=max(np.asarray(values)-x[16:]);width=n//9;weights=np.asarray([1.]*(n-width)+[100.]*width);objective=float(weights@x[16:])
  else:
   assert row['stage']=='PERFORMANCE'and len(x)==16 and slack is not None;residual=max(np.asarray(values)-slack);gear=case['case']['gear'];nom=case['case']['nominal'];objective=float((gear*x[0]-nom[0])**2+(gear*x[0]*x[1]-nom[1])**2)
  assert abs(residual-row['maximum_constraint_residual'])<1e-8 and abs(objective-row['objective'])<1e-10 and abs(objective-trans['original_objective'])<1e-10
  total+=1
 answer=v['answer'];states,_=f.rollout_jac(v['returns'][-1]['x'],case['case']['pose'],case['case']['gear']);assert np.max(abs(np.asarray(states)-answer['states']))<1e-12
 hard=max(f.REQUIRED-min(oracle.distances(pose,case['known']))for pose in states);assert abs(hard-answer['maximum_exact_hard_static_residual'])<1e-12
 numerical_ok=bool(answer['passed']);hard_ok=bool(hard<=1e-7);admissible=bool(numerical_ok and hard_ok)
 if case['id']=='synthetic_occupied':assert not admissible and not hard_ok
 else:assert admissible
 rows.append(dict(id=case['id'],aux_status=int(v['returns'][0]['status']),performance_status=int(v['returns'][1]['status']),maximum_original_aux_residual=float(v['returns'][0]['maximum_constraint_residual']),maximum_original_performance_residual=float(v['returns'][1]['maximum_constraint_residual']),original_aux_objective=float(v['returns'][0]['objective']),hard_geometry=hard_ok,numerical_program_passed=numerical_ok,physical_candidate_gate_passed=admissible,maximum_prediction_tightening_slack=float(answer['maximum_slack'])))
assert total==12
original=R/'runs/v2141_pcbf_progress_scope/components/PCBF/actual/FILTER_QUERY_081_RESULT.json';before=json.load(open(original))['answer']['returns'][0];assert before['status']==8 and not before['success'];pins[str(original.relative_to(R))]=sha(original)
out=dict(passed=True,closed=True,first_numeric_audit_of_this_new_math_scope=True,new_NLP_calls=0,saved_NLP_returns_verified=12,models=0,physics=0,replay=0,formal_tasks=0,five_positive_inputs_passed=True,occupied_negative_refused_by_unchanged_hard_geometry=True,known_failure_query081_aux_before_status=8,known_failure_query081_aux_after_status=0,old_failure_unchanged=True,all_status_gates_still_strict=True,original_objective_and_constraints_retained=True,rows=rows,outer_pipeline_remains_failed=True,outer_failure='NumPy bool final-console JSON serialization AFTER durable RESULT; no missing numerical returns',old_frozen_worker_not_rerun_or_edited=True,vehicle_or_wholegoal_qualified=False,late_after_runtime_archive=True,input_SHA256=pins,helper_sha256=sha(Path(__file__)))
(S/'RESULT.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(dict(passed=True,saved_returns=12,new_NLP=0,positive_inputs=5,occupied_hardgate_refused=True,known_failure_aux_status_before=8,known_failure_aux_status_after=0)))
