"""Four physical steering-response coefficients; two fixed fit cases only."""
import sys,importlib.abc,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1079_dual_steering_qualification'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODELS '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply()
import numpy as np
A=[[],[]];b=[[],[]]
for name in ['response_01','response_03']:
 out=R/'runs/v858_nav2_verified/v1077'/name;setup=json.loads((out/'physics/SETUP.json').read_text());z=np.load(out/'physics/NATIVE_TRACE.npz');q=z['qpos'][:,setup['steering_qpos_addresses']];v=z['qvel'][:,setup['steering_qvel_addresses']];u=z['ctrl'][:,setup['actuator_ids'][:2]];previous_q=np.vstack([setup['initial_steering_position'],q[:-1]]);previous_v=np.vstack([setup['initial_steering_velocity'],v[:-1]])
 for k in range(2):
  features=np.c_[previous_v[:,k],u[:,k]-previous_q[:,k]];mask=np.linalg.norm(features,axis=1)>1e-6;A[k].append(features[mask]);b[k].append(v[mask,k])
coefs=[]
for k in range(2):
 aa=np.vstack(A[k]);bb=np.concatenate(b[k]);coef=np.linalg.lstsq(aa,bb,rcond=None)[0];matrix=np.array([[1-.01*coef[1],.01*coef[0]],[-coef[1],coef[0]]]);pole=float(abs(np.linalg.eigvals(matrix)).max());assert 0<coef[0]<1 and coef[1]>0 and pole<1;coefs.append(dict(rate_pole=float(coef[0]),target_gain=float(coef[1]),maximum_state_pole=pole,fit_rmse=float(np.sqrt(np.mean((aa@coef-bb)**2)))))
params=dict(front_wheels=coefs,fit_tasks=['response_01','response_03'],held_out_tasks=['response_02','response_04','response_05'],long_held_out='V1078 executed recovery prefix2784 including fast turn-release; never fit',physical_controller_changed=False,sac_updates=0,models=0,integrations=0);(C/'PARAMETERS.json').write_text(json.dumps(params,indent=2)+'\n');print(json.dumps(params),flush=True)
