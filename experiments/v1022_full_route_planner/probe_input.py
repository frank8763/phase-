"""Fixed saved snapshots only; ZERO new vehicle models or physics steps."""
import importlib.abc,json,sys,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1022_full_route_planner';sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL')
sys.meta_path.insert(0,NoModel());from input_route import construct
route,which=sys.argv[1:3]
if which=='initial':
 pref=R/'runs/v858_nav2_verified/v1020/PREFLIGHTS'/route;p=json.loads((pref/'PREFLIGHT.json').read_text());setup=json.loads((pref/'SETUP.json').read_text())
 packet=dict(body=p['body'],native_tick=0,sim_time=0.,body_measured_at=0.,dynamic_discovered=False,
  steering=dict(position=p['steering'][:2],velocity=p['steering'][2:],native_tick=0,measured_at=0.),controller_memory=dict(last_ctrl=[0.]*4,integral=0.))
 source=None;scope='pre_detection_static';task=next(t for t in json.loads((R/'experiments/v1020_terminal_two_route_development/TASKS.json').read_text())if t['route']==route);goal=task['goal_xy']
else:
 out=R/'runs/v858_nav2_verified/v1020'/('main_'+route);rows=json.loads((out/'RECOVERY_CORRIDORS.json').read_text());row=rows[0 if which=='first'else-1];setup=json.loads((out/'physics/SETUP.json').read_text())
 packet=row['search_packet'];source=row['search_source'];goal=row['original_goal'];scope='post_detection_full_cycle'
result=construct(packet,source,goal,setup,time.time()+90.,scope)
(O/(route+'_'+which+'.input_route.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k not in ['path','state_path','edge_targets','planned_body_requests','predicted_actuator_controls','heuristic']},ensure_ascii=False))
