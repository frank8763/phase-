"""Fixed saved trajectory screening for stationary all-phase separation; zero models."""
import gzip,importlib.abc,json,math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];S=R/'runs/v858_nav2_verified/v914/main_we';O=R/'runs/v915_saved_stop_analysis'
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0] in {'mujoco','torch','factory','vehicle','physical','rclpy'}:raise AssertionError(name)
sys.meta_path.insert(0,Block());sys.path.insert(0,str(R/'experiments/v914_certified_wait_renewal'))
from command_tube import NORMALS,HALF,admit
from periodic_support import swept_bounds,bounds_from_vertices
rows=json.loads(gzip.decompress((S/'COMMAND_TUBES.json.gz').read_bytes()));known=json.loads((S/'physics/SETUP.json').read_text())['known'];witness=[];errors=[]
for row in rows:
 s=row['source'];p=row['packet'];a=row['proof'];prior=s.get('periodic')
 if prior is None:continue
 vertices=[np.asarray(x)for x in prior['vertices']]
 # Independent analytic maximum over every future phase for each coefficient vertex.
 upper=np.array([np.max(v[:,0]+np.hypot(v[:,1],v[:,2]))for v in vertices]+[np.max(-v[:,0]+np.hypot(v[:,1],v[:,2]))for v in vertices])+2e-7
 t=s['source_scan_sim_time'];other=swept_bounds(prior['vertices'],t,t+2*math.pi/.32);errors.append(float(abs(upper-other).max()))
 b=p['body'];theta=np.arctan2(NORMALS[:,1],NORMALS[:,0]);robot=np.array(b[:2])@NORMALS.T-.44*abs(np.cos(theta-b[2]))-.375*abs(np.sin(theta-b[2]))
 zero=admit(p,s,0,0,known,a['issued_at']);lower=float(np.max(robot-upper-.1)-zero['spatial_reserve_m'])
 witness.append(dict(tick=p['native_tick'],xy=b[:2],all_phase_dynamic_lower_m=lower,static_lower_m=zero['static_lower_m'],finite_stop_passed=zero['passed'],stationary_conditional_passed=bool(lower>=.155 and zero['static_lower_m']>=.155)))
last_safe=next((r for r in reversed(witness) if r['stationary_conditional_passed']),None)
result=dict(models=0,integrations=0,examined_saved_states=len(witness),independent_extrema_max_error=max(errors),last_saved_all_phase_separated=last_safe,last_state=witness[-1],scope='Analytic stationary geometry screening under the declared .32-frequency class and empirical pose residual only. Does not certify reachability, stopping dynamics at unexecuted branches, sensing robustness, indefinite closed-loop invariance or arrival.',witnesses=witness)
assert max(errors)<1e-10
(O/'CYCLE_WAIT_DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='witnesses'},indent=2))
