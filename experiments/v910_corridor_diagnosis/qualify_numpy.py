"""Retrospective declared-prior qualification. No native models or navigation."""
import gzip,importlib.abc,json,math,sys,time
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','torch','physical','vehicle','factory','rclpy'}:raise AssertionError(name)
sys.meta_path.insert(0,NoModel())
from periodic_numpy import PeriodicSupport,OMEGA,EPS
R=Path(__file__).resolve().parents[2];O=R/'runs/v910_corridor_diagnosis'
sys.path.insert(0,str(R/'experiments/v909_timed_command_contract'));from command_tube import NORMALS,HALF,RADIUS,pose_values,field
j=json.loads(gzip.decompress((O/'saved/MOTION_ENVELOPE.json.gz').read_bytes()))
# Truth object is explicitly offline-only and never passed to the candidate.
setup=json.loads((O/'saved/physics/SETUP.json').read_text());actor=setup['actor'];known=setup['known']
assert abs(actor['omega_rad_s']-OMEGA)<1e-12 and abs(actor['amplitude_m']-.25)<1e-12
p=PeriodicSupport();coverage=0;worst=-1e9;rows=[];wall=[];comparisons=[]
for state in j['states']:
 before=time.monotonic();changed=p.update(state['time'],state['native_tick'],state['support_bounds']);wall.append(time.monotonic()-before)
 if not changed:continue
 ts=state['time']+np.arange(0,2.31,.01);forecast=p.bounds(ts)
 actual=np.asarray(actor['anchor_xy'])+np.sin(OMEGA*ts+actor['phase_rad'])[:,None]*np.asarray(actor['axis_xy'])*actor['amplitude_m']
 worst=max(worst,float(np.max(actual@NORMALS.T-forecast)));coverage+=len(ts)*16
 # Independent HiGHS LP, actual causal inequalities, at fixed 1s checkpoints.
 if len(p.constraints)%4==0:
  matrix=np.array([[1.,math.sin(OMEGA*x['time']),math.cos(OMEGA*x['time'])]for x in p.constraints]);combined=np.r_[matrix,-matrix]
  k=len(ts)-1;vec=np.array([1.,math.sin(OMEGA*ts[k]),math.cos(OMEGA*ts[k])])
  errors=[]
  for i in range(8):
   b=np.r_[[x['support'][i]+EPS for x in p.constraints],[x['support'][i+8]+EPS for x in p.constraints]]
   for sign,col in [(1,i),(-1,i+8)]:
    lp=linprog(-sign*vec,A_ub=combined,b_ub=b,bounds=[(-8,8),(-.25,.25),(-.25,.25)],method='highs');assert lp.success
    errors.append(abs(-lp.fun+EPS-forecast[k,col]))
  comparisons.append(dict(tick=state['native_tick'],maximum_lp_error=float(max(errors))))
 if state['time']>=46. and (len(p.constraints)%4==0 or state['native_tick']>=6400):
  old=np.asarray(state['support_bounds'])+.08*2.3
  future=np.minimum(old,p.bounds([state['time']+2.3])[0])
  rows.append(dict(time=state['time'],tick=state['native_tick'],old_center_support=old.tolist(),periodic_center_support=future.tolist(),tightening_mean_m=float(np.mean(old-future)),vertices=max(len(x.v)for x in p.polytopes)))
checks=dict(all_saved_future_coverage=worst<=1e-8,independent_lp_supports=all(x['maximum_lp_error']<1e-7 for x in comparisons),nonempty_updates=bool(p.constraints),no_truth_to_candidate=True)
r=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,scope='Retrospective development on one exposed original WE trajectory. Known .32rad/s sinusoidal prior is NEW and narrower than arbitrary .08m/s motion. Not original-class acceptance or actual navigation.',future_support_coverage_count=coverage,worst_true_center_excess_m=worst,independent_lp_checks=len(comparisons)*16,maximum_lp_error=max(x['maximum_lp_error']for x in comparisons),update_wall_p95_s=float(np.quantile(wall,.95)),update_wall_max_s=max(wall),rows=rows,snapshot=p.snapshot(),lp=comparisons)
(O/'PERIODIC_NUMPY_QUALIFICATION.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k not in ['rows','snapshot','lp']}));assert r['passed']
