"""Independent saved qpos/ctrl response and complete stop audit; zero models."""
import json,math,sys
from pathlib import Path
from common import C,R,dump
import numpy as np
from logic import kernel,Adapter,ERROR_LIMIT
def audit(task,save=True):
 out=Path(task['output']);s=json.loads((out/'physics/SETUP.json').read_text());r=json.loads((out/'RESULT.json').read_text());j=json.loads((out/'MODE_JOURNAL.json').read_text());cmd=json.loads((out/'physics/BODY_COMMANDS.json').read_text())
 with np.load(out/'physics/NATIVE_TRACE.npz')as z:d={k:z[k]for k in z.files}
 with np.load(C/('PLAN_'+task['task_id']+'.npz'))as z:planned=z['states'].copy();rr=z['requests'].copy();modes=z['modes'].copy();targets=z['targets'].copy();coupled=z['coupled'].copy()
 n=len(d['qpos']);assert n>0 and n==len(cmd)and len(j)==n
 owner=kernel.Predictor(s,dict(state=[0.]*8,last_ctrl=[0.]*4,integral=0.,virtual_rate=.6),kernel.PARAMETERS).adapter;owner.__class__=Adapter
 ctrl=d['ctrl'][:,s['actuator_ids']];maxctrl=0.;mode_ok=True;schedule_ok=True;memory_ok=True;body_binding=True
 for k,(body,row)in enumerate(zip(cmd,j)):
  initial_packet=json.loads((out/'ACTUAL_INITIAL_PACKET.json').read_text()) if k==0 else None
  enc=np.r_[initial_packet['steering']['position'],initial_packet['steering']['velocity']] if k==0 else np.r_[d['qpos'][k-1,s['steering_qpos_addresses']],d['qvel'][k-1,s['steering_qvel_addresses']]]
  owner.encoders=lambda enc=enc:enc.copy()
  _,v,w,mv,mw,stale=body;memory_ok&=bool(np.max(abs(owner.last-row['last_ctrl']))<=1e-10 and abs(owner.integral-row['integral'])<=1e-10)
  if k==0:measured=[initial_packet['body'][3],initial_packet['body'][4]]
  else:
   quat=d['qpos'][k-1,3:7];heading=math.atan2(2*(quat[0]*quat[3]+quat[1]*quat[2]),1-2*(quat[2]**2+quat[3]**2));velocity=d['qvel'][k-1];measured=[velocity[0]*math.cos(heading)+velocity[1]*math.sin(heading),velocity[5]]
  body_binding&=bool(np.max(abs(np.asarray(measured)-[mv,mw]))<=1e-10 and row['before_native']==k)
  owner.parked_target=row['target']if row['parked']else None;u=owner.compute(v,w,mv,mw,stale);maxctrl=max(maxctrl,float(abs(u-ctrl[k]).max()))
  if row['parked']:mode_ok&=bool(np.array_equal(ctrl[k,2:],np.zeros(2)))
  i=row['nominal_index']
  if i is not None:schedule_ok&=bool(i==k and np.array_equal([v,w,float(stale)],rr[i])and int(row['parked'])==modes[i]and row['target']==targets[i])
  else:schedule_ok&=bool(row['phase']=='failure_hold_stop'and v==w==0. and not row['parked'])
 q=d['qpos'];quat=q[:,3:7];yaw=np.arctan2(2*(quat[:,0]*quat[:,3]+quat[:,1]*quat[:,2]),1-2*(quat[:,2]**2+quat[:,3]**2));states=np.c_[q[:,:2],yaw]
 indices=[k for k,row in enumerate(j[:n])if row['nominal_index']is not None];reference=np.array([j[k]['nominal_index']+1 for k in indices],int)
 angles=yaw[indices]-planned[reference,2];steer=np.array([kernel.virtual(row)for row in q[:,s['steering_qpos_addresses']]])
 errors=np.c_[np.linalg.norm(q[indices,:2]-planned[reference,:2],axis=1),abs(np.arctan2(np.sin(angles),np.cos(angles))),abs(steer[indices]-planned[reference,6])]
 limits=np.asarray(s['limits']);rate=np.asarray(s['slew_per_second'])*.01
 a,_=kernel.ref._old.Geometry(s['known'],None).clearances(states);vel=d['qvel'];stopped=n>=50 and np.linalg.norm(vel[-50:,:2],axis=1).max()<=.003 and abs(vel[-50:,5]).max()<=.003 and abs(vel[-50:][:,s['steering_qvel_addresses']]).max()<=.015
 zero_tail=len(cmd)>=2200 and all(x[1]==x[2]==0. for x in cmd[-2200:])and all(not row['parked']and row['phase']in ['final_stop','failure_hold_stop']for row in j[-2200:])
 longitudinal=vel[:,0]*np.cos(yaw)+vel[:,1]*np.sin(yaw);lat=-vel[:,0]*np.sin(yaw)+vel[:,1]*np.cos(yaw);anchor=None;envelope_ok=True;entry_ok=True;initial_packet=json.loads((out/'ACTUAL_INITIAL_PACKET.json').read_text());prior=np.array(initial_packet['body'][:3]);previous_phase=None;motion_speed_ok=True
 for k,row in enumerate(j):
  if row['phase']in ['restart','final_stop']:anchor=None
  if row['parked']and row['phase']!=previous_phase:
   anchor=prior.copy();raw=float(kernel.ref._old.Geometry(s['known'],None).clearances(anchor[None,:])[0][0]);envelope_ok&=raw-.02-math.hypot(.44,.375)*.1>=kernel.REQUIRED
   if k:entry_ok&=bool(abs(longitudinal[k-1])<=.003 and abs(vel[k-1,5])<=.003 and abs(vel[k-1,s['steering_qvel_addresses']]).max()<=.015)
  if anchor is not None:
   angle=math.atan2(math.sin(yaw[k]-anchor[2]),math.cos(yaw[k]-anchor[2]));envelope_ok&=bool(np.linalg.norm(q[k,:2]-anchor[:2])<=.02 and abs(angle)<=.1)
  if row['parked']:motion_speed_ok&=bool(abs(longitudinal[k])<=.01)
  prior=states[k];previous_phase=row['phase']
 mask=np.array([coupled[j[k]['nominal_index']]for k in indices],bool);speed_errors=abs(longitudinal[indices]-planned[reference,3]);speed_response=bool((speed_errors[mask]<=.002).all())
 evidence=dict(recorded_native=n==r['new_actual_native']==r['physical']['root_guard_native_count'],actual_measurements_bound=body_binding,all_mode_memory_reconstructed=memory_ok and maxctrl<=1e-10,mode_rear_zero=mode_ok,fixed_schedule=schedule_ok,raw_actual_clearance=float(d['clearance'].min())>=.15-1e-8,independent_bounding_footprint=float(a.min())>=.15-1e-8,self_containment=float(d['self_margin'].min())>=-1e-10,no_bad_contacts=r['physical']['bad_contacts']==0,legal_ctrl=bool((ctrl>=limits[:,0]-1e-10).all()and(ctrl<=limits[:,1]+1e-10).all()),legal_slew=bool((abs(np.diff(np.vstack([np.zeros(4),ctrl]),axis=0))<=rate+1e-10).all()),complete2200tail=bool(zero_tail and stopped),replay_exact=r.get('replay',{}).get('passed')is True and r['own_replay_native']==n)
 evidence.update(coupled_full_footprint_envelope=bool(envelope_ok),actual_park_entry_rest=bool(entry_ok),coupled_motion_speed_bound=bool(motion_speed_ok),all_native_body_caps=bool((abs(longitudinal)<=.13).all()and(abs(lat)<=.03).all()and(abs(vel[:,5])<=.16).all()))
 response=bool(len(errors)and(np.max(errors,axis=0)<=ERROR_LIMIT).all()and speed_response);passed=bool(all(evidence.values())and response and n==8100 and r['passed'])
 proof=dict(passed=passed,evidence_passed=bool(all(evidence.values())),checks=evidence,complete_response_passed=response and n==8100,coupled_speed_prediction_passed=speed_response,maximum_coupled_speed_error_m_s=float(speed_errors[mask].max())if mask.any()else None,maximum_response_errors=errors.max(axis=0).tolist()if len(errors)else None,maximum_controller_error=maxctrl,physical_native=n,models=0,integrations=0,analytical_prediction_integrations=0,not_dynamic_acceptance=True)
 if save:dump(out/'FINAL_INDEPENDENT_AUDIT.json',proof)
 return proof
if __name__=='__main__':
 proof=audit(json.loads(Path(sys.argv[1]).read_text()));print(json.dumps(proof));sys.exit(0 if proof['passed']else 1)
