"""Declared engineering projection, no safety/physical authority."""
import math
SPEED=.1
CURVATURE=1/1.32
DEADBAND=.005
FIELDS={'virtual_steer_rad','virtual_wheel_rad_s','wheel_radius_m','wheelbase_m'}

def finite(x):
 if type(x)not in(int,float)or not math.isfinite(x):raise ValueError('NONFINITE_OR_NONNUMERIC')
 return float(x)

def project(packet):
 if type(packet)is not dict or set(packet)!=FIELDS:raise ValueError('VIRTUAL_COMMAND_SCHEMA')
 steer,wheel,radius,base=[finite(packet[k])for k in ['virtual_steer_rad','virtual_wheel_rad_s','wheel_radius_m','wheelbase_m']]
 if radius<=0 or base<=0:raise ValueError('NONPOSITIVE_GEOMETRY')
 if abs(steer)>=math.pi/2:raise ValueError('STEER_SINGULARITY_OR_WRONG_UNITS')
 raw_v=wheel*radius;k=math.tan(steer)/base
 if not math.isfinite(raw_v)or not math.isfinite(k):raise ValueError('NONFINITE_DERIVED_COMMAND')
 v=max(-SPEED,min(SPEED,raw_v));limited_k=max(-CURVATURE,min(CURVATURE,k));deadband=abs(v)<DEADBAND
 if deadband:v=0.
 w=v*limited_k
 return {'request':[v,w,False],'raw_virtual':dict(packet),'raw_bicycle_velocity_m_s':raw_v,
         'raw_bicycle_curvature_m_inv':k,'raw_bicycle_yaw_rate_rad_s':raw_v*k,
         'speed_saturated':abs(raw_v)>SPEED,'curvature_saturated':abs(k)>CURVATURE,
         'deadband_applied':deadband,'projected_curvature_m_inv':limited_k,
         'speed_delta_m_s':v-raw_v,'curvature_delta_m_inv':limited_k-k,
         'physical_authority':False,'identity':'DECLARED_COMMON_COMMAND_DOMAIN_PROJECTION',
         'original_native_motor_differential_gain_and_state_correction_not_reproduced':True}
