"""Exercise actual run_phase namespace, disabled factory and nested ROS action."""
import sys,json,importlib.abc,time
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1121_coupled_route_night'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','torch'}:raise AssertionError('NO_ISOLATED_QUAL_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C));import worker
w=worker.load_worker();w.pipeline.configure(O)
def main():
 assert not(O/'ISOLATED_ENTRY_QUALIFICATION.json').exists();task=json.loads((C/'TASKS.json').read_text())[0];found,root,cfg,out=w.entry(str(O/(task['task_id']+'.json')));assert found==task and root==O
 try:w.factory(O).create_vehicle(Path(task['output'])/'physics',task)
 except AssertionError as e:assert str(e)=='PHYSICAL_MODELS_DISABLED_FOR_PREPARATION'
 else:raise AssertionError('MODEL_CREATED_DURING_ZERO_MODEL_ENTRY')
 from night_planner import plan
 x=json.loads((R/'runs/v1099_two_route_gate/EW_ACTUAL_INPUT.json').read_text());x['goal_yaw']=x['setup']['case']['yaw'];proposal=plan(x,O/'nested_ros_qualification',0.);assert proposal['passed'];answer={'passed':True,'actual_run_phase_namespace':True,'nested_real_ROS_action_passed':True,'disabled_actual_factory_refused':True,'models':0,'physical_integrations':0};(O/'ISOLATED_ENTRY_QUALIFICATION.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps(answer))
if __name__=='__main__':main()
