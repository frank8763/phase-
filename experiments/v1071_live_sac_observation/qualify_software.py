import importlib.abc,sys,ast,json,math,time
from pathlib import Path
from types import SimpleNamespace
class NoPhysics(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy'}:raise AssertionError('NO_MODELS '+name)
sys.meta_path.insert(0,NoPhysics());C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1071_live_sac_observation';sys.path[:0]=[str(C),str(R/'runtime/mk-mini'),str(R/'experiments/v1070_frozen_sac_proposals')]
import numpy as np
from measurements import build_blocks,depth24,lidar36
from observation import BLOCKS
source=R/'runtime/mk-mini/training/envs/mkmini_real_indoor_phase3_depth_astar_sac_env.py';tree=ast.parse(source.read_text());method=next(n for cls in tree.body if isinstance(cls,ast.ClassDef)for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='_get_depth_features');namespace={'np':np};exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),str(source),'exec'),namespace)
class Renderer:
 def update_scene(self,*a,**k):pass
 def enable_depth_rendering(self):pass
 def disable_depth_rendering(self):pass
 def render(self):return self.image
rng=np.random.default_rng(1071);maximum=0.
for i in range(16):
 image=rng.uniform(.1,5,(64,64)).astype(np.float32);renderer=Renderer();renderer.image=image;fake=SimpleNamespace(depth_camera_id=0,depth_feature_dim=24,depth_max_range=5.,depth_camera_name='d435i_depth',renderer=renderer,data=None);maximum=max(maximum,float(np.max(abs(namespace['_get_depth_features'](fake)-depth24(image)))))
assert maximum<=2e-7
proxy=SimpleNamespace(robot_xy=np.array([-4.,-2.]),robot_yaw=0.,goal_xy=np.array([4.,-2.]),map_min=-5.,map_max=5.,circle_obstacles=np.array([[-1.,-1.,.1]]),rect_obstacles=np.array([[0.,2.,.1,1.]]));image=np.full((64,64),2.,np.float32);primary=np.linspace(0,1,32,dtype=np.float32);blocks=build_blocks(proxy,image,[0.,-2.],[0.,0.],primary);assert set(blocks)==set(BLOCKS)and all(np.asarray(blocks[k]).shape==(n,)for k,n in BLOCKS.items());assert np.array_equal(blocks['lidar'],primary)and np.array_equal(blocks['outer_lidar'],primary)and blocks['camera_goal'][0]==1.
rejected=[]
for name,x in [('missing_image',np.zeros((0,0))),('nonfinite_image',np.full((64,64),np.nan))]:
 try:depth24(x);raise RuntimeError('ACCEPTED '+name)
 except AssertionError:rejected.append(name)
result=dict(passed=True,original_depth24_parity_max_error=maximum,real_feature_layout_complete=True,primary32_reused_exactly=True,goal_camera_clipping_correct=True,negative_cases=rejected,models=0,integrations=0,live_sensor_qualification_pending=True);(O/'SOFTWARE_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
