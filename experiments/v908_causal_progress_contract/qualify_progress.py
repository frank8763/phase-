"""Saved-source terminal mismatch red cases; candidate gate and negative tests."""
import copy,json,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(C))
from progress_gate import terminal_witness
from refuge_logic import wait_ok
root=R/'runs/v858_nav2_verified/v907/main_we';rows=json.loads((root/'ROUTER_REQUESTS.json').read_text());known=json.loads((root/'physics/SETUP.json').read_text())['known'];proofs=[];checks={}
for row in rows:
 s=row['causal_forecast_source']
 if row['navigation_role']!='ORIGINAL'or s['center_support_bounds']is None:continue
 snapshot=(dict(native_tick=s['source_native_tick']),dict(source_native_tick=s['source_native_tick'],source_age_s=s['source_age_s'],support_bounds=s['center_support_bounds']))
 p=terminal_witness(row['original_goal'],known,snapshot);proofs.append(p)
 selected=row['terminal_region_choice']['selected_xy']+[row['original_goal'][2]]
 assert not wait_ok(selected,s['center_support_bounds'],s['source_age_s'],6.)
 if p['admitted']:
  assert p['selected']['static_ok'] and p['selected']['hold6'] and p['total_goal_budget_m']<.45
checks['all35_current_reference_terminal_choices_reproduce_mismatch']=len(proofs)==35
checks['no_invalid_terminal_reported_valid']=all(not p['admitted']or(p['selected']['static_ok']and p['selected']['hold6'])for p in proofs)
for name,changes in [('future',dict(source_native_tick=snapshot[0]['native_tick']+1)),('stale',dict(source_age_s=.21))]:
 altered=copy.deepcopy(snapshot);altered[1].update(changes)
 try:terminal_witness([4.,-2.,0.],known,altered)
 except AssertionError:checks['reject_'+name]=True
 else:checks['reject_'+name]=False
result=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,actual_saved_sources=len(proofs),sources_with_finite_terminal_witness=sum(p['admitted']for p in proofs),sources_without_witness=sum(not p['admitted']for p in proofs),proofs=proofs,navigation_ready=False,remaining='Need common route and execution contract, genuine planner/closed-loop validation; terminal witness alone is insufficient.')
for p in [R/'runs/v908_causal_progress_contract/TERMINAL_QUALIFICATION.json',R/'records/nav2_v908_20261109/TERMINAL_QUALIFICATION.json']:p.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k!='proofs'}));assert result['passed']
