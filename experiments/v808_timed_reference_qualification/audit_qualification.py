"""Independent saved-box geometry and finite future coverage; no planner calls/models."""
import hashlib,json,pathlib,sys
from types import SimpleNamespace
import numpy as np
repo=pathlib.Path(__file__).resolve().parents[2];own=pathlib.Path(__file__).parent;sys.path.insert(0,str(own));from exact_footprint import pose_values
from union_belief import future_cells
root=repo/'runs/v808_timed_reference_qualification';read=lambda p:json.loads(p.read_text());rows=read(root/'RESULTS.json');protocol=read(repo/'runs/v807_reactive_single_task_continuation/main_slot01/paired/STATIC_PROTOCOL.json');b=np.array(protocol['footprint_bounds']);base=dict(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.));records=[];covered=0;error=0.
robotpad=.004*(1+np.hypot(.44,.375)*np.tan(.42722137342572125)/.6);actorpad=.12*.02
for r in rows:
 state=r['causal_state'];pl=np.array(state['position_lower']);pu=np.array(state['position_upper']);vl=np.array(state['velocity_lower']);vu=np.array(state['velocity_upper']);tt=np.arange(657)*.01
 lo=np.maximum(pl+tt[:,None]*vl-.02*tt[:,None]**2,pl-.12*tt[:,None])-1e-5;hi=np.minimum(pu+tt[:,None]*vu+.02*tt[:,None]**2,pu+.12*tt[:,None])+1e-5;cl,ch=future_cells(state['outer_state_cells'],tt);assert np.max(lo[:,None,:]-cl)<=1e-7 and np.max(ch-hi[:,None,:])<=1e-7;covered+=657
 checks=dict(input_source_sha=hashlib.sha256((repo/r['input_file']).read_bytes()).hexdigest()==r['input_sha256'],all657_union_cells_contained=True,current_rectangle_preserved=r['causal_world']['rectangles'][-1]==state['current_outer_rectangle'],no_future_union_static_rectangle=len(r['causal_world']['rectangles'])==len(protocol['known_rectangles'])+1,scope_explicit=r['metadata']['beyond_horizon_is_uncertified_guidance']and r['metadata']['hidden_world_geometry_used']is False)
 if r['path']is not None:
  z=np.load(root/r['saved_arrays']);path=z['path'];arrival=z['arrivals'];p=z['dense'];times=z['times'];field=SimpleNamespace(**base,rectangles=np.array(r['causal_world']['rectangles']),circles=np.array(r['causal_world']['circles']));vals=pose_values(field,p)
  # Independent time bounds and rectangle polygon query, per recorded sample.
  for i in np.flatnonzero(times<=6.56+1e-10):
   t=times[i];a=np.maximum(pl+t*vl-.02*t*t,pl-.12*t)-1e-5-actorpad;d=np.minimum(pu+t*vu+.02*t*t,pu+.12*t)+1e-5+actorpad
   box=SimpleNamespace(**dict(base,config=SimpleNamespace(lower=-1e6,upper=1e6)),rectangles=np.array([[*((a+d)/2),*((d-a)/2)]]),circles=np.empty((0,3)));dynamic=pose_values(box,p[i:i+1])[0]-.10-robotpad;vals[i]=min(vals[i],dynamic)
  err=float(np.max(abs(vals-z['values'])));error=max(error,err)
  checks.update(values_exact=err<=1e-10,sample_floor=vals.min()>=r['stats']['guard_m']-1e-8,actual_path_shape=len(path)==len(arrival)and path.shape[1]==4,forward_reverse_only=set(path[:,3])<={-1.,1.},timing_monotone=bool(np.all(np.diff(arrival)>0)),curvature=True,schedule_exact=True,beyond_horizon_not_claimed=int(np.sum(arrival>6.56))==r['stats']['uncertified_beyond_horizon_reference_nodes'])
  for j,(a,d)in enumerate(zip(path[:-1],path[1:])):
   gear=d[3];dy=(d[2]-a[2]+np.pi)%(2*np.pi)-np.pi;curv=dy/(gear*.04);checks['curvature']&=abs(curv)<=np.tan(.42722137342572125)/.6+1e-8
   expected=.2+(.4 if a[3]!=d[3]else 0.);checks['schedule_exact']&=abs(arrival[j+1]-arrival[j]-expected)<=1e-8
 records.append(dict(step=r['step'],checks={k:bool(v)for k,v in checks.items()},passed=bool(all(checks.values())),old_remaining=r['old_endpoint_goal_distance_m'],new_remaining=r.get('new_endpoint_goal_distance_m'),new_status=r['stats']['status']))
first=next((r for r in records if r['step']==303),None);mathpass=len(rows)==5 and all(r['passed']for r in records);improved=bool(first and first['new_status']=='GLOBAL_GOAL_PATH'and first['new_remaining']<=.28 and first['old_remaining']>2.)
result=dict(status='TIME_REFERENCE_QUALIFICATION_PASS'if mathpass and improved else'TIME_REFERENCE_QUALIFICATION_NOT_PASSED',all_math_and_scope_checks=mathpass,registered_fresh_detection303_goal_reference_improved=improved,records=records,finite_future_coverage_queries=covered,maximum_geometry_error=error,new_models=0,integrations=0,scope='Proposed geometric arrival clocks, no executed controls or actual dynamic arrival. Goal beyond horizon guidance explicitly uncertified.')
(root/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert mathpass
