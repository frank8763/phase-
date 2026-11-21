"""Backward actual-velocity secant is a planner hint, never acceleration truth."""
import copy
import hashlib
import json
import math

def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def finite(v):return type(v)in(int,float)and math.isfinite(v)

def rear_kinematics(state):
 assert set(state)=={'time','qpos','qvel','ctrl','mocap_pos','mocap_quat'}and finite(state['time'])
 q=state['qpos'];v=state['qvel'];assert len(q)>=7 and len(v)>=6 and all(finite(x)for x in [*q,*v])
 yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
 return dict(position=[q[0]-.3*math.cos(yaw),q[1]-.3*math.sin(yaw)],velocity=[v[0]+.3*math.sin(yaw)*v[5],v[1]-.3*math.cos(yaw)*v[5]],yaw=yaw)

def initial_hint(current_fullstate,previous_fullstate,*,native_tick):
 assert type(native_tick)is int and native_tick>=0 and abs(current_fullstate['time']-.01*native_tick)<=1e-8
 now=rear_kinematics(current_fullstate);current_sha=digest(current_fullstate)
 if previous_fullstate is None:
  if native_tick==0 and max(abs(x)for x in current_fullstate['qvel'])<=1e-10 and max(abs(x)for x in current_fullstate['ctrl'])<=1e-10:
   return dict(kind='CANONICAL_REST_DECLARED_ZERO_POLYNOMIAL_ACCELERATION_TARGET',origin_native=0,origin_fullstate_sha256=current_sha,acceleration_hint_world=[0.,0.],measured_instantaneous_acceleration=False,instantaneous_error_bound=None,source_qualified=False,planned_derivatives_used=False,zero_substitution_used=True,zero_role='EXPLICIT_PLANNER_BOUNDARY_TARGET_NOT_MEASUREMENT')
  return dict(kind='UNAVAILABLE_NO_BACKWARD_ACTUAL_SAMPLE',origin_native=native_tick,origin_fullstate_sha256=current_sha,acceleration_hint_world=None,measured_instantaneous_acceleration=False,instantaneous_error_bound=None,source_qualified=False,planned_derivatives_used=False,zero_substitution_used=False)
 assert native_tick>=1 and abs(previous_fullstate['time']-.01*(native_tick-1))<=1e-8
 before=rear_kinematics(previous_fullstate);dt=current_fullstate['time']-previous_fullstate['time'];assert abs(dt-.01)<=1e-8 and dt>0
 acceleration=[(a-b)/dt for a,b in zip(now['velocity'],before['velocity'])];assert all(finite(x)for x in acceleration)
 return dict(kind='CAUSAL_BACKWARD_ACTUAL_REAR_VELOCITY_SECANT_PLANNER_HINT',origin_native=native_tick,previous_native=native_tick-1,origin_fullstate_sha256=current_sha,previous_fullstate_sha256=digest(previous_fullstate),interval_s=dt,previous_velocity_world=before['velocity'],current_velocity_world=now['velocity'],acceleration_hint_world=acceleration,measured_instantaneous_acceleration=False,instantaneous_error_bound=None,source_qualified=False,planned_derivatives_used=False,zero_substitution_used=False)

def from_recorded_owner(native,current_fullstate):
 n=native.vehicle.count;assert n==native.applied and not native.in_step
 if n<2:return initial_hint(current_fullstate,None,native_tick=n)
 row=native.vehicle.rows[-2]
 def values(x):return x.tolist()if hasattr(x,'tolist')else copy.deepcopy(x)
 previous={k:values(row[k])for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']};previous['time']=float(row['time'])
 return initial_hint(current_fullstate,previous,native_tick=n)

def boundary_state(current):
 clean=dict(current);identity=clean.pop('input_sha256');assert digest(clean)==identity
 hint=current['author_initial_boundary_hint'];assert hint['origin_native']==current['fixed_origin_native']and hint['origin_fullstate_sha256']==current['fullstate_sha256']
 assert hint['acceleration_hint_world']is not None,'PRIEST_NO_CAUSAL_ACCELERATION_HINT_NO_COLD_START_FABRICATION'
 assert hint['planned_derivatives_used']is False and hint['measured_instantaneous_acceleration']is False
 if hint['kind']=='CANONICAL_REST_DECLARED_ZERO_POLYNOMIAL_ACCELERATION_TARGET':
  assert hint['origin_native']==0 and hint['zero_substitution_used']is True and hint['zero_role']=='EXPLICIT_PLANNER_BOUNDARY_TARGET_NOT_MEASUREMENT'
 else:assert hint['kind']=='CAUSAL_BACKWARD_ACTUAL_REAR_VELOCITY_SECANT_PLANNER_HINT'and hint['zero_substitution_used']is False
 return dict(state=[*current['rear_pose_world'][:2],*current['rear_velocity_world'],*hint['acceleration_hint_world']],source=copy.deepcopy(hint),role='POLYNOMIAL_BOUNDARY_APPROXIMATION_ONLY',instantaneous_actual_acceleration_is_known=False,source_or_error_qualification_passed=False,physical_admission=False)
