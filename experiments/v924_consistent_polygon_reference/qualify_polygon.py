import ast,copy,gzip,importlib.abc,json,math,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v924_consistent_polygon_reference'
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in{'mujoco','torch','factory','physical','vehicle','rclpy'}:raise AssertionError(name)
sys.meta_path.insert(0,Block());sys.path[:0]=[str(C),str(R/'experiments/v891_dynamic_consistency_software'),str(R/'experiments/v881_timing_accounting_continuation'),str(R/'experiments/v864_diagnosis'),str(R/'experiments/v862_ready_static'),str(R/'experiments/v884_feasible_rpp')]
from polygon_geometry import distances,terminal_values,route_check
from polygon_audit import distance,terminal_check,route_check as independent_route
from cycle_backup import terminal_bound,cycle_upper
from support_envelope import polygon
from periodic_support import swept_bounds
from command_tube import admit
checks={};rng=np.random.default_rng(924);errors=[]
for _ in range(256):
 q=np.array([[-.7,-.5],[.8,-.5],[.9,.2],[.3,.9],[-.9,.3]])+rng.uniform(-2,2,2);p=np.c_[rng.uniform(-3,3,(12,2)),rng.uniform(-math.pi,math.pi,12)]
 online=distances(p,q);independent=np.array([distance(x,q)for x in p]);errors.extend(abs(online-independent).tolist())
checks['independent_3072_pose_distance']=max(errors)<1e-10
N=R/'runs/v858_nav2_verified/v920/main_we';rows=json.loads(gzip.decompress((N/'COMMAND_TUBES.json.gz').read_bytes()));known=json.load(open(N/'physics/SETUP.json'))['known'];cases=[]
for mode in ['SOFT','HARD']:
 for case in json.load(open(R/'runs/v922_reference_consistency_diagnosis'/mode/'RESULT.json'))['cases']:
  if not case['path']:continue
  row=min(rows,key=lambda r:abs(r['source']['source_scan_sim_time']-case['scan_time']));prior=row['source']['periodic'];start=time.perf_counter();new=route_check(case['path'],prior);elapsed=time.perf_counter()-start;ind=independent_route(case['path'],prior)
  cases.append(dict(mode=mode,time=case['scan_time'],online=new,independent=ind,online_wall_s=elapsed));assert abs(new['lower_m']-ind['lower_m'])<1e-9
checks['hard_late_two_certified']=sum(x['online']['passed']for x in cases if x['mode']=='HARD')==2
checks['soft_three_rejected']=all(not x['online']['passed']for x in cases if x['mode']=='SOFT')
# Mutate a known good path to overlap the center enclosure: whole chain must reject.
case=json.load(open(R/'runs/v922_reference_consistency_diagnosis/HARD/RESULT.json'))['cases'][-1];row=min(rows,key=lambda r:abs(r['source']['source_scan_sim_time']-case['scan_time']));prior=row['source']['periodic'];q=polygon(cycle_upper(prior));bad=copy.deepcopy(case['path']);bad[len(bad)//2]=[*q.mean(axis=0),0.]
checks['tampered_path_both_rejected']=not route_check(bad,prior)['passed']and not independent_route(bad,prior)['passed']
# Existing command/stop scientific contract is unchanged except this terminal.
comparison=[]
for i in np.linspace(0,len(rows)-1,40,dtype=int):
 r=rows[i];p=r['proof'];a=admit(r['packet'],r['source'],p['v'],p['w'],known,p['issued_at'])
 checks['original_short_time_static_dynamic_preserved']=checks.get('original_short_time_static_dynamic_preserved',True)and abs(a['static_lower_m']-p['static_lower_m'])<1e-10 and (a['dynamic_lower_m']==p['dynamic_lower_m']or abs(a['dynamic_lower_m']-p['dynamic_lower_m'])<1e-10)
 if r['source']['periodic']is not None:
  from command_tube import nominal
  pose=nominal(p['body'],p['v'],p['w'],[.2])[0];old=p['terminal_cycle_lower_m'];ind=terminal_check(pose,r['source']['periodic'],p['spatial_reserve_m']);comparison.append(abs(a['terminal_cycle_lower_m']-max(old,ind)))
checks['new_terminal_independent']=max(comparison)<1e-9
text=(C/'dynamic_proxy.py').read_text();checks['actual_route_return_requires_certificate']="if not row['dynamic_geometry_guard']['passed']"in text and text.index("if not row['dynamic_geometry_guard']['passed']")<text.rindex("handle.succeed()")
checks['hard_global_publisher_and_rebuild']=('reference_grid[reference_grid>0]=100'in(C/'motion_publisher.py').read_text()and"grid[grid>0]=100"in(C/'motion_audit.py').read_text())
for p in C.glob('*.py'):ast.parse(p.read_text())
report=dict(passed=all(checks.values()),checks=checks,models=0,integrations=0,independent_max_error=max(errors),cases=cases,terminal_max_error=max(comparison),physical_integration_not_yet_run=True)
for name in ['ZERO_MODEL_QUALIFICATION.json','RELEASE_QUALIFICATION.json','PLANNING_QUALIFICATION.json','AUDIT_QUALIFICATION.json']:(O/name).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));assert report['passed']
