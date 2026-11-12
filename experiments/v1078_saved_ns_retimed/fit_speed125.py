"""New-speed ARX calibration, fixed two cases and three held-out cases."""
import sys,importlib.abc,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1078_saved_ns_retimed'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODELS '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
import numpy as np
from kernel import PARAMETERS,virtual
assert json.loads((R/'runs/v1077_speed125_response/COMPLETION.json').read_text())['response_5_passed'];features=[];targets=[];inputs=[]
for task_id in ['response_01','response_03']:
 p=R/'runs/v858_nav2_verified/v1077'/task_id;assert json.loads((p/'FINAL_INDEPENDENT_AUDIT.json').read_text())['passed'];setup=json.loads((p/'physics/SETUP.json').read_text());z=np.load(p/'physics/NATIVE_TRACE.npz');cmd=np.array(json.loads((p/'physics/BODY_COMMANDS.json').read_text()));q=z['qpos'];vel=z['qvel'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));forward=vel[:,0]*np.cos(yaw)+vel[:,1]*np.sin(yaw);ctrl=z['ctrl'][:,setup['actuator_ids']];delta=np.array([virtual(row)for row in q[:,setup['steering_qpos_addresses']]]);u=ctrl[:125,2:].mean(axis=1);k=np.tan(delta[:125])/.6;features.append(np.c_[u,u*k*k]);targets.append(forward[:125]-PARAMETERS['speed_discrete'][0]*cmd[:125,3]);inputs.append(dict(task_id=task_id,trace_sha256=hashlib.sha256((p/'physics/NATIVE_TRACE.npz').read_bytes()).hexdigest(),fit_native=125))
A=np.vstack(features);b=np.concatenate(targets);coef=np.linalg.lstsq(A,b,rcond=None)[0];assert .8*PARAMETERS['speed_discrete'][1]<coef[0]<1.2*PARAMETERS['speed_discrete'][1]and -.02<coef[1]<0.;parameters=dict(speed=.125,speed_pole=PARAMETERS['speed_discrete'][0],speed_gain=float(coef[0]),curvature_speed_coefficient=float(coef[1]),fit_tasks=['response_01','response_03'],held_out_tasks=['response_02','response_04','response_05'],fit_inputs=inputs,fit_residual_rmse=float(np.sqrt(np.mean((A@coef-b)**2))),models=0,mujoco_integrations=0,sac_updates=0,original_speed08_predictor_unchanged=True);(C/'PARAMETERS.json').write_text(json.dumps(parameters,indent=2)+'\n');print(json.dumps(parameters),flush=True)
