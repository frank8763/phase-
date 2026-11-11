"""Saved-only all-native controller, prediction, historical and coverage audit."""
import importlib.util,json,sys
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];H=R/'runs/v858_nav2_verified/v1024/dynamic_we'
s=importlib.util.spec_from_file_location('v1039_audit_original_whole_input',R/'experiments/v1023_dense_input_route/whole_input.py');original=importlib.util.module_from_spec(s);s.loader.exec_module(original)
def audit(task, *, save=False):
 out=Path(task['output']);r=json.loads((out/'RESULT.json').read_text());setup=json.loads((out/'physics/SETUP.json').read_text());d=np.load(out/'physics/NATIVE_TRACE.npz');old=np.load(H/'physics/NATIVE_TRACE.npz');commands=json.loads((out/'physics/BODY_COMMANDS.json').read_text());n=len(commands);history=min(n,16740);maximum=0.
 if save:assert out.resolve().is_relative_to(R/'runs/v858_nav2_verified/v1039'),'AUDIT_WRITE_OUTSIDE_NEW_BATCH'
 for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
  if d[key][:history].size:maximum=max(maximum,float(abs(d[key][:history]-old[key][:history]).max()))
 p=original.Predictor(setup,dict(state=[0.]*8,last_ctrl=[0.]*4,integral=0.,virtual_rate=.6),original.PARAMETERS);controller_error=0.
 for command,u in zip(commands,d['ctrl']):
  _,v,w,mv,mw,stale=command;expected=p.adapter.compute(v,w,mv,mw,stale);controller_error=max(controller_error,float(abs(expected-u[setup['actuator_ids']]).max()))
 ctrl=d['ctrl'][:,setup['actuator_ids']];limits=np.asarray(setup['limits']);rates=np.asarray(setup['slew_per_second'])*.01;checks=dict(all_native_accounted=n==r.get('completed_native')==r['physical']['fully_recorded_native']==r['physical']['root_guard_native_count'],historical_reproduction=history==16740 and maximum<=1e-8,original_controller_reconstruction=controller_error<=1e-10,full_clearance=float(d['clearance'].min())>=.15-1e-8,full_self=float(d['self_margin'].min())>=-1e-10,no_bad_contact=r['physical']['bad_contacts']==0,legal_ctrl=bool((ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all()),legal_slew=bool((abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rates+1e-10).all()),entire_own_replay=r.get('replay',{}).get('passed')is True and r['own_replay_native']==n and r.get('replay',{}).get('maximum_qpos_qvel_ctrl_mocap_error',1.)<=1e-8)
 metrics=dict(historical_maximum_error=maximum,controller_maximum_error=controller_error,minimum_actual_clearance_m=float(d['clearance'].min()))
 if(out/'APPROACH_PLAN.json').exists()and n>16740:
  plan=json.loads((out/'APPROACH_PLAN.json').read_text());initial=json.loads((out/'APPROACH_INITIAL.json').read_text());p=original.Predictor(setup,original.initial(initial['packet']),original.PARAMETERS);ss=[p.state.copy()];uu=[]
  for request in plan['planned_body_requests']:state,u=p.step(*request);ss.append(state);uu.append(u)
  ss=np.asarray(ss);uu=np.asarray(uu);checks['whole_prediction_reconstruction']=float(abs(ss-np.asarray(plan['state_path'])).max())<=1e-10 and float(abs(uu-np.asarray(plan['predicted_actuator_controls'])).max())<=1e-10
  count=n-16740;q=d['qpos'][16740:];v=d['qvel'][16740:];expected=ss[1:count+1];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));delta=yaw-expected[:,2];pos=np.linalg.norm(q[:,:2]-expected[:,:2],axis=1);head=abs(np.arctan2(np.sin(delta),np.cos(delta)));checks['native_tracking']=float(pos.max())<=.04 and float(head.max())<=.035
  registered=np.asarray(json.loads((C/'REQUESTS.json').read_text()));actual=np.asarray([[r[1],r[2],float(r[5])]for r in commands[16740:]]);checks['exact_new_request_prefix']=bool(np.array_equal(registered[:count],actual));checks['all_6900_new_native']=count==6900;checks['complete_final_stop']=count==6900 and np.linalg.norm(v[-50:,:2],axis=1).max()<=.03 and abs(v[-50:,5]).max()<=.03 and abs(v[-50:][:,setup['steering_qvel_addresses']]).max()<=.03
  spec=importlib.util.spec_from_file_location('v1039_audit_geometry',R/'experiments/v1023_dense_input_route/geometry_model.py');gm=importlib.util.module_from_spec(spec);spec.loader.exec_module(gm);ref=gm.ref;REQUIRED=gm.REQUIRED
  a,b=ref._old.Geometry(setup['known'],initial['source']['periodic']).clearances(ss[:,:3]);checks['independent_full_cycle_prediction_geometry']=float(np.minimum(a,b).min())>=REQUIRED
  spec=importlib.util.spec_from_file_location('v1039_audit_cycle',R/'experiments/v1020_terminal_two_route_development/cycle_backup.py');cycle=importlib.util.module_from_spec(spec);spec.loader.exec_module(cycle)
  bounds=cycle.cycle_upper(initial['source']['periodic'])+1e-6;normals=np.c_[np.cos(np.arange(16)*np.pi/8),np.sin(np.arange(16)*np.pi/8)];actor=d['mocap_pos'][16740:,setup['actor']['mocap_id'],:2];checks['all_actual_future_actor_centers_covered']=bool((actor@normals.T<=bounds+1e-8).all())
  displacement=float(np.linalg.norm(q[-1,:2]-initial['packet']['body'][:2]));checks['actual_1m_approach']=displacement>=1.;metrics.update(maximum_position_m=float(pos.max()),maximum_heading_rad=float(head.max()),actual_displacement_m=displacement)
 else:checks['new_component_present']=False
 checks={k:bool(v)for k,v in checks.items()};proof=dict(passed=r['passed']and all(checks.values()),checks=checks,metrics=metrics,models=0,integrations=0,original_goal_arrival_claim=False,scope='finite safe observation component only')
 if save:(out/'FINAL_INDEPENDENT_AUDIT.json').write_text(json.dumps(proof,indent=2)+'\n')
 return proof
