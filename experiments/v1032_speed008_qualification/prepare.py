"""Freeze three nonfitted .08m/s response schedules before any physical model."""
import importlib.abc,json,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1032_speed008_qualification';sys.path[:0]=[str(C),str(R/'experiments/v1027_timed_speed_source')]
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL')
sys.meta_path.insert(0,NoModel());from whole_input import Predictor,PARAMETERS,initial;from geometry_model import ref,REQUIRED
fixture=json.loads((R/'records/nav2_v1022_20261111/NS_SOURCE_FIXTURE.json').read_text());packet=fixture['packet'];setup=fixture['setup'];rows=[]
for slot,(name,k)in enumerate([('straight',0.),('left',.758770385),('right',-.758770385)]):
 p=Predictor(setup,initial(packet),PARAMETERS);requests=[[.08,.08*k,False ]] *300+[[0.,0.,False]]*200;states=[p.state.copy()];ctrl=[]
 for request in requests:s,u=p.step(*request);states.append(s);ctrl.append(u)
 states=np.asarray(states);a,b=ref._old.Geometry(setup['known'],None).clearances(states[:,:3]);lower=float(a.min());passed=lower>=REQUIRED and abs(states[-50:,3:6]).max()<=.03 and abs(states[-50:,7]).max()<=.03
 plan=dict(passed=bool(passed),scope='NEW_SPEED_RESPONSE_ONLY_NOT_NAVIGATION',state_path=states.tolist(),planned_body_requests=requests,predicted_actuator_controls=np.asarray(ctrl).tolist(),minimum_static_raw_m=lower,required_raw_m=REQUIRED,models=0,integrations=0,physical_response_qualified=False)
 (C/('PLAN_'+name+'.json')).write_text(json.dumps(plan,separators=(',',':'))+'\n')
 rows.append(dict(task_id=name,passed=bool(passed),minimum_static_raw_m=lower,planned_native=500,prediction_heldout_not_fitted=True))
tasks=[dict(task_id=x['task_id'],slot=i,run_id='v1032-'+x['task_id'],case_id='NORTH_SOUTH',seed=10010002,phase=3.673083947600074,dynamic=False,goal_xy=fixture['original_goal'],output=str(R/'runs/v858_nav2_verified/v1032'/x['task_id']))for i,x in enumerate(rows)]
(C/'TASKS.json').write_text(json.dumps(tasks,indent=2)+'\n')
for x in tasks:(C/('TASK_'+x['task_id']+'.json')).write_text(json.dumps(x,indent=2)+'\n')
out=dict(passed=all(x['passed']for x in rows),rows=rows,models=0,integrations=0,original_controller_and_parameters_unchanged=True,actual_response_error_gates=dict(position_m=.01,heading_rad=.008,steering_rad=.015),no_fitting_on_actual_qualification=True)
(O/'ZERO_MODEL_QUALIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));assert out['passed']
