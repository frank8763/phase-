"""One exact witness at best saved timing; no optimization or physics."""
import sys,json,time,importlib.abc
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1134_joint_space_time'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(R/'experiments/v1129_recording_entry_preparation'));from result_io import dump
sys.path.insert(0,str(R/'experiments/v1128_timed_terminal_source'));from timed_source import Timed,NORMALS,initial,REQUIRED
from source import Engine
from exact_timed import ExactTimedGeometry,pg
import numpy as np

def main():
 x=json.loads((R/'runs/v858_nav2_verified/v1122/r00_m15_b8_main_WEST_EAST/COUPLED_ENTRY.json').read_text());x['safe_terminal_pose']=json.loads((R/'runs/v1125_safe_goal_region/TERMINAL_SELECTION.json').read_text())['selected_body_pose'];old=json.loads((R/'runs/v1133_terminal_spatial_corridor/TERMINAL_REACHABILITY.json').read_text());phases=json.loads((R/'runs/v1133_terminal_spatial_corridor/TIMING_PROBES.json').read_text());best=max(phases,key=lambda r:r['minimum_timed_raw_m']);wait=best['initial_wait_native'];rows=[(0.,0.,wait,0)]+old['rows'];e=Engine(x['setup']);ss,uu=e.simulate(initial(x['packet']),rows);t=Timed(x);a,b=t.components(ss[:,:3],np.arange(len(ss)));k=int(np.argmin(b));exact=ExactTimedGeometry(x['setup']['known'],x['source']['periodic'],x['packet']['sim_time']);window=np.arange(max(0,k-100),min(len(ss),k+101));values=exact.clearances(ss[window,:3],window,.005);ix=int(np.argmin(values));phase=(x['packet']['sim_time']+.01*k)%t.period;j=min(int(phase/.025),len(t.edges)-1);poly=exact.polygons[j];pose=ss[k,:3];dynamic=float(pg.distances(pose[None,:],poly)[0]-.1);local=np.arange(0,4000,10);probe_poses=np.repeat(pose[None,:],len(local),axis=0);_,db=t.components(probe_poses,local);answer={'models':0,'physical_integrations':0,'analytical_cpp_native':e.native,'best_initial_wait_native':wait,'minimum_projected_dynamic_m':float(b[k]),'minimum_at_native':k,'original_time_s':float(x['packet']['sim_time']+.01*k),'pose':pose.tolist(),'exact_dynamic_distance_same_pose_m':dynamic,'exact_interval_window_min_m':float(values.min()),'actor_outer_polygon':poly.tolist(),'body_static_lower_m':float(a[k]),'required_m':REQUIRED,'fixed_pose_best_over_phase_projected_m':float(db.max()),'direction_hint':'joint source must change the spatial passage and clock; fixed phase waits were exhausted'};dump(O/'EXACT_WITNESS.json',answer);dump(O/'SELECTED_SEED.json',{'selected_z':old['selected_z'],'rows':old['rows'],'initial_wait_native':wait,'scope':'saved development source only'});print(json.dumps({k:v for k,v in answer.items()if k!='actor_outer_polygon'}))
if __name__=='__main__':main()
