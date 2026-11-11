"""Straight-only ARX identification, turning trace held out unchanged."""
import importlib.abc,json,math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'runs/v1043_speed_predictor_identification';I=O/'input/selected'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1023_dense_input_route'))
from whole_input import Predictor,PARAMETERS,initial

def read(task):
 p=I/task;s=json.loads((p/'physics/SETUP.json').read_text());d=dict(np.load(p/'physics/NATIVE_TRACE.npz'));q=d['qpos'];v=d['qvel'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));speed=v[:,0]*np.cos(yaw)+v[:,1]*np.sin(yaw);lateral=-v[:,0]*np.sin(yaw)+v[:,1]*np.cos(yaw);u=d['ctrl'][:,s['actuator_ids']];packet=json.loads((p/'ACTUAL_INITIAL_PACKET.json').read_text());plan=json.loads((p/'REGENERATED_PROFILE.json').read_text());return s,packet,plan,q,yaw,speed,lateral,u

def compare(task,parameters,brake=None):
 setup,packet,plan,q,yaw,speed,lateral,u=read(task);p=Predictor(setup,initial(packet),parameters);states=[];controls=[]
 for request in plan['planned_body_requests'][:len(q)]:
  if brake is not None:p.p['speed_discrete']=parameters['speed_discrete']if request[0]>.005 else brake
  state,control=p.step(*request);states.append(state);controls.append(control)
 states=np.asarray(states);controls=np.asarray(controls);heading=abs(np.arctan2(np.sin(yaw-states[:,2]),np.cos(yaw-states[:,2])));pos=np.linalg.norm(q[:,:2]-states[:,:2],axis=1)
 return dict(native=len(q),maximum_position_m=float(pos.max()),maximum_heading_rad=float(heading.max()),maximum_speed_m_s=float(abs(speed-states[:,3]).max()),maximum_lateral_m_s=float(abs(lateral-states[:,4]).max()),final_position_error_vector=(q[-1,:2]-states[-1,:2]).tolist(),maximum_control_prediction_error=float(abs(u-controls).max()),all_original_response_position_heading_gates=bool(pos.max()<=.01 and heading.max()<=.008)),states

def main():
 s,packet,plan,q,yaw,speed,lateral,u=read('straight');prev=np.r_[packet['body'][3],speed[:-1]];command=u[:,2:].mean(axis=1);moving=np.asarray(plan['planned_body_requests'])[:len(q),0]>.005;rows=np.c_[prev,command];fit=np.linalg.lstsq(rows[moving],speed[moving],rcond=None)[0];braking=~moving;pole=float(prev[braking]@speed[braking]/(prev[braking]@prev[braking]));new=dict(PARAMETERS,speed_discrete=fit.tolist());old={};revised={}
 for task in ['straight','left']:old[task]=compare(task,PARAMETERS)[0];revised[task]=compare(task,new,[pole,0.])[0]
 result=dict(models=0,integrations=0,training_task='straight',heldout_task='left',heldout_is_truncated_343_native=True,old=old,revised=revised,moving_speed_discrete=fit.tolist(),braking_speed_discrete=[pole,0.],fit_rank=int(np.linalg.matrix_rank(rows[moving])),condition_number=float(np.linalg.cond(rows[moving])),old_failure_kept=True,new_physical_qualification=False,full_turn_and_stop_qualification_missing=True)
 (O/'DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
