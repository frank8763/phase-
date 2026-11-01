"""Independent evaluator; loads geometry, integrates no physics."""
import json,sys,os,hashlib
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(os.environ['PHASE_REPO'])/'experiments/v686_dynamic_open_curriculum'))
from exact_footprint import build
root=Path(sys.argv[1]);cell=root/'geometry_memory'
read=lambda p:json.loads(p.read_text())
states=[json.loads(s)for s in(cell/'motion_estimate.jsonl').read_text().splitlines()]
config=read(root/'DYNAMIC_PROTOCOL.json');r=read(cell/'result.json');coverage=[json.loads(s)for s in(cell/'forecast_coverage.jsonl').read_text().splitlines()]
truth=np.asarray([np.asarray(config['anchor_xy'])+config['amplitude_m']*np.sin(s['time']*config['omega_rad_s']+config['phase_rad'])*np.asarray(config['axis_xy'])for s in states])
seen=[(i,s)for i,s in enumerate(states)if s['observed_this_frame']]
motion_velocity=any(s['center']is not None and (np.any(np.asarray(s['velocity_lower'])>0)or np.any(np.asarray(s['velocity_upper'])<0))for s in states)
motion_positions=False
valid=[s for s in states if s['center']is not None]
for i,s in enumerate(valid):
 if any(np.any(np.asarray(t['position_upper'])<s['position_lower'])or np.any(np.asarray(s['position_upper'])<t['position_lower'])for t in valid[:i]):motion_positions=True;break
from types import SimpleNamespace,MethodType
from exact_footprint import pose_values
protocol=read(root/'STATIC_PROTOCOL.json');bounds=np.asarray(protocol['footprint_bounds'])
def field_for(world,step):
 f=SimpleNamespace(half=(bounds[2:]-bounds[:2])/2,center_local=(bounds[2:]+bounds[:2])/2,rectangles=np.asarray(world['rectangles']).reshape(-1,4),circles=np.asarray(world['circles']).reshape(-1,3),sensor_points=np.asarray(world['sensor_points']).reshape(-1,2),sensor_extra=max(0.,world['sensor_radius']-world['robot_radius']),config=SimpleNamespace(lower=-5.,upper=5.))
 f.pose_values=MethodType(pose_values,f)
 from motion_tracker import install_time_gate
 install_time_gate(f,states[step],'predictive',protocol['known_circles'],protocol['known_rectangles'])
 return f
prior=read(root/'KNOWN_PRIOR_REFERENCE.json');priorpath=np.asarray(prior['path']);plans=[]
for p in sorted(cell.glob('planning_*.json')):
 x=read(p);path=x['path'];step=x['step'];world=x['causal_input']
 dense=[]
 if path is not None:
  pp=np.asarray(path)
  for a,b in zip(pp[:-1],pp[1:]):
   dy=(b[2]-a[2]+np.pi)%(2*np.pi)-np.pi
   n=max(1,int(np.ceil(np.linalg.norm(b[:2]-a[:2])/.01)),int(np.ceil(abs(dy)/.01)))
   for k in range(n):dense.append([*(a[:2]+(k+.5)/n*(b[:2]-a[:2])),a[2]+(k+.5)/n*dy])
  dense.extend(pp[:,:3].tolist())
 dense_min=None if not dense else float(np.min(field_for(world,step).pose_values(dense)))
 plans.append({'step':step,'status':x['stats']['status'],'path_points':0 if path is None else len(path),'max_lateral_detour_m':None if path is None else float(np.max(abs(np.asarray(path)[:,1]+2.))),'dense_current_belief_clearance_m':dense_min,'causal_actor_present':step<len(states)and states[step]['center']is not None,'direct_reference_intersects_current_belief':False})
 if step<len(states)and states[step]['center']is not None:
  s=states[step];lo=np.asarray(s['position_lower'])-.1;hi=np.asarray(s['position_upper'])+.1
  # Straight baseline aligned with x: exact rectangle gap along y, and longitudinal overlap.
  plans[-1]['direct_reference_intersects_current_belief']=bool(lo[1]<-2.+.375+.155 and hi[1]>-2.-.375-.155 and lo[0]<1.+.44 and hi[0]>-3.-.44)
out={'task':'OPEN_SINGLE_CROSSING_01','new_scene_not_old_confirmation':True,'detected_frames':len(seen),'decision_frames':len(states),'first_detected_step':None if not seen else seen[0][0],'certified_unknown_ray_count':sum(s['certified_unknown_rays']for s in states),'position_center_max_error_m':max((float(np.linalg.norm(np.asarray(s['center'])-truth[i]))for i,s in enumerate(states)if s['center']is not None),default=None),'finite329_coverage_pass':bool(coverage)and all(x['passed']and x['checked_future_samples']==329 for x in coverage),'motion_identified_by_velocity_interval':bool(motion_velocity),'motion_identified_by_disjoint_position_intervals':bool(motion_positions),'detection_evidence_pass':len(seen)>=5 and all(x['passed']for x in coverage),'planning_records':plans,'global_detour_proposed':any(x['status']=='GLOBAL_GOAL_PATH'and x['dense_current_belief_clearance_m']>=.155-1e-8 and x['causal_actor_present']and x['max_lateral_detour_m']>=.2 and x['direct_reference_intersects_current_belief']for x in plans),'strict_arrival':r['strict_safe_arrival'],'goal_distance_m':r['goal_distance_m'],'outcome':r['outcome'],'public_steps':r['public_steps'],'verification_integrations':0,'training_updates':0,'scope':'one new easy development task; dense route geometry checked separately from time admission; not learned dynamics or stability acceptance'}
(root/'LAYER_METRICS_V2.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
