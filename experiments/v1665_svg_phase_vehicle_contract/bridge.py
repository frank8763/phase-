"""Measured Phase actuator/body data to author state; no plant or allocator calls.

This conversion retains the full packet as the independent response gate origin.
A five-state author bicycle approximation never replaces measured wheel/memory,
body lateral motion, or the original full-state predictor/retained-stop gates.
"""
import copy,hashlib,json,math
WHEELBASE=.6
HALF_TRACK=.27
CENTER_LIMIT=.42722137342572125

def number(value):
 assert type(value)in (int,float)and math.isfinite(value),'NONFINITE_OR_NONSCALAR'
 return float(value)

def digest(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def decode(packet,*,expected_native,expected_sim_time,expected_packet_sha256):
 assert digest(packet)==expected_packet_sha256,'FOREIGN_MEASURED_PACKET'
 assert type(expected_native)is int and expected_native>=0
 assert packet['native_tick']==packet['steering']['native_tick']==expected_native,'MIXED_NATIVE_MEASUREMENT'
 assert number(packet['sim_time'])==number(expected_sim_time),'CHANGED_MEASURED_CLOCK'
 assert len(packet['body'])==5 and len(packet['steering']['position'])==len(packet['steering']['velocity'])==2
 body=list(map(number,packet['body']));angles=list(map(number,packet['steering']['position']));rates=list(map(number,packet['steering']['velocity']))
 assert all(abs(x)<math.pi/2 for x in angles),'STEERING_INVERSE_DOMAIN'
 curvature=[]
 for angle,side in zip(angles,[1.,-1.]):
  t=math.tan(angle);denominator=WHEELBASE+side*HALF_TRACK*t
  assert denominator>0.,'STEERING_INVERSE_DENOMINATOR'
  curvature.append(t/denominator)
 virtual=math.atan(WHEELBASE*sum(curvature)/2)
 # Keep original estimator: mean inferred curvature, never average wheel angles.
 memory=packet['controller_memory'];assert len(memory['last_ctrl'])==4
 list(map(number,memory['last_ctrl']));number(memory['integral'])
 for key in ['body_measured_at','sent_at']:number(packet[key])
 number(packet['steering']['measured_at']);number(packet['body_lateral'])
 assert packet['body_measured_at']<=packet['sent_at']and packet['steering']['measured_at']<=packet['sent_at'],'MEASURED_TIME_ORDER'
 return dict(author_state=[body[0],body[1],body[2],body[3],virtual],origin_packet=copy.deepcopy(packet),origin_packet_sha256=expected_packet_sha256,origin_native=expected_native,origin_sim_time=expected_sim_time,measured_wheel_curvatures=curvature,measured_wheel_curvature_disagreement=abs(curvature[0]-curvature[1]),author_velocity_convention='measured signed body longitudinal velocity; bicycle approximate, lateral motion remains in original response gate',unrepresented_author_states=dict(body_lateral=packet['body_lateral'],body_yaw_rate=body[4],wheel_velocities=rates,controller_memory=copy.deepcopy(memory),steering_motion_active=packet['steering_motion_active'],coupled_episode=packet['coupled_episode']),packet_timestamps_preserved=True,physical_authorized=False)

def request(raw_steering,*,longitudinal_speed,declared_gear,origin,expected_origin_sha256):
 delta=number(raw_steering);speed=number(longitudinal_speed)
 assert origin['origin_packet_sha256']==expected_origin_sha256==digest(origin['origin_packet']),'OUTPUT_ORIGIN_CHANGED'
 assert abs(delta)<=CENTER_LIMIT,'RAW_SVG_STEERING_OUTSIDE_PHASE_CAP'
 assert declared_gear in (-1,0,1)and type(declared_gear)is int,'UNDECLARED_GEAR'
 assert abs(speed)<=.1,'DECLARED_SPEED_OUTSIDE_COMMON_CAP'
 assert (speed==0. and declared_gear==0)or(speed>0. and declared_gear==1)or(speed<0. and declared_gear==-1),'SPEED_GEAR_MISMATCH'
 assert speed==0. or abs(speed)>=.005,'SPEED_IN_BRAKING_DEADBAND'
 if declared_gear==0:assert delta==0.,'NO_IMPLICIT_PARKED_STEERING_MODE'
 yaw=speed*math.tan(delta)/WHEELBASE
 return dict(raw_author_steering=delta,external_longitudinal_speed=speed,external_gear=declared_gear,body_request=[speed,yaw,False],origin_packet_sha256=expected_origin_sha256,origin_native=origin['origin_native'],origin_sim_time=origin['origin_sim_time'],output_not_clipped_or_smoothed=True,original_Allocator_required=True,original_current_fullstate_shadow_and_complete_stop_required=True,physical_authorized=False)

def physical_permission(*args,**kwargs):
 raise AssertionError('SVG_PHASE_FULLSTATE_CAUSAL_MAP_REFERENCE_SHADOW_RUNTIME_NOT_QUALIFIED')
