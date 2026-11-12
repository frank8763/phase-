"""Independent native proposal geometry vs Python Euclidean reference."""
import sys,importlib.abc,json,ctypes,math
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from kernel import *
pin_threads();sys.path.insert(0,str(C));from planner import library,interval_support;from exact_timed import pg
x=json.loads((R/'runs/v1066_actual_route_diagnosis/ns_source_repro/INPUT.json').read_text());lib=library();setup=x['setup'];rect=np.ascontiguousarray(setup['known']['known_rectangles'],float);circles=np.ascontiguousarray(setup['known']['known_circles'],float);rng=np.random.default_rng(10671112);poses=np.c_[rng.uniform(-4.8,4.8,(1000,2)),rng.uniform(-math.pi,math.pi,1000)];reference=ref._old.Geometry(setup['known'],None).clearances(poses)[0];native=np.array([lib.static_pose(*p,rect,len(rect),circles,len(circles))for p in poses]);error=float(abs(reference-native).max());assert error<=1e-10
period=2*math.pi/.32;dt=.025;edges=np.arange(0,period,dt);support=interval_support(x['source']['periodic']['vertices'],edges-.075,edges+dt+.075);p=PARAMETERS;parameters=np.array([p['gain_a'],p['steering_rate_b'],*p['steering_discrete'],*p['speed_discrete'],*p['lateral_discrete'],p['curvature_speed_coefficient']],float);limits=np.ascontiguousarray(setup['limits'],float);rates=np.ascontiguousarray(setup['slew_per_second'],float);tested=0
for i in range(400):
 pose=np.r_[rng.uniform([-2.8,-2.7],[.2,.3]),rng.uniform(-math.pi,math.pi)];b=support[int(rng.integers(len(support)))];poly=pg.polygon(b);dynamic=float(pg.distances(pose[None,:],poly)[0])-.1;static=float(ref._old.Geometry(setup['known'],None).clearances(pose[None,:])[0][0]);expected=min(static,dynamic)>=REQUIRED;state=np.r_[pose,np.zeros(5)];memory=np.zeros(5);table=np.ascontiguousarray(np.vstack([b,b]));actions=np.zeros((1000,3));count=ctypes.c_int();stats=np.zeros(5);code=lib.search(state,memory,limits,rates,parameters,rect,len(rect),circles,len(circles),table,1,period,0.,np.array(x['goal'],float),0.,0,actions,ctypes.byref(count),stats);actual=code!=2;assert actual==expected,('DYNAMIC_GEOMETRY_DISAGREEMENT',i,expected,code,static,dynamic);tested+=1
result=dict(passed=True,static_random_poses=1000,maximum_static_error=error,timed_outer_polygon_classification_poses=tested,false_dynamic_admissions=0,independent_python_euclidean_reference=True,cpp_proposal_not_final_admission=True,models=0,integrations=0);dump(O/'GEOMETRY_QUALIFICATION.json',result);print(json.dumps(result),flush=True)
