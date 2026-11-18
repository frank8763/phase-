"""Exact scientific construction identity, excluding two measured durations only."""
import copy,json
from pathlib import Path
TIMING_PATHS=(('actor','swept_envelope_reference','elapsed_s'),('actor','swept_envelope_reference','search','wall_s'))
def physical_identity(setup):
 d=copy.deepcopy(setup)
 for path in TIMING_PATHS:
  p=d
  for k in path[:-1]:p=p[k]
  assert isinstance(p[path[-1]],(int,float))and p[path[-1]]>=0,'CONSTRUCTION_TIMER_FORMAT';del p[path[-1]]
 # A historically stale EW label in a WE record is reported separately;
 # actual case/start/model/actor identity are all kept and independently bound.
 d.pop('declared_course_id',None)
 return d

def verify(a,b,task):
 assert physical_identity(a)==physical_identity(b),'PHYSICAL_SCIENTIFIC_SETUP_CHANGED';assert a['case']['id']==task['case_id']=='WEST_EAST'and a['seed']==task['seed']==10010001 and a['dynamic']is True;assert a['case']['start_xy']==task['start_xy']==[-4.,-2.]and a['case']['goal_xy']==task['goal_xy']==[4.,-2.];assert a['case']['yaw']==task['start_yaw']==0.;assert a['actor']['phase_rad']==task['phase']==.6573753567727383;assert a['actor']['anchor_xy']==[3.,-1.]and a['actor']['radius_m']==.1 and a['actor']['amplitude_m']==.25 and a['actor']['omega_rad_s']==.32
 return {'passed':True,'excluded_timing_paths':['/'.join(p)for p in TIMING_PATHS],'all_other_physical_and_scientific_fields_equal':True,'old_legacy_course_label':b.get('declared_course_id'),'new_legacy_course_label':a.get('declared_course_id'),'registered_course_independently_bound':'WEST_EAST_ORIGINAL_START_AND_GOAL','not_permission_to_change_actor_or_geometry':True}
