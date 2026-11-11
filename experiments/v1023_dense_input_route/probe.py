"""Fixed saved-source qualification; no model imports or integration."""
import importlib.abc,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1023_dense_input_route';sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL')
sys.meta_path.insert(0,NoModel());from input_route import construct
route,which=sys.argv[1:3]
if which=='initial':
 if route=='ns':fixture=json.loads((R/'records/nav2_v1022_20261111/NS_SOURCE_FIXTURE.json').read_text());packet=fixture['packet'];setup=fixture['setup'];goal=fixture['original_goal']
 else:
  pref=R/'runs/v858_nav2_verified/v1020/PREFLIGHTS'/route;p=json.loads((pref/'PREFLIGHT.json').read_text());setup=json.loads((pref/'SETUP.json').read_text());goal=[4.,-2.]
  packet=dict(body=p['body'],native_tick=0,sim_time=0.,body_measured_at=0.,dynamic_discovered=False,steering=dict(position=p['steering'][:2],velocity=p['steering'][2:],native_tick=0,measured_at=0.),controller_memory=dict(last_ctrl=[0.]*4,integral=0.))
 source=None;scope='pre_detection_static'
else:
 fixture=next(x for x in json.loads((R/'records/nav2_v1022_20261111/DYNAMIC_REJECTION_FIXTURES.json').read_text())if x['route']==route);packet=fixture['packet'];source=fixture['source'];goal=fixture['original_goal'];setup=fixture['setup'];scope='post_detection_full_cycle'
result=construct(packet,source,goal,setup,time.time()+100.,scope)
(O/(route+'_'+which+'.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['path','state_path','edge_targets','planned_body_requests','predicted_actuator_controls','heuristic']}))
