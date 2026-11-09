"""Replay actual stalled zero-command entry; no vehicle models."""
import copy,gzip,json,sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v936_rpccr_corridor_search';sys.path.insert(0,str(C));from reference_loss import ReferenceLoss
rows=json.loads(gzip.decompress((O/'saved/COMMAND_TUBES.json.gz').read_bytes()));routes=json.loads((O/'saved/ROUTER_REQUESTS.json').read_text());machine=ReferenceLoss();route_index=0;trigger=None
for row in rows:
 p,s=row['packet'],row['source'];now=row['proof']['issued_at']
 while route_index<len(routes)and routes[route_index]['started_monotonic']+routes[route_index]['wall_s']<=now:
  route=routes[route_index];machine.route(route['started_monotonic']+route['wall_s'],route['passed']);route_index+=1
 machine.command(now,*row['wanted']);result=machine.observe(p,s,now)
 if result['triggered']:trigger=dict(result,packet=p,source=s,original_wanted=row['wanted']);break
checks=dict(actual_original_zero_stall_triggers=trigger is not None and trigger['original_wanted']==[0.,0.],trigger_uses_actual_body_and_causal_source=trigger is not None and trigger['body_native_tick']>=trigger['source_native_tick'])
assert trigger is not None
for label,change in [('fresh_valid_reference',lambda m,p,s,t:m.route(t,True)),('normal_progress',lambda m,p,s,t:m.command(t,.1,0.)),('no_actor',lambda m,p,s,t:s.update(support_bounds=None))]:
 m=ReferenceLoss();m.failures=[0,1,2];m.last_success=trigger['packet']['body_measured_at']-10;p=copy.deepcopy(trigger['packet']);s=copy.deepcopy(trigger['source']);t=trigger['packet']['body_measured_at'];m.poses=[(t-1.6,*p['body'][:2])];change(m,p,s,t);checks[label+'_does_not_trigger']=not m.observe(p,s,t)['triggered']
m=ReferenceLoss();p=copy.deepcopy(trigger['packet']);s=copy.deepcopy(trigger['source']);s['source_native_tick']=p['native_tick']+1
try:m.observe(p,s,p['body_measured_at'])
except AssertionError:checks['future_source_rejected']=True
else:checks['future_source_rejected']=False
p=copy.deepcopy(trigger['packet']);s=copy.deepcopy(trigger['source'])
try:ReferenceLoss().observe(p,s,p['body_measured_at']+.201)
except AssertionError:checks['stale_body_rejected']=True
else:checks['stale_body_rejected']=False
proof=dict(passed=all(checks.values()),checks=checks,first_actual_trigger=trigger,models=0,integrations=0,scope='Original V934 never-triggered zero-motion stall now enters explicit recovery state; no command is dispatched by this entry test.');(O/'ENTRY_QUALIFICATION.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items()if k!='first_actual_trigger'}));assert proof['passed']
