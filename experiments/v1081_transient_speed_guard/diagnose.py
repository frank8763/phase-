"""Saved native trace feedback loop, no vehicle or physics import."""
import sys,json,importlib.abc,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1081_transient_speed_guard'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();import numpy as np
from kernel import PARAMETERS,virtual,load
virtual_rate=load("v1081_original_virtual_rate",R/"experiments/v1003_causal_recovery_execution/predictor.py").virtual_rate
fit=R/'runs/v858_nav2_verified/v1078/saved_NS_complete_goal';test=R/'runs/v858_nav2_verified/v1080/remaining3555';S=json.loads((R/'experiments/v1078_saved_ns_retimed/PARAMETERS.json').read_text());pole=S['speed_pole'];gain=S['speed_gain'];curv=S['curvature_speed_coefficient']
def data(out,start):
 st=json.loads((out/'physics/SETUP.json').read_text());z=np.load(out/'physics/NATIVE_TRACE.npz');cmd=np.asarray(json.loads((out/'physics/BODY_COMMANDS.json').read_text()));q=z['qpos'];vv=z['qvel'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));v=vv[:,0]*np.cos(yaw)+vv[:,1]*np.sin(yaw);front=q[:,st['steering_qpos_addresses']];rates=vv[:,st['steering_qvel_addresses']];u=z['ctrl'][:,st['actuator_ids']];delta=np.array([virtual(x)for x in front]);vr=np.array([virtual_rate(a,b)for a,b in zip(front,rates)]);prevdelta=np.r_[0.,delta[:-1]];prevr=np.r_[0.,vr[:-1]];mean=u[:,2:].mean(axis=1);base=pole*cmd[:,3]+gain*mean+curv*mean*(np.tan(delta)/.6)**2;F=np.c_[prevdelta*prevr,prevr**2,cmd[:,3]*(np.tan(prevdelta)/.6)**2];mask=(np.arange(len(v))>=start)&(abs(cmd[:,1]-.125)<=1e-12);return F[mask],(v-base)[mask],dict(v=v,cmd=cmd,base=base,delta=delta,mask=mask)
A,b,xx=data(fit,15290);coef=np.linalg.lstsq(A,b,rcond=None)[0];T,y,yy=data(test,18074);pred=yy['base'][yy['mask']]+T@coef
result=dict(fit_native=len(b),held_out_native=len(y),features=['previous_virtual_delta_times_rate','previous_virtual_rate_squared','measured_speed_times_curvature_squared'],coefficients=coef.tolist(),fit_rmse=float(np.sqrt(np.mean((A@coef-b)**2))),fit_max_residual=float(abs(A@coef-b).max()),test_max_residual=float(abs(T@coef-y).max()),observed_cap_breach=bool(abs(yy['v'][yy['mask']]).max()>.13),predicted_one_step_speed_max=float(pred.max()),old_one_step_speed_max=float(yy['base'][yy['mask']].max()),actual_speed_max=float(yy['v'][yy['mask']].max()),models=0,integrations=0)
(O/'DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
