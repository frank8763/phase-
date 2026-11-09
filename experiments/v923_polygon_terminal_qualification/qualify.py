import copy,gzip,importlib.abc,json,math,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v923_polygon_terminal_qualification';started=time.monotonic()
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','torch','factory','physical','vehicle','rclpy'}:raise AssertionError(name)
sys.meta_path.insert(0,Block());sys.path.insert(0,str(C))
from polygon_distance import convex_distance,rectangle,terminal,terminal_from_polygon
from cycle_backup import cycle_upper
from support_envelope import polygon
sys.path[:0]=[str(R/'experiments/v864_diagnosis'),str(R/'experiments/v884_feasible_rpp')]
from snapshot_geometry import dense
checks={};box=np.array([[-1.,-1.],[1.,-1.],[1.,1.],[-1.,1.]])
checks['axis_known_distance']=abs(convex_distance(box,box+[3.,0.])-1)<1e-12
checks['diagonal_known_distance']=abs(convex_distance(box,box+[3.,3.])-math.sqrt(2))<1e-12
checks['overlap']=convex_distance(box,box+[1.,1.])==0
checks['touch']=convex_distance(box,box+[2.,0.])==0
checks['symmetry']=convex_distance(box,rectangle([3.,2.,.7]))==convex_distance(rectangle([3.,2.,.7]),box)
for label,p in [('nan',np.full((4,2),math.nan)),('degenerate',np.zeros((4,2)))]:
 try:convex_distance(box,p)
 except AssertionError:checks[label+'_rejected']=True
 else:checks[label+'_rejected']=False
rng=np.random.default_rng(923);errors=[]
for _ in range(256):
 a=rectangle([*rng.uniform(-2,2,2),rng.uniform(-math.pi,math.pi)]);b=rectangle([*rng.uniform(-2,2,2),rng.uniform(-math.pi,math.pi)])
 # Independent dual separation on16384 complete angular directions.
 theta=np.arange(16384)*2*math.pi/16384;u=np.c_[np.cos(theta),np.sin(theta)]
 projection=(b@u.T).min(axis=0)-(a@u.T).max(axis=0)
 lower=max(0.,float(projection.max()));actual=convex_distance(a,b)
 error=actual-lower;angular_bound=float(np.linalg.norm(b[:,None,:]-a[None,:,:],axis=2).max())*math.pi/16384+1e-10
 assert -1e-10<=error<=angular_bound,(error,angular_bound)
 errors.append(error)
checks['independent_256_dual_direction_bounds']=True
N=R/'runs/v858_nav2_verified/v920/main_we';rows=json.loads(gzip.decompress((N/'COMMAND_TUBES.json.gz').read_bytes()));conversions=0;rejected=0;no_loosening=True
for r in rows:
 if r['source'].get('periodic')is None:continue
 p=r['proof'];new=terminal(pose=[*p['body'][:3]],prior=r['source']['periodic'],reserve=p['spatial_reserve_m'])
 # Endpoint must use proposed motion; same .2s equation as the original contract.
 from command_tube import nominal
 if [p['v'],p['w']]!=r['wanted']:
  from command_tube import admit
  original=admit(r['packet'],r['source'],*r['wanted'],json.loads((N/'physics/SETUP.json').read_text())['known'],p['issued_at'])
  endpoint=nominal(p['body'],*r['wanted'],[.2])[0];bound=terminal(endpoint,r['source']['periodic'],original['spatial_reserve_m']);rejected+=1
  conversions+=int(original['static_lower_m']>=.155 and original['dynamic_lower_m']>=.155 and max(bound,original['terminal_cycle_lower_m'])>=.155)
 assert time.monotonic()-started<600
cases=[]
for mode in ['SOFT','HARD']:
 for case in json.loads((R/'runs/v922_reference_consistency_diagnosis'/mode/'RESULT.json').read_text())['cases']:
  item=dict(mode=mode,time=case['scan_time'],planner_status=case['status'],registered_path_count=len(case['path']))
  if case['path']:
   row=min(rows,key=lambda r:abs(r['source']['source_scan_sim_time']-case['scan_time']));prior=row['source']['periodic'];center=polygon(cycle_upper(prior)+1e-6);samples=dense(case['path']);values=[terminal_from_polygon(p,center,.06)for p in samples]
   gap=.005+math.hypot(.44,.375)*.005;lower=min(values)-gap
   item.update(dense_samples=len(samples),polygon_distance_sample_lower_m=min(values),continuous_gap_reserve_m=gap,continuous_lower_m=lower,qualified_continuous_geometry=lower>=.155)
  cases.append(item)
report=dict(passed=all(checks.values()),checks=checks,independent_max_distance_error=max(errors),constructed_dual_cases=256,independent_angular_checks=256*16384,actual_saved_requests_examined=rejected,terminal_refusals_geometry_representationally_recovered=conversions,path_cases=cases,models=0,integrations=0,elapsed_s=time.monotonic()-started,physical_entrypoint=False,scope='Component distance correctness and fixed saved path geometry only; old V920 NOT_PASSED unchanged; no physical tracking or general safety claim')
(O/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['passed']
