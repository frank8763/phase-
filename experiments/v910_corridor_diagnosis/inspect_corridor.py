"""Saved-input cross-section diagnostic; no model, no generated execution."""
import gzip,hashlib,importlib.abc,json,math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v910_corridor_diagnosis'
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0] in {'mujoco','torch','factory','physical','vehicle','rclpy'}:raise AssertionError(name)
sys.meta_path.insert(0,Guard());sys.path.insert(0,str(R/'experiments/v909_timed_command_contract'))
from command_tube import NORMALS,HALF,RADIUS,pose_values,field
rows=json.loads(gzip.decompress((O/'saved/COMMAND_TUBES.json.gz').read_bytes()))
known=json.loads((O/'saved/physics/SETUP.json').read_text())['known']
# Fixed one-centimetre cross-section, all original heading bins, current V909 bound.
y=np.arange(-2.4,-.39,.01);a=np.linspace(-math.pi,math.pi,145)[:-1]
Y,A=np.meshgrid(y,a);P=np.c_[np.full(Y.size,3.),Y.ravel(),A.ravel()]
static=pose_values(field(known),P)
low=P[:,:2]@NORMALS.T-.44*abs(np.c_[np.cos(P[:,2]),np.sin(P[:,2])]@NORMALS.T)-.375*abs(np.c_[-np.sin(P[:,2]),np.cos(P[:,2])]@NORMALS.T)
result=[]
for tick in [4700,5000,5300,5600,5900,6200,6461]:
 row=min(rows,key=lambda z:abs(z['packet']['native_tick']-tick));s=row['source'];pr=row['proof'];h=s['support_bounds'];reserve=pr['spatial_reserve_m'];age=pr['source_age_s']+pr['body_age_s']+.05
 items=[]
 for horizon in [0.,.5,2.2,6.]:
  dyn=(low-np.asarray(h)-.1-.08*(age+horizon)).max(axis=1)-reserve
  margin=np.minimum(static-reserve,dyn);k=int(np.argmax(margin));feasible=margin>=.155
  items.append(dict(horizon_s=horizon,best_lower_m=float(margin[k]),best_pose=P[k].tolist(),feasible_sampled_poses=int(feasible.sum()),feasible_y_min=None if not feasible.any()else float(P[feasible,1].min()),feasible_y_max=None if not feasible.any()else float(P[feasible,1].max())))
 result.append(dict(tick=row['packet']['native_tick'],source_tick=s['source_native_tick'],body=row['packet']['body'],source=h,sections=items))
output=dict(models=0,integrations=0,rows=result,scope='Retrospective saved causal support; fixed x=3 cross-section and discrete y/headings. Necessary geometric probe, not complete SE2 path, not infeasibility proof, not actual navigation. Short horizons are diagnosis only and never authorize commands.')
(O/'CROSS_SECTION.json').write_text(json.dumps(output,indent=2)+'\n')
for r in result:print(r['tick'],[(v['horizon_s'],round(v['best_lower_m'],4),v['feasible_sampled_poses'],[round(z,3)for z in v['best_pose']])for v in r['sections']])
# Validate selectively restored records against the published inventory.
i=json.loads((O/'remote/phase-v909-continuation-20261109.INVENTORY.json').read_text());catalog={x['path']:x for x in i['files']}
for x in json.loads((O/'RESTORE.json').read_text())['rows']:assert catalog[x['path']]['sha256']==x['sha256']
print('RESTORED_MEMBERS_SHA_VERIFIED')
