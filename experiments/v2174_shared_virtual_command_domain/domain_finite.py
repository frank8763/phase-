"""Finite trace envelope around the unchanged initial domain projection."""
import math
from domain import project as original_project

def project(packet):
 result=original_project(packet)
 # Finite input factors can still overflow a raw diagnostic product.
 for key in ['raw_bicycle_velocity_m_s','raw_bicycle_curvature_m_inv','raw_bicycle_yaw_rate_rad_s',
             'projected_curvature_m_inv','speed_delta_m_s','curvature_delta_m_inv']:
  if not math.isfinite(result[key]):raise ValueError('NONFINITE_DERIVED_TRACE:'+key)
 return result
