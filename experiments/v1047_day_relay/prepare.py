"""Freeze finite relay tables and three reverse source profiles, no models."""
import importlib.abc,itertools
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
import sys
sys.meta_path.insert(0,NoModel())
from kernel import *

def main():
 assert time.time()<HARD_END-1800;fixture=json.loads((R/'records/nav2_v1022_20261111/NS_SOURCE_FIXTURE.json').read_text());tasks=[];rows=[]
 for name,k in [('straight',0.),('left',.758770385),('right',-.758770385)]:
  task=dict(task_id='reverse_'+name,case_id='NORTH_SOUTH',seed=10010002,phase=3.673083947600074,dynamic=False,goal_xy=fixture['original_goal'],run_id='v1047-reverse-'+name,output=str(R/'runs/v858_nav2_verified/v1047'/('reverse_'+name)));p=Predictor(fixture['setup'],initial(fixture['packet']),PARAMETERS);requests=[[-.03,-.03*k,False]]*500+[[0.,0.,False]]*200;states=[p.state.copy()];ctrl=[]
  for request in requests:s,u=p.step(*request);states.append(s);ctrl.append(u)
  states=np.asarray(states);a,b=ref._old.Geometry(fixture['setup']['known'],None).clearances(states[:,:3]);lower=float(a.min());assert lower>=REQUIRED and abs(states[-50:,3:6]).max()<=.03;plan=dict(passed=True,state_path=states.tolist(),predicted_actuator_controls=np.asarray(ctrl).tolist(),planned_body_requests=requests,minimum_static_raw_m=lower,required_raw_m=REQUIRED,models=0);dump(C/('REVERSE_PLAN_'+task['task_id']+'.json'),plan);dump(C/('TASK_'+task['task_id']+'.json'),task);tasks.append(task);rows.append(dict(task_id=task['task_id'],minimum_static_raw_m=lower))
 dump(C/'REVERSE_TASKS.json',tasks);full=[dict(task_id='full_main'if i==0 else'full_repeat',case_id='WEST_EAST',seed=10010001,phase=.6573753567727383,dynamic=True,goal_xy=[4.,-2.],run_id='v1047-full-'+str(i),output=str(R/'runs/v858_nav2_verified/v1047'/('full_main'if i==0 else'full_repeat')))for i in range(2)];dump(C/'FULL_TASKS.json',full)
 for task in full:dump(C/('TASK_'+task['task_id']+'.json'),task)
 configs=[];(C/'configs').mkdir(exist_ok=True)
 for i,(ticks,weight,width,reverse)in enumerate(itertools.product([125,250],[1.5,3.],[512,1024],[False,True]),1):
  row=dict(id='source_%02d'%i,allow_reverse=reverse,move_ticks=ticks,heuristic_weight=weight,frontier_width=width,maximum_expansions=1000000,wall_s=2400);configs.append(row);dump(C/'configs'/(row['id']+'.json'),row)
 dump(C/'CONFIGS.json',configs);dump(O/'INPUT_SOURCE.json',json.loads((R/'runs/v1040_approach_information_audit/REBUILT_SOURCE.json').read_text()));dump(O/'PREPARATION.json',dict(passed=True,reverse_source_profiles=rows,software_configurations=len(configs),models=0,integrations=0,absolute_deadline_unix=HARD_END));print(json.dumps(dict(passed=True,rows=rows,software_configurations=len(configs),models=0)))
if __name__=='__main__':main()
