"""Time-support conservative enclosure against original exact polygons."""
import sys,json,math,time,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1128_timed_terminal_source'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(C));from timed_source import Timed,NORMALS,interval_support,Solver,REQUIRED
from exact_timed import ExactTimedGeometry
import numpy as np

def main():
 x=json.loads((R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/COUPLED_ENTRY.json').read_text());t=Timed(x);rng=np.random.default_rng(1128);ticks=rng.integers(0,40000,256);poses=np.c_[rng.uniform(-4.5,4.5,(256,2)),rng.uniform(-np.pi,np.pi,256)];low=t.clearances(poses,ticks);exact=ExactTimedGeometry(x['setup']['known'],x['source']['periodic'],x['packet']['sim_time']).clearances(poses,ticks,.005);assert np.all(low<=exact+1e-10),'PROJECTED_BOUND_NOT_CONSERVATIVE'
 # Samples at native bin edges and wrap verify every vertex stays enclosed.
 violations=[]
 for j in [0,1,50,len(t.edges)-1]:
  at=np.linspace(t.edges[j]-.075,t.edges[j]+t.width+.075,41);dense=interval_support(x['source']['periodic']['vertices'],at,at);violations.append(float(np.max(dense-t.bounds[j])))
 assert max(violations)<=1e-10,'TIME_INTERVAL_ENCLOSURE_FAILURE'
 bad=json.loads(json.dumps(x));bad['source']['source_native_tick']=x['packet']['native_tick']+1
 try:Timed(bad)
 except AssertionError:pass
 else:raise AssertionError('FUTURE_SOURCE_ACCEPTED')
 bad=json.loads(json.dumps(x));bad['source']['source_age_s']=.201
 try:Timed(bad)
 except AssertionError:pass
 else:raise AssertionError('STALE_SOURCE_ACCEPTED')
 answer={'passed':True,'conservative_geometry_cases':256,'max_projected_minus_exact_m':float((low-exact).max()),'interval_vertex_enclosure_max_error':max(violations),'future_source_and_stale_negative_cases':2,'models':0,'physical_integrations':0,'dynamics_integrations':0};(O/'QUALIFICATION.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps(answer))
if __name__=='__main__':main()
