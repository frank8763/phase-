"""Explicit body-centre/rear-axle geometry and pipe schema; no engine imports."""
import copy,math
from context import R,load,digest

def finite(values):
 assert all(type(x)in(int,float)and math.isfinite(x)for x in values),'TEB_NONFINITE_SCHEMA'

def rear(pose,offset=.3):
 finite(pose);x,y,a=pose
 return [x-offset*math.cos(a),y-offset*math.sin(a),a]

def centre(pose,offset=.3):
 finite(pose);x,y,a=pose
 return [x+offset*math.cos(a),y+offset*math.sin(a),a]

def observation_receipt(origin_receipt,scan):
 shared=load('v1739_shared_measurement_contract',R/'experiments/v1694_shared_observation_closure/contract.py')
 p=origin_receipt['packet'];s=shared.scan_only(scan,p['native_tick'],p['sim_time'])
 r=dict(schema='PHASE_CURRENT_MEASUREMENT_V1',packet_acquisitions=1,packet=copy.deepcopy(p),packet_sha256=digest(p),before_monotonic=origin_receipt['acquisition_before_monotonic'],after_monotonic=origin_receipt['acquisition_after_monotonic'],scan=s)
 shared.verify_receipt(r,p['native_tick']);return r

def scan_points(scan):
 points=[]
 for i,r in enumerate(scan['ranges']):
  if r<2.999:
   a=scan['yaw']+math.tau*i/32
   points.append([scan['xy'][0]+r*math.cos(a),scan['xy'][1]+r*math.sin(a)])
 return points

def encode(receipt,goal,static_points,config):
 shared=load('v1739_shared_causal_receipt',R/'experiments/v1694_shared_observation_closure/contract.py')
 p=shared.verify_receipt(receipt,receipt['packet']['native_tick']);assert len(p['body'])==5
 finite(p['body']+[p['body_lateral']]);finite(goal);assert len(goal)==3
 assert config['wheelbase']==.6 and config['rear_offset']==.3
 xyz=rear(p['body'][:3],config['rear_offset']);g=rear(goal,config['rear_offset'])
 points=copy.deepcopy(static_points)+scan_points(receipt['scan']);assert 0<len(points)<=4096
 for point in points:assert len(point)==2;finite(point)
 q=dict(x=xyz[0],y=xyz[1],yaw=xyz[2],goal_x=g[0],goal_y=g[1],goal_yaw=g[2],vx=p['body'][3],vy=p['body_lateral']-.3*p['body'][4],omega=p['body'][4])
 return dict(schema='PHASE_TEB_REAR_AXLE_QUERY_V1',config=copy.deepcopy(config),query=q,obstacles=[dict(x=x,y=y,vx=0.,vy=0.,dynamic=0)for x,y in points],origin_packet_sha256=digest(p),receipt_sha256=digest(receipt),source_native=p['native_tick'],source_sim_time=p['sim_time'],goal_body_centre=list(goal),historical_controls_supplied=False,actor_truth_supplied=False,point_snapshot_not_future_certificate=True)

def command(raw,config):
 assert raw['status']==0,'TEB_ORIGINAL_OPTIMIZER_REFUSAL'
 raw_twist=[raw['vx'],raw['vy'],raw['omega']];finite(raw_twist)
 velocity=load('v1739_author_command_saturation_port',R/'experiments/v1739_teb_current_cycle/velocity.py')
 v,y,w=velocity.saturate(*raw_twist,config)
 assert abs(y)<=1e-8,'TEB_LATERAL_COMMAND_NOT_SUPPORTED'
 assert abs(v)<=config['forward']and abs(w)<=config['omega'],'TEB_RAW_TWIST_OUTSIDE_COMMON_CAP'
 if v==0.:
  assert w==0.,'TEB_IN_PLACE_ROTATION_REFUSED'
  return dict(body_request=[0.,0.,False],gear=0,virtual_steering=0.,raw_twist=raw_twist,original_saturation_only=True)
 assert abs(v)>=config['minimum_nonzero_speed'],'TEB_RAW_SPEED_IN_BRAKING_DEADBAND'
 assert abs(w/v)<=config['maximum_curvature'],'TEB_RAW_CURVATURE_OUTSIDE_COMMON_CAP'
 return dict(body_request=[v,w,False],gear=1 if v>0 else -1,virtual_steering=math.atan(.6*w/v),raw_twist=raw_twist,original_saturation_only=True)

def trajectory(raw,config):
 values=raw['trajectory'];assert 2<=len(values)<=500,'TEB_TIMED_TRAJECTORY_SHAPE'
 last=-1.;body=[]
 for row in values:
  assert len(row)==7;finite(row);assert row[3]>=last and row[3]>=0.,'TEB_TIMED_TRAJECTORY_TIME'
  body.append(centre(row[:3],config['rear_offset'])+row[3:]);last=row[3]
 assert last>0.,'TEB_ZERO_DURATION_TRAJECTORY'
 return body
