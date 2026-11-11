"""Independent saved-native checks; importing this cannot load a vehicle."""
import json,math,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'experiments/v1027_timed_speed_source'))
from whole_input import Predictor,PARAMETERS,virtual
def audit(task):
 out=Path(task['output']);r=json.loads((out/'RESULT.json').read_text());s=json.loads((out/'physics/SETUP.json').read_text());d=np.load(out/'physics/NATIVE_TRACE.npz');commands=json.loads((out/'physics/BODY_COMMANDS.json').read_text());plan=json.loads((out/'REGENERATED_PROFILE.json').read_text());states=np.asarray(plan['state_path']);requests=np.asarray(plan['planned_body_requests']);n=len(commands)
 p=Predictor(s,dict(state=[0.]*8,last_ctrl=[0.]*4,integral=0.,virtual_rate=.6),PARAMETERS);error=0.
 for command,actual in zip(commands,d['ctrl']):
  _,v,w,mv,mw,stale=command;u=p.adapter.compute(v,w,mv,mw,stale);error=max(error,float(abs(u-actual[s['actuator_ids']]).max()))
 ctrl=d['ctrl'][:,s['actuator_ids']];limits=np.asarray(s['limits']);rates=np.asarray(s['slew_per_second'])*.01
 # qpos orientation is quaternion; derive heading independently from trace.
 pose=d['qpos'];q=pose[:,3:7];yaw=np.arctan2(2*(q[:,0]*q[:,3]+q[:,1]*q[:,2]),1-2*(q[:,2]**2+q[:,3]**2));angle=yaw-states[1:,2];heading=abs(np.arctan2(np.sin(angle),np.cos(angle)));position=np.linalg.norm(pose[:,:2]-states[1:,:2],axis=1)
 # Encoder addresses are saved model metadata, independent of online errors.
 from pathlib import Path as _Path
 addresses=s.get('steering_qpos_addresses')
 assert addresses is not None,'MISSING_SAVED_STEERING_ADDRESSES'
 steering=np.asarray([virtual(x)for x in pose[:,addresses]]);steering_error=abs(steering-states[1:,6]);v=d['qvel'];stopped=np.linalg.norm(v[-50:,:2],axis=1).max()<=.03 and abs(v[-50:,5]).max()<=.03 and abs(v[-50:][:,s['steering_qvel_addresses']]).max()<=.03
 actual_requests=np.asarray([[x[1],x[2],float(x[5])]for x in commands])
 checks=dict(all_500_native_accounted=n==500==r['navigation_native']==len(pose),fixed_input_schedule=bool(np.array_equal(actual_requests,requests)),all_inputs_reconstructed=error<=1e-10,position_heldout=float(position.max())<=.01,heading_heldout=float(heading.max())<=.008,steering_heldout=float(steering_error.max())<=.015,original_actual_clearance=float(d['clearance'].min())>=.15-1e-8,full_self=float(d['self_margin'].min())>=-1e-10,legal_ctrl=bool((ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all()),legal_slew=bool((abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rates+1e-10).all()),no_bad_contacts=r['physical']['bad_contacts']==0,complete_200_tail=bool((requests[-200:]==0.).all())and bool(stopped),exact_full_replay=r.get('replay',{}).get('passed')is True and r.get('own_replay_native')==500,actual_component_passed=r['passed']is True)
 proof=dict(passed=all(checks.values()),checks=checks,metrics=dict(maximum_controller_error=error,maximum_position_m=float(position.max()),maximum_heading_rad=float(heading.max()),maximum_virtual_steering_rad=float(steering_error.max()),minimum_actual_clearance_m=float(d['clearance'].min())),models=0,integrations=0,navigation_acceptance=False,global_prediction_bound=False)
 (out/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(proof,indent=2)+'\n');return proof
