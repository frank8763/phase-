"""Declared absence of any dynamic/unknown actor; static collision map unchanged."""
import math,json
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import numpy as np
from exact_footprint import pose_values
from scene_sensors import synchronize_sensor_arrays
class Motion:
 def __init__(self,config):assert config['dynamic_actor_present']is False;self.config=config
 def xy(self,t):return np.empty(0)
 def apply(self,m,d):assert m.nmocap==0
class Actor(Motion):
 def __init__(self,config,env,rect,circ,mj):
  super().__init__(config);self.env=env;self.rect=rect;self.circ=circ;self.mj=mj;self.maximum_displacement=0.;self.last_xy=None;self.observed_ticks=0
 def synchronize(self,m,d):
  self.apply(m,d);self.mj.mj_kinematics(m,d);self.mj.mj_collision(m,d);synchronize_sensor_arrays(self.env,self.rect,self.circ,[])
 def true_clearance(self,geometry,m,d):
  b=geometry.actual(m,d);q=d.qpos;yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2))
  f=SimpleNamespace(half=(b[2:]-b[:2])/2,center_local=(b[2:]+b[:2])/2,rectangles=np.asarray(self.rect).reshape(-1,4),circles=np.asarray(self.circ).reshape(-1,3),sensor_points=[],sensor_extra=0.,config=SimpleNamespace(lower=-5.,upper=5.))
  return float(pose_values(f,[[q[0],q[1],yaw]])[0])
def setup(context,env,rect,circ,F,H,B,mj,max_steer):
 m=env.model;d=env.data;assert len(rect)==10 and len(circ)==9 and m.nmocap==0 and float(d.time)==0.
 before=json.loads((Path(context['out'])/'ARENA_CONSTRUCTION.json').read_text())['known_static_geometries_preserved']
 for known in before:
  i=mj.mj_name2id(m,mj.mjtObj.mjOBJ_GEOM,known['name']);assert np.array_equal(m.geom_pos[i],known['pos'])and np.array_equal(m.geom_size[i],known['size'])and int(m.geom_contype[i])==known['contype']and int(m.geom_conaffinity[i])==known['conaffinity']
 tree=ET.parse(context['xml']);removed=[]
 for name in env.HIDDEN_GEOM_NAMES:
  i=mj.mj_name2id(m,mj.mjtObj.mjOBJ_GEOM,name)
  if i<0:continue
  m.geom_contype[i]=m.geom_conaffinity[i]=0;m.geom_pos[i,2]=-10.;m.geom_rgba[i,3]=0.
  node=tree.getroot().find(f".//geom[@name='{name}']");assert node is not None
  node.set('contype','0');node.set('conaffinity','0');node.set('pos',' '.join(map(str,m.geom_pos[i])));node.set('rgba',' '.join(map(str,m.geom_rgba[i])));removed.append(name)
 tree.write(context['xml'],encoding='unicode');mj.mj_forward(m,d)
 assert all(int(m.geom_contype[mj.mj_name2id(m,mj.mjtObj.mjOBJ_GEOM,n)])==int(m.geom_conaffinity[mj.mj_name2id(m,mj.mjtObj.mjOBJ_GEOM,n)])==0 for n in removed)
 config=dict(dynamic_actor_present=False,unknown_actor_count=0,mocap_bodies=0,removed_collision_and_sensor_geometries=removed,known_static_geometry_count=19,scope='known complete static map full-path diagnostic, not unknown or dynamic acceptance')
 (Path(context['out'])/'NO_DYNAMIC_CONSTRUCTION.json').write_text(json.dumps(dict(**config,known_static_geometries_preserved=before),indent=2)+'\n')
 synchronize_sensor_arrays(env,rect,circ,[]);return Actor(config,env,rect,circ,mj)
