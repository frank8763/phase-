"""Held-out .125 response then complete original saved-NS candidate, no plant."""
import sys,importlib.abc,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1078_saved_ns_retimed'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
import numpy as np
from kernel import virtual,initial,PARAMETERS,load,Predictor as Old
sys.path.insert(0,str(C));from calibrated_model import Predictor
rows=[]
for task in json.loads((R/'experiments/v1077_speed125_response/TASKS.json').read_text()):
 out=Path(task['output']);setup=json.loads((out/'physics/SETUP.json').read_text());plan=json.loads((out/'PLAN.json').read_text());z=np.load(out/'physics/NATIVE_TRACE.npz');p=Predictor(setup,initial(plan['packet']),PARAMETERS);states=[p.state.copy()]
 for request in plan['planned_body_requests']:q,u=p.step(*request);states.append(q)
 ss=np.asarray(states);q=z['qpos'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));a=yaw-ss[1:,2];e=[float(np.linalg.norm(q[:,:2]-ss[1:,:2],axis=1).max()),float(abs(np.arctan2(np.sin(a),np.cos(a))).max()),float(abs(np.array([virtual(row)for row in q[:,setup['steering_qpos_addresses']]])-ss[1:,6]).max())];rows.append(dict(task_id=task['task_id'],held_out=task['task_id']in ['response_02','response_04','response_05'],passed=bool(np.all(np.asarray(e)<=[.04,.035,.015])),maximum_local_error=e))
assert all(x['passed']for x in rows),'NEW_SPEED_HELD_OUT_RESPONSE_REJECTED';(O/'RESPONSE_MODEL_QUALIFICATION.json').write_text(json.dumps(dict(passed=True,fit_tasks=['response_01','response_03'],held_out_tasks=['response_02','response_04','response_05'],rows=rows,models=0,integrations=0),indent=2)+'\n')
x=json.loads((R/'records/nav2_v1076_20261112/ACTUAL_CAUSAL_ENTRY_INPUT.json').read_text());baseline=np.load(R/'records/nav2_v1076_20261112/PATH_PHASE_DIAGNOSIS.npz');retimer=load('v1078_calibrated_complete_retimer',C/'retime_complete.py');q=retimer.propose(x['setup'],x['packet'],x['source'],x['goal'],baseline['requests']);summary={k:v for k,v in q.items()if k not in ['states','controls','requests']};summary.update(response_model_held_out_passed=True,scope='Calibrated125 complete goal analytical qualification, saved NS15290 only');(O/'QUALIFICATION.json').write_text(json.dumps(summary,indent=2)+'\n');np.savez_compressed(O/'COMPLETE_GOAL_SOURCE.npz',states=q['states'],controls=q['controls'],requests=q['requests']);print(json.dumps(summary),flush=True);assert q['passed'],'CALIBRATED_COMPLETE_GOAL_REJECTED'
