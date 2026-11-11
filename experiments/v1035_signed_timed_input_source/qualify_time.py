"""Independent interval-cache containment check against direct analytic support."""
import importlib.abc,json,sys,math
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1035_signed_timed_input_source'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
from timed_input import Geometry
from time_geometry import interval_support
p=R/'runs/v858_nav2_verified/v1024/dynamic_we';r=json.loads((p/'DYNAMIC_COMPLETE_PLAN.json').read_text());setup=json.loads((p/'physics/SETUP.json').read_text());prior=r['source']['periodic'];start=r['packet']['sim_time'];g=Geometry(setup['known'],prior,start);rng=np.random.default_rng(10350001);ticks=rng.integers(0,40000,512);ticks=np.r_[ticks,[-16740,-16739,-14777,-14776,0,1,39999,40000]];absolute=start+ticks*.01;phase=absolute%g.period;ix=np.minimum((phase/g.bin).astype(int),len(g.edges)-1);cached=g.support[ix];direct=interval_support(prior['vertices'],absolute-.075,absolute+.075);minimum_slack=float((cached-direct).min());assert minimum_slack>=-1e-10
# Evaluate actual coefficient vertices through each subinterval separately.
maximum_miss=-math.inf
for i in range(0,len(absolute),8):
 t=absolute[i];ts=t+np.linspace(-.075,.075,41);bounds=cached[i]
 for direction,vertices in enumerate(prior['vertices']):
  v=np.asarray(vertices);value=v[:,0,None]+v[:,1,None]*np.sin(.32*ts)+v[:,2,None]*np.cos(.32*ts);maximum_miss=max(maximum_miss,float(value.max()-bounds[direction]),float(-value.min()-bounds[direction+8]))
assert maximum_miss<=1e-10
other=interval_support(prior['vertices'],absolute+.2-.075,absolute+.2+.075);assert abs(other-direct).max()>1e-3
out=dict(passed=True,models=0,integrations=0,interval_rows=len(absolute),directions=16,periodic_bin_s=.025,clock_jitter_s=.05,maximum_native_sample_half_interval_s=.025,minimum_cached_over_direct_support_slack=minimum_slack,maximum_bruteforce_vertex_interval_miss=maximum_miss,time_shift_is_not_ignored=True,physical_ready=False)
(O/'TIME_QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
