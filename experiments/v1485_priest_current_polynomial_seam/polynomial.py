"""World rear-axle Bernstein proposal math, never a vehicle integration."""
import math

def finite_vector(values,n):
 assert isinstance(values,list)and len(values)==n and all(type(x)in(int,float)and math.isfinite(x)for x in values),'PRIEST_POLYNOMIAL_NONFINITE_OR_SHAPE'

def evaluate(coefficients,time_s,horizon_s):
 finite_vector(coefficients,11)
 assert type(time_s)in(int,float)and type(horizon_s)in(int,float)and math.isfinite(time_s)and math.isfinite(horizon_s)
 assert horizon_s==10. and 0<=time_s<=horizon_s,'PRIEST_FIXED_POLYNOMIAL_TIME'
 u=time_s/horizon_s;n=10
 def basis(values):
  m=len(values)-1
  return sum(math.comb(m,i)*u**i*(1-u)**(m-i)*v for i,v in enumerate(values))
 first=[n*(coefficients[i+1]-coefficients[i])/horizon_s for i in range(n)]
 second=[n*(n-1)*(coefficients[i+2]-2*coefficients[i+1]+coefficients[i])/horizon_s**2 for i in range(n-1)]
 result=[basis(coefficients),basis(first),basis(second)];assert all(math.isfinite(x)for x in result)
 return result

def sample(coefficients_x,coefficients_y,*,time_s,gear):
 assert type(gear)is int and gear in(-1,1)
 x,vx,ax=evaluate(coefficients_x,time_s,10.);y,vy,ay=evaluate(coefficients_y,time_s,10.)
 speed=math.hypot(vx,vy)
 if speed<=1e-12:
  return dict(time_s=time_s,position=[x,y],velocity=[vx,vy],acceleration=[ax,ay],gear=gear,tangent_heading_rad=None,nominal_yaw_rate_rad_s=None,nominal_curvature_m_inv=None,singular_zero_speed_tangent=True,actuator_or_collision_feasible=None,control_emitted=False)
 heading=math.atan2(gear*vy,gear*vx);yaw_rate=(vx*ay-vy*ax)/(speed*speed);curvature=yaw_rate/(gear*speed)
 assert math.isfinite(yaw_rate)and math.isfinite(curvature)
 return dict(time_s=time_s,position=[x,y],velocity=[vx,vy],acceleration=[ax,ay],gear=gear,tangent_heading_rad=heading,nominal_yaw_rate_rad_s=yaw_rate,nominal_curvature_m_inv=curvature,singular_zero_speed_tangent=False,actuator_or_collision_feasible=None,control_emitted=False)
