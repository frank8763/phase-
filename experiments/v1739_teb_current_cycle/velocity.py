"""Explicit Python port of upstream ROS command saturation, no extra rescue.

teb_local_planner_ros.cpp::saturateVelocity, original default
use_proportional_saturation=false. The original HCP output is retained before
this production command operation. This is not a claim to execute the ROS plugin.
"""
import math
def saturate(vx,vy,omega,config):
 assert config['use_proportional_saturation']is False
 assert all(math.isfinite(x)for x in [vx,vy,omega])
 ratio_x=ratio_y=ratio_omega=1.
 if vx>config['forward']:ratio_x=config['forward']/vx
 if abs(vy)>config['max_vel_y']:ratio_y=abs(config['max_vel_y']/vy)
 if abs(omega)>config['omega']:ratio_omega=abs(config['omega']/omega)
 assert config['backward']>0
 if vx < -config['backward']:ratio_x=-config['backward']/vx
 vx*=ratio_x;vy*=ratio_y;omega*=ratio_omega
 vel_linear=math.hypot(vx,vy)
 if vel_linear>config['max_vel_trans']:
  ratio=config['max_vel_trans']/vel_linear;vx*=ratio;vy*=ratio
 return vx,vy,omega
