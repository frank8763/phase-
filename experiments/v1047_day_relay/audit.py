"""All-native saved audits; no model import, partial safety distinct from success."""
from kernel import *
def audit_native(task,full_profile=False):
 out=Path(task['output']);r=json.loads((out/'RESULT.json').read_text());setup=json.loads((out/'physics/SETUP.json').read_text());z=dict(np.load(out/'physics/NATIVE_TRACE.npz'));commands=json.loads((out/'physics/BODY_COMMANDS.json').read_text());n=len(commands);ctrl=z['ctrl'][:,setup['actuator_ids']];limits=np.asarray(setup['limits']);rate=np.asarray(setup['slew_per_second'])*.01;p=Predictor(setup,dict(state=[0.]*8,last_ctrl=[0.]*4,integral=0.,virtual_rate=.6),PARAMETERS);error=0.
 for c,u in zip(commands,ctrl):expected=p.adapter.compute(c[1],c[2],c[3],c[4],c[5]);error=max(error,float(abs(u-expected).max()))
 safety=dict(all_native_recorded=n==r.get('completed_native',r.get('new_response_native'))==len(z['qpos'])==r['physical']['fully_recorded_native']==r['physical']['root_guard_native_count'],actual_clearance=float(z['clearance'].min())>=.15-1e-8,self_margin=float(z['self_margin'].min())>=-1e-10,no_bad_contacts=r['physical']['bad_contacts']==0,legal_ctrl=bool((ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all()),legal_slew=bool((abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rate+1e-10).all()),controller_reconstruction=error<=1e-10,full_own_replay=r.get('replay',{}).get('passed')is True and r.get('own_replay_native')==n and r.get('replay',{}).get('maximum_qpos_qvel_ctrl_mocap_error',1.)<=1e-8)
 prediction={}
 plan_path=out/('FRESH_PLAN.json'if full_profile else'REGENERATED_PROFILE.json')
 if plan_path.exists():
  plan=json.loads(plan_path.read_text());origin=23640 if full_profile else 0;count=max(0,n-origin);states=np.asarray(plan['state_path'])[1:count+1];q=z['qpos'][origin:];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));pos=np.linalg.norm(q[:,:2]-states[:,:2],axis=1);angle=yaw-states[:,2];head=abs(np.arctan2(np.sin(angle),np.cos(angle)));steer=np.asarray([virtual(row)for row in q[:,setup['steering_qpos_addresses']]]);se=abs(steer-states[:,6]);prediction=dict(position_m=float(pos.max())if count else None,heading_rad=float(head.max())if count else None,steering_rad=float(se.max())if count else None,passed=bool(count and pos.max()<=(.04 if full_profile else.01)and head.max()<=(.035 if full_profile else.008)and se.max()<=.015))
 result=dict(safety_passed=all(safety.values()),safety=safety,passed=r['passed']and all(safety.values())and prediction.get('passed',False),prediction=prediction,maximum_controller_error=error,minimum_actual_clearance_m=float(z['clearance'].min()),models=0,integrations=0)
 if full_profile:result['passed']=result['passed']and r.get('actual_original_goal_reached',False)and r.get('historical_replay_maximum_error',1.)<=1e-8
 assert out.resolve().is_relative_to(R/'runs/v858_nav2_verified/v1047');dump(out/'FINAL_INDEPENDENT_AUDIT.json',result);return result

def compare(main,repeat):
 a=Path(main['output']);b=Path(repeat['output']);sa=json.loads((a/'physics/SETUP.json').read_text());sb=json.loads((b/'physics/SETUP.json').read_text());x=dict(np.load(a/'physics/NATIVE_TRACE.npz'));y=dict(np.load(b/'physics/NATIVE_TRACE.npz'));maximum=0.;length=True
 for k in ['qpos','qvel','ctrl','mocap_pos','mocap_quat']:
  length=length and x[k].shape==y[k].shape
  if length and x[k].size:maximum=max(maximum,float(abs(x[k]-y[k]).max()))
 ra=json.loads((a/'RESULT.json').read_text());rb=json.loads((b/'RESULT.json').read_text());same=sa['model_sha256']==sb['model_sha256']and ra['physical']['bad_contacts']==rb['physical']['bad_contacts']==0 and ra['physical']['first_actor_detection']==rb['physical']['first_actor_detection'];out=dict(passed=length and maximum<=1e-8 and same,same_length=length,maximum_qpos_qvel_ctrl_mocap_error=maximum,model_contacts_discovery_equal=same,models=0);dump(O/'FULL_REPEAT_AUDIT.json',out);return out
