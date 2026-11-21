"""Map/source-bound proposal arrays; these are not safety certificates."""
import bisect
import copy
import hashlib
import json
import math

VEHICLE_REAR_RADIUS=math.hypot(.74,.375)

def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def finite(x):return type(x)in(int,float)and math.isfinite(x)

def path_arrays(poses):
 assert isinstance(poses,list)and len(poses)>=2
 for p in poses:assert len(p)==3 and all(finite(v)for v in p)
 points=[]
 for x,y,_ in poses:
  if not points or math.dist(points[-1],[x,y])>1e-12:points.append([x,y])
 assert len(points)>=2,'PRIEST_ZERO_LENGTH_SEGMENT'
 arc=[0.]
 for a,b in zip(points,points[1:]):arc.append(arc[-1]+math.dist(a,b))
 distances=[arc[-1]*i/999 for i in range(1000)];x=[];y=[]
 for s in distances:
  k=min(len(points)-2,max(0,bisect.bisect_right(arc,s)-1));u=(s-arc[k])/(arc[k+1]-arc[k])
  x.append(points[k][0]+u*(points[k+1][0]-points[k][0]));y.append(points[k][1]+u*(points[k+1][1]-points[k][1]))
 dx=[b-a for a,b in zip(x,x[1:])];dy=[b-a for a,b in zip(y,y[1:])]
 assert all(math.hypot(a,b)>1e-12 for a,b in zip(dx,dy)),'PRIEST_RESAMPLED_DEGENERATE_TANGENT'
 # Explicit terminal extension of the final measured route-edge derivative.
 dx.append(dx[-1]);dy.append(dy[-1])
 return dict(x_waypoint=x,y_waypoint=y,arc_vec=distances,x_diff=dx,y_diff=dy,terminal_derivative='REPEAT_FINAL_ROUTE_EDGE_NOT_ZERO_OR_EXTRA_PATH')

def build(current,*,prepared,boundary_state,port_identity):
 value=copy.deepcopy(current);identity=value.pop('input_sha256');assert digest(value)==identity
 assert current['core_identity_sha256']==prepared.hot_identity()and current['source_manifest_sha256']==prepared.source_manifest_sha256
 assert current['public_map_sha256']==prepared.public_map_sha256==digest(prepared.public_map)
 assert current['causal_snapshot_sha256']==digest(current['causal_snapshot'])
 assert boundary_state['source']==current['author_initial_boundary_hint']and not boundary_state['instantaneous_actual_acceleration_is_known']
 initial=boundary_state['state'];assert len(initial)==6 and all(finite(v)for v in initial)
 assert initial[:4]==[*current['rear_pose_world'][:2],*current['rear_velocity_world']]
 assert initial[4:]==current['author_initial_boundary_hint']['acceleration_hint_world']
 grid=prepared.public_map;resolution=grid['resolution'];assert resolution==.05 and grid['origin'][2]==0.
 assert len(grid['data'])==grid['height']*grid['width']
 cells=[]
 for i,v in enumerate(grid['data']):
  assert v in(0,100),'PRIEST_PUBLIC_GRID_UNDECLARED_CELL'
  if v==100:
   x=grid['origin'][0]+(i%grid['width']+.5)*resolution;y=grid['origin'][1]+(i//grid['width']+.5)*resolution
   cells.append((math.hypot(x-initial[0],y-initial[1]),i,x,y))
 assert len(cells)>=50,'PRIEST_NO_DUMMY_STATIC_OBSTACLES'
 cells.sort();selected=cells[:50];radius=VEHICLE_REAR_RADIUS+.22+resolution/math.sqrt(2)
 forecast=current['causal_forecast'];snapshot=current['causal_snapshot']
 if snapshot['periodic']is None:
  assert forecast is None and current['observation_stage']=='NO_DYNAMIC_RETURN_YET_NO_MEASURED_FUTURE';dynamic=[];dynamic_radius=VEHICLE_REAR_RADIUS+.22
 else:
  exact=prepared.field.all_future(snapshot,current_native=current['fixed_origin_native'],current_sim_time=current['fixed_origin_sim_time'])
  assert exact==forecast,'PRIEST_FORECAST_NOT_COMPLETE_CURRENT_COEFFICIENT_DISK'
  dynamic=[[float(forecast['center'][0]),float(forecast['center'][1])]];dynamic_radius=float(forecast['radius_m'])+VEHICLE_REAR_RADIUS+.22
 kwargs=dict(a_obs_1=radius,b_obs_1=radius,a_obs_2=dynamic_radius,b_obs_2=dynamic_radius,v_max=.1,v_min=0.,a_max=.1,num_obs_1=50,num_obs_2=len(dynamic),t_fin=10.,num=100,num_batch=110,maxiter=1,maxiter_cem=12,weight_smoothness=1.,weight_track=.001,way_point_shape=1000,v_des=.1)
 path=path_arrays(current['next_segment']['poses']);static=[[x,y]for _,_,x,y in selected]
 request=dict(kind='PHASE_ENGINEERING_PRIEST_OPTIMIZER_REQUEST',schema=1,run_id=current['run_id'],input_sha256=identity,core_identity_sha256=current['core_identity_sha256'],port_identity=copy.deepcopy(port_identity),origin_native=current['fixed_origin_native'],origin_sim_time=current['fixed_origin_sim_time'],constructor_kwargs=kwargs,initial_state=copy.deepcopy(initial),boundary_role='APPROXIMATION_NOT_INSTANTANEOUS_MEASUREMENT',path=path,static_points_world=static,static_grid_indices=[i for _,i,_,_ in selected],dynamic_points_world=dynamic,causal_snapshot_sha256=current['causal_snapshot_sha256'],public_map_sha256=current['public_map_sha256'],forecast_role='CURRENT_FULL_PERIOD_CAUSAL_DISK_PROPOSAL_ONLY',numpy_seed=0,jax_key=0,gear=current['next_segment']['gear'],goal_world=path['x_waypoint'][-1:]+path['y_waypoint'][-1:],optimizer_qualified=False,obstacle_subset_is_not_complete_map_safety=True,complete_current_response_required=True,physical_admission=False)
 return dict(request,request_sha256=digest(request))
