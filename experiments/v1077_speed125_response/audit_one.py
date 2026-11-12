"""Saved physical response audit; model/vehicle imports forbidden."""
import sys,importlib.abc,gzip,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));from common import *
paths()
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL_AUDIT '+name)
sys.meta_path.insert(0,NoModel());from resource_policy import apply
apply()
import numpy as np
from kernel import Predictor,PARAMETERS,virtual
from fresh import finite_plan

def audit(task):
 out=Path(task['output']);physics=out/'physics';p=out/'RESULT.json';p=p if p.exists()else physics/'paired/ENTRY_FAILURE_RESULT.json';result=json.loads(p.read_text());assert result['passed'],'ACTUAL_RESPONSE_FAILED';setup=json.loads((physics/'SETUP.json').read_text());plan=json.loads((out/'PLAN.json').read_text());z=np.load(physics/'NATIVE_TRACE.npz');cmd=np.asarray(json.loads((physics/'BODY_COMMANDS.json').read_text()));ctrl=z['ctrl'][:,setup['actuator_ids']];n=len(z['qpos']);engine=Predictor(setup,dict(state=[0.]*8,last_ctrl=[0.]*4,integral=0.,virtual_rate=.6),PARAMETERS);error=0.
 for c,u in zip(cmd,ctrl):error=max(error,float(abs(u-engine.adapter.compute(c[1],c[2],c[3],c[4],c[5])).max()))
 req=np.vstack([np.tile([.125,.125*math.tan(task['target'])/.6,0.],(125,1)),np.zeros((2200,3))]);new=finite_plan(setup,plan['packet'],None,req,'INDEPENDENT_SAVED_RESPONSE_RECONSTRUCTION');states=np.asarray(new['state_path']);prediction_error=float(abs(states-np.asarray(plan['state_path'])).max());q=z['qpos'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));ang=yaw-states[1:,2];maximum=[float(np.linalg.norm(q[:,:2]-states[1:,:2],axis=1).max()),float(abs(np.arctan2(np.sin(ang),np.cos(ang))).max()),float(abs(np.array([virtual(row)for row in q[:,setup['steering_qpos_addresses']]])-states[1:,6]).max())];forward=z['qvel'][:,0]*np.cos(yaw)+z['qvel'][:,1]*np.sin(yaw)
 with gzip.open(physics/'CONTACTS.json.gz','rt')as f:contacts=json.load(f)
 with gzip.open(physics/'SENSORS.json.gz','rt')as f:sensors=json.load(f)
 limits=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second'])*.01;checks=dict(all_native=n==2325==len(cmd)==result['response_native']==result['physical']['root_guard_native_count']==result['physical']['fully_recorded_native'],actual_clearance=float(z['clearance'].min())>=.15-1e-8,full_self=float(z['self_margin'].min())>=-1e-10,actual_contacts_complete=len(contacts)==n+1,no_bad_contacts=not any(c[2]in ['robot_obstacle_contact','robot_obstacle_penetration','unknown_contact','robot_self_contact']for cs in contacts for c in cs),legal_ctrl=(ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all(),legal_slew=(abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rates+1e-10).all(),actual_body_caps=abs(forward).max()<=.13 and abs(z['qvel'][:,5]).max()<=.16,ctrl_reconstruction=error<=1e-10,original_prediction=new['passed']and prediction_error<=1e-8,exact_executed_requests=np.array_equal(cmd[:,[1,2,5]],req),local_tracking=np.all(np.asarray(maximum)<=[.04,.035,.015]),stop2200=np.array_equal(cmd[-2200:,[1,2,5]],np.zeros((2200,3))),last328_actual_stop=np.linalg.norm(z['qvel'][-328:,:2],axis=1).max()<=.03 and abs(z['qvel'][-328:,5]).max()<=.03,complete_own_replay=result['replay']['passed']and result['own_replay_native']==n and result['replay']['maximum_qpos_qvel_ctrl_mocap_error']<=1e-8 and result['replay']['contact_mismatched_ticks']==0,actual_motion=result['actual_motion_m']>=.08,actual_speed_response=abs(float(forward[:125].max())-.125)<=.015,clock=np.max(abs(z['time']-np.arange(1,n+1)*.01))<=1e-7,canonical_model=setup['model_sha256']=='412f0616d1160dad61bb395919d9442372108ad094e07a5122274df5b29201f8',sensor_calls=[s['native_tick']for s in sensors]==[0,0,0]+list(range(5,n+1,5)))
 checks={k:bool(v)for k,v in checks.items()};a=dict(passed=all(checks.values()),checks=checks,maximum_local_tracking=maximum,controller_reconstruction_error=error,prediction_reconstruction_error=prediction_error,maximum_actual_forward_speed=float(forward.max()),minimum_actual_clearance=float(z['clearance'].min()),models=0,integrations=0,task_id=task['task_id']);dump(out/'FINAL_INDEPENDENT_AUDIT.json',a);return a
if __name__=='__main__':
 q=audit(json.loads(Path(sys.argv[1]).read_text()));print(json.dumps(q),flush=True);sys.exit(0 if q['passed']else 1)
