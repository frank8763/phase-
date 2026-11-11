"""Fresh-causal prior cache containment at period boundaries, no truth input."""
import importlib.abc,json,sys,math
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1045_curvature_timed_route'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C));from timed_input import Geometry;from time_geometry import interval_support
x=json.loads((R/'runs/v1040_approach_information_audit/REBUILT_SOURCE.json').read_text());prior=x['source']['periodic'];start=x['packet']['sim_time'];g=Geometry(x['setup']['known'],prior,start);rng=np.random.default_rng(10450001);ticks=np.r_[rng.integers(0,40000,512),[-23640,-23639,-21677,-21676,0,1,39999,40000]];absolute=start+ticks*.01;ix=np.minimum(((absolute%g.period)/g.bin).astype(int),len(g.edges)-1);cached=g.support[ix];direct=interval_support(prior['vertices'],absolute-.075,absolute+.075);slack=float((cached-direct).min());assert slack>=-1e-10
miss=-math.inf
for i in range(0,len(absolute),8):
 ts=absolute[i]+np.linspace(-.075,.075,41)
 for direction,vertices in enumerate(prior['vertices']):
  v=np.asarray(vertices);value=v[:,0,None]+v[:,1,None]*np.sin(.32*ts)+v[:,2,None]*np.cos(.32*ts);miss=max(miss,float(value.max()-cached[i,direction]),float(-value.min()-cached[i,direction+8]))
assert miss<=1e-10
out=dict(passed=True,models=0,integrations=0,rows=len(absolute),directions=16,minimum_cached_over_direct_support=slack,maximum_sampled_vertex_miss=miss,clock_margin_s=.05,bin_s=.025,maximum_sample_half_s=.025,source_native_tick=x['packet']['native_tick']);(O/'TIME_QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
