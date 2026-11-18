"""Real installed ROS map/action binding at saved causal input; no physics."""
import sys,json,importlib.abc,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1121_coupled_route_night'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch'}:raise AssertionError('NO_MODEL_ROS '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(C));from night_planner import plan

def main():
 start=time.monotonic();x=json.loads((R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json').read_text());x['goal_yaw']=x['setup']['case']['yaw'];p=plan(x,O/'ros_entry_qualification',0.);assert p['passed'];answer={'passed':True,'actual_installed_map_action_bound':True,'models':0,'physical_integrations':0,'planner_poses':len(p['path']),'source_native_tick':p['config']['source_native_tick'],'planning_wall_s':p['planner']['planning_wall_s'],'total_wall_s':time.monotonic()-start};(O/'ROS_QUALIFICATION.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps(answer))
if __name__=='__main__':main()
