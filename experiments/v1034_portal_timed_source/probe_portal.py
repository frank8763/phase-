import importlib.abc,json,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1034_portal_timed_source'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C));from shoot import portal
from geometry_model import ref,REQUIRED
setup=json.loads((R/'runs/v858_nav2_verified/v1024/static_we/physics/SETUP.json').read_text());origin=dict(state=[-4.,-2.,0.,0.,0.,0.,0.,0.],last_ctrl=[0.]*4,integral=0.,virtual_rate=.6)
# Portal proposal comes from the known vertical divider opening and goal side.
# The fixed target heading points toward the lower-right goal chamber, never
# actor truth. This diagnostic target is declared before any new model.
pose=[-.05,-.75,-.15];started=time.time();r=portal(setup,origin,pose)
if r['passed']:
 states=r['state_path'];a,b=ref._old.Geometry(setup['known'],None).clearances(states[:,:3]);r.update(minimum_static_raw_m=float(a.min()),required_raw_m=REQUIRED,static_geometry_passed=float(a.min())>=REQUIRED,terminal_pose=states[-1,:3].tolist(),analytical_steps=len(r['requests']))
for k,v in list(r.items()):
 if isinstance(v,np.ndarray):r[k]=v.tolist()
r.update(models=0,integrations=0,physical_ready=False,actuation_authority=False,scope='PUBLIC_MAP_PORTAL_PREFIX_ONLY_NOT_FULL_ROUTE_OR_DYNAMIC',target_pose=pose,wall_s=time.time()-started)
(O/'PORTAL_PREFIX.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k not in ['state_path','ctrl','requests']}))
