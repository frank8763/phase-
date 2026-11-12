"""Exact failure regression + fixed held-out traces; zero model imports."""
import sys,importlib.abc,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1079_dual_steering_qualification'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
import numpy as np
from kernel import PARAMETERS,virtual,load
sys.path.insert(0,str(C));from steering_model import Predictor,initial
rows=[]
for task in json.loads((R/'experiments/v1077_speed125_response/TASKS.json').read_text()):
 out=Path(task['output']);setup=json.loads((out/'physics/SETUP.json').read_text());plan=json.loads((out/'PLAN.json').read_text());z=np.load(out/'physics/NATIVE_TRACE.npz');engine=Predictor(setup,initial(plan['packet']),PARAMETERS);ss=[engine.state.copy()]
 for rr in plan['planned_body_requests']:s,u=engine.step(*rr);ss.append(s)
 ss=np.asarray(ss);q=z['qpos'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));d=yaw-ss[1:,2];e=[float(np.linalg.norm(q[:,:2]-ss[1:,:2],axis=1).max()),float(abs(np.arctan2(np.sin(d),np.cos(d))).max()),float(abs(np.array([virtual(row)for row in q[:,setup['steering_qpos_addresses']]])-ss[1:,6]).max())];rows.append(dict(case=task['task_id'],held_out=task['task_id']in ['response_02','response_04','response_05'],passed=bool(np.all(np.array(e)<=[.04,.035,.015])),maximum_local_error=e))
out=R/'runs/v858_nav2_verified/v1078/saved_NS_complete_goal';inp=json.loads((out/'ACTUAL_CAUSAL_INPUT.json').read_text());setup=inp['setup'];oldplan=np.load(out/'COMPLETE_GOAL_PLAN.npz');z=np.load(out/'physics/NATIVE_TRACE.npz');n=len(z['qpos'])-15290;engine=Predictor(setup,initial(inp['packet']),PARAMETERS);ss=[engine.state.copy()]
for rr in oldplan['requests'][:n]:s,u=engine.step(*rr);ss.append(s)
ss=np.asarray(ss);q=z['qpos'][15290:];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));d=yaw-ss[1:,2];e=[float(np.linalg.norm(q[:,:2]-ss[1:,:2],axis=1).max()),float(abs(np.arctan2(np.sin(d),np.cos(d))).max()),float(abs(np.array([virtual(row)for row in q[:,setup['steering_qpos_addresses']]])-ss[1:,6]).max())];baseline=float(abs(np.array([virtual(row)for row in q[:,setup['steering_qpos_addresses']]])-oldplan['states'][1:n+1,6]).max());rows.append(dict(case='unfitted_saved_recovery_2784',held_out=True,baseline_failed=baseline>.015,baseline_steering_error=baseline,passed=bool(np.all(np.array(e)<=[.04,.035,.015])),maximum_local_error=e));result=dict(passed=all(x['passed']for x in rows),scope='Saved-data predictor qualification only; original V1078 remains failed',rows=rows,models=0,mujoco_integrations=0,sac_updates=0,physical_controller_changed=False,new_physical_window_opened=False,physical_ready=False);(O/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
