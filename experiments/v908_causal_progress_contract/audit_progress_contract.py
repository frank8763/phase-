"""Quantify declared supervisor/reference mismatch on real saved navigation paths.
Not future ground truth or a counterfactual vehicle rollout.
"""
import json,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path.insert(0,str(R/'experiments/v907_recovery_corridor_memory'))
from refuge_logic import wait_ok
root=R/'runs/v858_nav2_verified/v907/main_we';rows=json.loads((root/'ROUTER_REQUESTS.json').read_text());plans=json.loads((root/'PLANS.json').read_text());e=json.loads((root/'REFUGE_SUPERVISION.json').read_text())['events'];results=[]
assert len(rows)==len(plans)==100
for i,(r,p)in enumerate(zip(rows,plans)):
 assert r['passed'] and abs(p['at']-(r['started_monotonic']+r['wall_s']))<.08,'PLAN_ASSOCIATION_TIME'
 assert np.linalg.norm(np.asarray(p['path'][0][:2])-r['original_start'][:2])<.1,'PLAN_ASSOCIATION_START'
 support=r['causal_forecast_source']['center_support_bounds']
 if r['navigation_role']!='ORIGINAL' or support is None:continue
 age=r['causal_forecast_source']['source_age_s'];valid=[wait_ok(pt,support,age,6.)for pt in p['path']]
 results.append(dict(index=i,source_native_tick=r['causal_forecast_source']['source_native_tick'],original_start=r['original_start'],route_end=p['path'][-1],waypoints=len(valid),instantaneous_hold6_rejected_waypoints=sum(not x for x in valid),selected_endpoint_hold6=valid[-1]))
summary=dict(models=0,integrations=0,matched_original_tracked_routes=len(results),selected_endpoints_without_current_hold6=sum(not x['selected_endpoint_hold6']for x in results),rows=results,
 recovery_request_positions=[x['body'][:2]for x in e if x['event']=='REFUGE_REQUEST'],
 scope='Actual ordered published paths matched to successful request times/start poses. Applies current saved causal support at all points with no arrival-time expansion: optimistic retrospective contract comparison, not future trajectory feasibility or proof of impossibility. Confirms planner accepts endpoints the supervisor currently rejects.')
for p in [R/'runs/v908_causal_progress_contract/PROGRESS_CONTRACT_DIAGNOSIS.json',R/'records/nav2_v908_20261109/PROGRESS_CONTRACT_DIAGNOSIS.json']:p.write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items()if k!='rows'}))
