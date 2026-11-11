"""Saved nearest-prefix continuation gates; no controls applied to a plant."""
import importlib.abc,json,math,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1046_retreat_entry_timed_route'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C));from timed_input import Predictor,PARAMETERS,initial,Geometry,Expander,TARGETS,REQUIRED
x=json.loads((R/'runs/v1040_approach_information_audit/REBUILT_SOURCE.json').read_text());r=json.loads((O/'RESULT.json').read_text());p=Predictor(x['setup'],initial(x['packet']),PARAMETERS);elapsed=0
for action in r['nearest_candidate_actions']:
 v=(.08 if action['gear']>0 else-.03)if action['kind']=='move'else 0.;w=v*math.tan(action['target'])/.6
 for _ in range(action['ticks']):p.step(v,w,False);elapsed+=1
assert abs(p.state-r['nearest_candidate_state']).max()<=1e-10;engine=Expander(x['setup']);g=Geometry(x['setup']['known'],x['source']['periodic'],x['packet']['sim_time']);rows=[]
for target in TARGETS:
 ss,uu,mm=engine.expand(p.state,np.r_[p.adapter.last,p.adapter.integral],np.array([target]),125,np.array([.08]));static=g.static.clearances(ss[0,:,:3])[0];timed=g.clearances(ss[0,:,:3],elapsed+np.arange(1,126),.005);rows.append(dict(kind='forward',target=float(target),minimum_static_raw_m=float(static.min()),minimum_timed_raw_m=float(timed.min()),geometry_passed=bool(timed.min()>=REQUIRED)))
ss,uu,mm=engine.expand(p.state,np.r_[p.adapter.last,p.adapter.integral],np.array([0.]),200,np.array([0.]));timed=g.clearances(ss[0,:,:3],elapsed+np.arange(1,201),.005);stop=dict(kind='full_200_stop',minimum_timed_raw_m=float(timed.min()),geometry_passed=bool(timed.min()>=REQUIRED));rows.append(stop)
out=dict(models=0,integrations=0,nearest_pose=p.state[:3].tolist(),remaining_goal_m=r['best_goal_distance_m'],elapsed_prediction_native=elapsed,extensions=rows,all_tested_extensions_blocked=not any(r['geometry_passed']for r in rows),search_work_cap_not_infeasibility_proof=True);(O/'FRONTIER_DIAGNOSIS.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
