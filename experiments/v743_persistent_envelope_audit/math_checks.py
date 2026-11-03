"""Supplemental analytic edge cases; synthetic distance fields, no simulator."""
import hashlib,json,os,sys,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo/'experiments/v735_scan_differential_navigation'));sys.path.insert(0,str(repo/'experiments/v742_persistent_clearance_envelope'))
from envelope import Envelope
from recursive_domain import AXIS,HALF_DIAGONAL,SLACK,SPEED
from exact_footprint import pose_values
root=repo/'runs/v743_persistent_math_checks';root.mkdir(exist_ok=False);assert(repo/'REVIEW_PENDING').exists();os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});start=time.time();rng=np.random.default_rng(743);xx,yy=np.meshgrid(AXIS,AXIS,indexing='ij');origin=np.array([0.,0.]);checks={}
zero=Envelope(origin)
for i in range(11):zero.update(SimpleNamespace(origin=origin,time=i*.08,distance=np.zeros(xx.shape)))
points=rng.uniform(-6,6,(10000,2));assert np.array_equal(zero.point_lower(points,np.full(10000,.8)),np.zeros(10000));assert zero.point_lower([[100.,100.]],[.8])[0]==0.;checks['zero_information_and_unknown_boundary_no_free_space_invention']=True
c=np.array([4.,0.]);e=Envelope(origin);minimum_truth_slack=float('inf');minimum_monotonic_gain=float('inf');rejected=0;body_queries=0
for i in range(11):
 when=i*.08
 if i:
  direction=rng.normal(size=2);direction/=np.linalg.norm(direction);c+=direction*rng.uniform(0.,SPEED*.08);old=e.copy()
 distance=np.hypot(xx-c[0],yy-c[1])+HALF_DIAGONAL+SLACK if i%2==0 else np.zeros(xx.shape)
 e.update(SimpleNamespace(origin=origin,time=when,distance=distance));p=rng.uniform(-5,5,(10000,2));bound=e.point_lower(p,np.full(10000,when));truth=np.linalg.norm(p-c,axis=1);minimum_truth_slack=min(minimum_truth_slack,float((truth-bound).min()));assert np.all(bound<=truth+1e-12)
 if i:
  future=np.full(10000,when+3.28);gain=e.point_lower(p,future)-old.point_lower(p,future);minimum_monotonic_gain=min(minimum_monotonic_gain,float(gain.min()));assert np.all(gain>=-1e-12)
 for invalid in [when-.08]:
  try:e.point_lower([[0.,0.]],[invalid])
  except AssertionError:rejected+=1
  else:raise AssertionError('FUTURE_INFORMATION_ACCEPTED_FOR_EARLIER_TIME')
 # Ensure the centre is outside the footprint; test its actual external clearance.
 pp=np.c_[rng.uniform(-3,1.5,1000),rng.uniform(-2,2,1000),rng.uniform(-np.pi,np.pi,1000)];field=SimpleNamespace(half=np.array([.44,.375]),center_local=np.zeros(2),rectangles=np.empty((0,4)),circles=np.asarray([[*c,.10]]),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-100.,upper=100.));lower=e.body_lower(pp,np.full(1000,when));actual=pose_values(field,pp);assert np.all(lower<=actual+1e-12);body_queries+=len(pp)
checks.update(bounded_motion_point_queries=110000,finite_body_cover_queries=body_queries,same_absolute_time_monotonic_queries=100000,noncausal_time_queries_rejected=rejected,missing_new_certificate_retains_aged_old_bound=True)
result=dict(status='PERSISTENT_CERTIFICATE_ANALYTIC_EDGE_CASES_VERIFIED',checks=checks,minimum_actual_distance_slack_m=minimum_truth_slack,minimum_absolute_time_monotonic_gain_m=minimum_monotonic_gain,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),elapsed_s=time.time()-start,new_initializations=0,new_integrations=0,scope='Synthetic valid distance-source and bounded-motion edge cases; not sensor calibration, navigation or a replacement for assumptions.')
(root/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
