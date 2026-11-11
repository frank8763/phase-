"""Execute the actual initialization arena against pure arrays, never a MJB."""
import importlib.abc,copy,json,math,os,sys,tempfile,types
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1063_night_entry_continuation_20261111';sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import load,dump,sha
from scene_binding import bind_scene,create_vehicle
import numpy as np
assert sha(C/'KNOWN_FIELD.json')==sha(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json');cases=json.loads((C/'SCENE_CASES.json').read_text());old=json.loads((R/'experiments/v855_renewal_worker/SCENE_CASES.json').read_text());assert cases[:2]==old[:2];changed=dict(cases[2]);changed['start_xy']=old[2]['start_xy'];changed['euclidean_distance_m']=old[2]['euclidean_distance_m'];assert changed==old[2]
try:create_vehicle(None,None)
except AssertionError as e:assert str(e)=='PHYSICAL_MODELS_DISABLED_FOR_PREPARATION'
else:raise AssertionError('MODEL_CREATE_NOT_BLOCKED')
arena=load('v1061_actual_arena_in_pure_arrays',C/'arena.py');known=json.loads((C/'KNOWN_FIELD.json').read_text());recorded=[];previous=sys.modules.get('unseen_prior');sys.modules['unseen_prior']=types.SimpleNamespace(set_public_origin=lambda start:recorded.append(np.array(start).tolist()));rows=[]
class MJ:
 mjtObj=types.SimpleNamespace(mjOBJ_GEOM=1)
 @staticmethod
 def mj_id2name(m,t,g):return m.names[g]
 @staticmethod
 def mj_forward(m,d):pass
try:
 for case in cases:
  model=types.SimpleNamespace(ngeom=19,geom_bodyid=np.zeros(19),geom_pos=np.zeros((19,3)),geom_size=np.ones((19,3)),geom_contype=np.ones(19),geom_conaffinity=np.ones(19),names=['real_rect_obs_'+str(i)for i in range(10)]+['real_circle_obs_'+str(i)for i in range(9)]);data=types.SimpleNamespace(qpos=np.zeros(12),qvel=np.zeros(11),ctrl=np.zeros(4),time=0.);env=types.SimpleNamespace(model=model,data=data,HIDDEN_GEOM_NAMES=[],robot_xy=np.zeros(2),goal_xy=np.zeros(2),robot_yaw=0.,dense_path=None,path_world=None,wp_index=0,path_index=0,prev_goal_dist=0.,prev_wp_dist=0.);env._phase19_object_chain=lambda:[env];B=types.SimpleNamespace(clean_map=lambda env:(known['known_rectangles'],known['known_circles']));old_env=os.environ.get('PHASE_FIELD_CASE');os.environ['PHASE_FIELD_CASE']=case['id']
  with tempfile.TemporaryDirectory(dir=O,prefix='arena_array_fixture_')as d:arena.prepare(dict(env=env,B=B,out=d),MJ)
  if old_env is None:os.environ.pop('PHASE_FIELD_CASE',None)
  else:os.environ['PHASE_FIELD_CASE']=old_env
  assert data.qpos[:2].tolist()==case['start_xy']and env.goal_xy.tolist()==np.array(case['goal_xy'],np.float32).tolist();assert recorded[-1]==case['start_xy'];rows.append(dict(case_id=case['id'],actual_constructor_function_array_test_passed=True,initial_xy=data.qpos[:2].tolist(),not_MJB_or_physical_qualification=True))
finally:
 if previous is None:sys.modules.pop('unseen_prior',None)
 else:sys.modules['unseen_prior']=previous
fake=types.SimpleNamespace(W=Path('/original'));old_arena=sys.modules.get('arena')
try:
 with bind_scene(fake,arena):assert fake.W==C and sys.modules['arena']is arena;raise RuntimeError('intentional_constructor_failure')
except RuntimeError:pass
assert fake.W==Path('/original')and sys.modules.get('arena')is old_arena;dump(O/'SCENE_BINDING_QUALIFICATION.json',dict(passed=True,rows=rows,only_EW_start_changed=True,known_map_byte_identical=True,context_restored_on_exception=True,physical_call_blocked_before_import=True,models=0,integrations=0));print(json.dumps(dict(passed=True,rows=rows,models=0,integrations=0)))
