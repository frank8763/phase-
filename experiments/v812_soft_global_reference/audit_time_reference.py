"""Independent saved temporal reference geometry and clock audit; no models."""
import argparse,json,pathlib
import numpy as np
from independent_time_reference import field,values
from exact_footprint import pose_values
ap=argparse.ArgumentParser();ap.add_argument('pair',type=pathlib.Path);a=ap.parse_args();c=a.pair/'geometry_memory';read=lambda p:json.loads(p.read_text());p=read(a.pair/'STATIC_PROTOCOL.json');states={x['step']:x for x in map(json.loads,(c/'motion_estimate.jsonl').read_text().splitlines())};records=[]
for file in sorted(c.glob('planning_*.json')):
 r=read(file);state=states[r['step']]
 if state['center']is None:continue
 f=field(p,state);w=r['causal_route_input'];md=r['route_projection_metadata'];checks=dict(current_actor_only_world=w['rectangles']==[*p['known_rectangles'],state['current_outer_rectangle']]and w['circles']==p['known_circles'],source_causal=md['hidden_world_geometry_used']is False and state['hidden_world_geometry_used']is False,scope=md['beyond_horizon_is_uncertified_guidance']and md['dynamic_future_is_not_static_union'],constant_parameters=md['reference_speed_m_s']==.2 and md['gear_transition_reference_wait_s']==.4 and md['horizon_s']==6.56)
 if r['path']is not None:
  path=np.asarray(r['path']);t=np.asarray(r['stats']['reference_arrival_times_s']);queries=[];times=[];curvature=True;clock=True
  for aa,bb,ta,tb in zip(path[:-1],path[1:],t[:-1],t[1:]):
   dy=(bb[2]-aa[2]+np.pi)%(2*np.pi)-np.pi;wait=.4 if aa[3]!=bb[3]else 0.;clock&=abs(tb-ta-.2-wait)<=1e-8;curvature&=abs(dy/.04)<=np.tan(.42722137342572125)/.6+1e-8
   if wait:
    for dt in np.linspace(0,wait,21):queries.append(aa[:3]);times.append(ta+dt)
   for u in np.arange(1,6)/5.:queries.append([*(aa[:2]+u*(bb[:2]-aa[:2])),aa[2]+u*dy]);times.append(ta+wait+u*.2)
  v=values(f,state,np.asarray(queries),np.asarray(times));minimum=float(v.min());checks.update(clock=clock,curvature=curvature,timing_shape=len(t)==len(path)and t[0]==0 and np.all(np.diff(t)>0),all_dense_temporal_reference_floor=minimum>=r['stats']['guard_m']-1e-8 and abs(minimum-r['stats']['minimum_clearance_m'])<=1e-8,beyond_horizon_flag=int(np.sum(t>6.56))==r['stats']['uncertified_beyond_horizon_reference_nodes'],current_occupancy_entire_path=float(pose_values(f,path[:,:3]).min())>=r['stats']['guard_m']-1e-8)
 else:minimum=None
 records.append(dict(step=r['step'],passed=all(checks.values()),checks={k:bool(v)for k,v in checks.items()},minimum=minimum,reference_status=r['stats']['status']))
out=dict(status='TIME_REFERENCE_SAVED_GEOMETRY_PASS'if all(x['passed']for x in records)else'FAIL',records=records,tracked_plan_count=len(records),new_models=0,integrations=0,scope='Proposed arrival clock/current occupancy only, finite forecast horizon; no execution or whole-route dynamic proof.')
(a.pair/'TIME_REFERENCE_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'tracked_plans':len(records)}));assert all(x['passed']for x in records)

