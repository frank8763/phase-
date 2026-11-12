"""Fast saved regression: symptom red/green, exact reused controls and feedback."""
import sys,json,math
from pathlib import Path
from qualify import R,C,O,NoModel,setup,PARAMETERS,Predictor,initial,packet,kin,P,rollout
import numpy as np
from kernel import load
Old=load('v1081_pre_guard_dual_predictor',R/'experiments/v1079_dual_steering_qualification/steering_model.py').Predictor
from governor import Adapter
rows=[]
for task in ['turn_left','turn_right']:
 out=R/'runs/v858_nav2_verified/v1080'/task;inp=json.loads((out/'ACTUAL_INPUT.json').read_text());z=np.load(out/'physics/NATIVE_TRACE.npz');cmd=np.asarray(json.loads((out/'physics/BODY_COMMANDS.json').read_text()));pp=np.load(out/'PLAN.npz');p=Predictor(setup,initial(inp['packet']),PARAMETERS);ss=[p.state.copy()]
 for r in pp['requests']:s,u=p.step(*r);ss.append(s)
 ss=np.asarray(ss);q=z['qpos'];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));da=yaw-ss[1:,2];err=np.array([np.linalg.norm(q[:,:2]-ss[1:,:2],axis=1).max(),abs(np.arctan2(np.sin(da),np.cos(da))).max(),abs(np.array([kin.virtual(x)for x in q[:,setup['steering_qpos_addresses']]])-ss[1:,6]).max()]);p=Predictor(setup,initial(inp['packet']),PARAMETERS);ce=0.;active=0
 for i,c in enumerate(cmd):
  p.front=np.array(setup['initial_steering_position'])if i==0 else q[i-1,setup['steering_qpos_addresses']].copy();p.front_rate=np.array(setup['initial_steering_velocity'])if i==0 else z['qvel'][i-1,setup['steering_qvel_addresses']].copy();u=p.adapter.compute(*c[[1,2,3,4,5]]);ce=max(ce,float(abs(u-z['ctrl'][i,setup['actuator_ids']]).max()));active+=getattr(p.adapter,'last_speed_projection',{}).get('limited',False)
 rows.append(dict(task_id=task,new_predictor_maximum_error=err.tolist(),passed=bool(np.all(err<=[.04,.035,.015])and ce<=1e-10 and active==0),unchanged_actual_ctrl_max_error=ce,actual_speed_projection_activations=active))
# Old speed setpoints must remain byte-exact before any .125 episode.
a=Old(setup,initial(inp['packet']),PARAMETERS);b=Predictor(setup,initial(inp['packet']),PARAMETERS);pe=0.
for v,w in [(0.,0.)]*100+[(.03,.005)]*100+[(.08,0.)]*100+[(0.,0.)]*2200:
 x,u=a.step(v,w);y,z=b.step(v,w);pe=max(pe,float(abs(x-y).max()),float(abs(u-z).max()))
qual=json.loads((O/'QUALIFICATION.json').read_text());diag=json.loads((O/'DIAGNOSIS.json').read_text());breach=diag['observed_cap_breach'];upper=diag['predicted_one_step_speed_max']+P['empirical_one_step_error_reserve'];detected=upper>.13;neg=[]
for label,mutate in [('nonfinite_body',lambda a:a.compute(.125,0.,float('nan'),0.)),('missing_encoders',lambda a:(setattr(a,'encoders',None),a.compute(.125,0.,.12,0.)) )]:
 a=Predictor(setup,initial(packet),PARAMETERS).adapter
 try:mutate(a);neg.append(False)
 except (AssertionError,ValueError):neg.append(True)
r=dict(passed=all(x['passed']for x in rows)and pe==0 and detected and all(neg)and qual['passed'],reused_actual_components=rows,original08_03_zero_state_control_error=pe,old_observed_speed_breach=breach,revised_one_step_upper_detects_breach=detected,revised_upper_at_saved_breach=upper,negative_rejections=neg,models=0,integrations=0,physical_ready=False);(O/'SAVED_REGRESSION.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));assert r['passed']
