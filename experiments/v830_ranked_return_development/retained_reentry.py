"""Causal full-contract return during the execution of a retained safe tail.
Only controller metadata can be committed after the real held-prefix matches.
"""
import copy,gzip,json
import numpy as np
from pathlib import Path
from self_geometry import containment_margin
from retained_coupled import prepare_retained
from instrumentation import dump

TARGETS=[np.array([0.,0.,float(m+d),float(m-d)])for m in [0,1,2]for d in [-6,-3,0,3,6]]

def poses(q):
 q=np.asarray(q);return np.c_[q[:,:2],np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2))]
def serial(x):
 if isinstance(x,np.ndarray):return x.tolist()
 if isinstance(x,np.generic):return x.item()
 raise TypeError(type(x).__name__)
def write_gz(p,x):
 with gzip.open(p,'xt')as f:json.dump(x,f,default=serial,allow_nan=False)

class RetainedReentry:
 def __init__(self,cell,predictor):
  self.cell=Path(cell);self.folder=self.cell/'retained_reentry';self.folder.mkdir();self.p=predictor;self.attempts=0;self.successes=0;self.private=0;self.pending=None;self.j=0;self.step=-1
 def begin_public(self,step):
  assert self.pending is None;self.step=step;self.j=0
 def after_native(self,real,reserved):
  if self.pending is not None:
   proof=self.pending['proof'];i=self.j;assert i<8
   error=max(np.max(abs(real.qpos-np.asarray(proof['qpos'])[i])),np.max(abs(real.qvel-np.asarray(proof['qvel'])[i])),np.max(abs(real.ctrl[self.p.command_map.ids]-proof['prefix_command'])))
   assert error<=1e-8,'NEW_REENTRY_NATIVE_PREFIX_MISMATCH'
  elif reserved.executing and reserved.cache is not None and reserved.cache['recovery_kind']=='COUPLED_OBSERVATION_BRAKE':
   i=reserved.cursor-8+self.j;assert 0<=i<320
   error=max(np.max(abs(real.qpos-reserved.cache['qpos'][i])),np.max(abs(real.qvel-reserved.cache['qvel'][i])),np.max(abs(real.ctrl[self.p.command_map.ids]-reserved.cache['controls'][i])))
   assert error<=1e-8,'RETAINED_COUPLED_NATIVE_MISMATCH'
  self.j+=1
 def try_return(self,env,field,state,reserved,path,index,step):
  if state['center']is not None or step%4!=0 or step-reserved.cache['created_step']<4:return None
  reserved.check_current_contract(env.data);real=env.data;p=self.p;m=p.model;mj=p.mj;ids=p.command_map.ids;last=real.ctrl[ids].copy();before=[getattr(real,n).copy()for n in ['qpos','qvel','ctrl','act','qacc_warmstart','mocap_pos','mocap_quat']];when=float(real.time);old=reserved.cache;cursor=reserved.cursor
  self.attempts+=1;records=[];selected=None;best=None;previous_private=p.prediction_steps
  for i,target in enumerate(TARGETS):
   scratch=mj.MjData(m);mj.mj_resetData(m,scratch)
   for n in ['qpos','qvel','act','qacc_warmstart']:getattr(scratch,n)[:]=getattr(real,n)
   scratch.time=when;scratch.ctrl[:]=0.;scratch.ctrl[ids]=last;mj.mj_forward(m,scratch);scratch.qacc_warmstart[:]=real.qacc_warmstart
   pq=[];pv=[];pb=[]
   for _ in range(8):
    p.native(m,scratch);p.prediction_steps+=1;mj.mj_kinematics(m,scratch);pq.append(scratch.qpos.copy());pv.append(scratch.qvel.copy());pb.append(p.self_geometry.actual(m,scratch))
   p.predict(scratch,target,ids,last,320,160);q=np.vstack([pq,p.last_forecast_qpos]);v=np.vstack([pv,p.last_forecast_qvel]);bounds=np.vstack([pb,p.last_self_bounds]);traj=poses(q);ctrl=np.vstack([np.repeat([last],8,axis=0),p.command_map.sequence(target,last,320,160)])
   values=field.trajectory_values(traj,.01);minimum=float(values.min());margin=float(containment_margin(bounds,p.domain).min());speed=float(np.linalg.norm(v[-1,:2]));angular=float(np.linalg.norm(v[-1,3:6]));progress=float(np.linalg.norm(real.qpos[:2]-env.goal_xy)-np.linalg.norm(q[-1,:2]-env.goal_xy))
   reason='TIME_CLEARANCE'if minimum<.155 else'SELF_DOMAIN'if margin<.002 else'TERMINAL_SPEED'if speed>.025 else'TERMINAL_ANGULAR_SPEED'if angular>.025 else None
   label=f'step{step:04d}_candidate{i:02d}';np.savez_compressed(self.folder/(label+'.npz'),initial_qpos=real.qpos.copy(),initial_qvel=real.qvel.copy(),initial_ctrl=last,initial_time=when,qpos=q,qvel=v,controls=ctrl,poses=traj,self_bounds=bounds)
   record=dict(index=i,label=label,target=target.tolist(),minimum_causal_clearance_m=minimum,self_margin_m=margin,terminal_speed_m_s=speed,terminal_angular_speed_rad_s=angular,goal_progress_m=progress,reason=reason)
   records.append(record)
   eligible=reason is None and np.mean(target[2:])>=1 and progress>=.05
   # Same deterministic progress ranking across the fixed 15 targets; ties by index.
   if eligible and (best is None or progress>best):
    best=progress;selected=i
  private=p.prediction_steps-previous_private;self.private+=private;assert private==15*328
  assert real.time==when and all(np.array_equal(getattr(real,n),value)for n,value in zip(['qpos','qvel','ctrl','act','qacc_warmstart','mocap_pos','mocap_quat'],before)) and reserved.cache is old and reserved.cursor==cursor,'PREDICTION_MUTATED_REAL_OR_OLD_CONTRACT'
  entry=dict(step=step,time=when,old_created_step=old['created_step'],old_native_cursor=cursor,real_entry_qpos=real.qpos.tolist(),real_entry_qvel=real.qvel.tolist(),real_entry_ctrl=last.tolist(),forecast_state=copy.deepcopy(state),records=records,selected_index=selected,private_integrations=private,hidden_world_geometry_used=False)
  dump(self.folder/f'step{step:04d}.json',entry)
  if selected is None:return None
  record=records[selected];z=np.load(self.folder/(record['label']+'.npz'))
  proof=dict(schema='V749_COUPLED_01',created_step=step,start_time=when,prefix_command=last.tolist(),target=record['target'],qpos=z['qpos'].tolist(),qvel=z['qvel'].tolist(),poses=z['poses'].tolist(),controls=z['controls'].tolist(),forecast_state=copy.deepcopy(state),minimum_causal_predicted_clearance_m=record['minimum_causal_clearance_m'],minimum_predicted_self_domain_margin_m=record['self_margin_m'],terminal_speed_m_s=record['terminal_speed_m_s'],terminal_angular_speed_rad_s=record['terminal_angular_speed_rad_s'],total_native_ticks=328,first_held_command_ticks=8,brake_after_native_ticks=168,hidden_world_geometry_used=False)
  self.pending=dict(proof=proof,entry=entry);write_gz(self.folder/f'step{step:04d}_proof.json.gz',proof)
  reserved.expected=(z['qpos'][7].copy(),z['qvel'][7].copy());reserved.expected_ctrl=last.copy();reserved.finish_pending=False
  gate=dict(status='PREDETECTION_CERTIFIED_PREFIX',certified_differential_return=True,hidden_world_geometry_used=False,active_gear=1,prediction_steps_total=p.prediction_steps,reentry_step=step,predicted_goal_progress_m=record['goal_progress_m'])
  return last,gate,path,index
 def after_public(self,real,reserved):
  if self.pending is None:return
  assert self.j==8
  proof=self.pending['proof'];entry=self.pending['entry'];assert reserved.cache['created_step']==entry['old_created_step'] and reserved.cursor==entry['old_native_cursor']
  cache,evidence=prepare_retained(proof,real,self.p.command_map);q=cache['initial_qpos'];yaw=float(poses(q[None,:])[0,2]);signed=float((cache['poses'][-1,:2]-q[:2])@np.array([np.cos(yaw),np.sin(yaw)]));cache['signed_reverse_displacement_m']=signed;cache['signed_longitudinal_displacement_m']=signed
  directory=self.cell/'recovery_contracts';directory.mkdir(exist_ok=True);write_gz(directory/f"reentry_{proof['created_step']:04d}.json.gz",cache)
  reserved.cache=cache;reserved.cursor=0;reserved.executing=True;reserved.finish_pending=False;reserved.expected=None;reserved.expected_ctrl=None;self.successes+=1
  dump(self.folder/f"step{proof['created_step']:04d}_committed.json",dict(evidence=evidence,old_created_step=entry['old_created_step'],old_cursor=entry['old_native_cursor'],new_created_step=proof['created_step'],actual_prefix_native=8,real_time=float(real.time),new_remaining_native=320,real_state_writes=0))
  self.pending=None
