"""Scene/evaluation diagnostic only, zero navigation steps."""
import os,json,time
from pathlib import Path
from factory import initialize
from instrumentation import dump
start=time.monotonic();out=Path(os.environ['PHASE_RUNS'])/'v648_static_unknown'/'scene_probe_11';out.mkdir()
c,native=initialize(91000002,out/'paired');e=c['env'];import mujoco
rows=[]
for name in e.HIDDEN_GEOM_NAMES:
 gid=mujoco.mj_name2id(e.model,mujoco.mjtObj.mjOBJ_GEOM,name)
 if gid<0:continue
 rows.append({'name':name,'pos':e.model.geom_pos[gid].tolist(),'size':e.model.geom_size[gid].tolist(),'collision_masks':[int(e.model.geom_contype[gid]),int(e.model.geom_conaffinity[gid])],'alpha':float(e.model.geom_rgba[gid,3])})
owners=[]
for obj in e._phase19_object_chain():
 local=vars(obj)
 if 'circle_obstacles'in local:owners.append({'type':str(type(obj)),'circles':local['circle_obstacles'].tolist()})
dump(c['out']/'scene_geometry.json',{'hidden_physical':rows,'sensor_owners':owners,'elapsed_s':time.monotonic()-start,'actual_navigation_steps':0})
print(json.dumps(rows))
