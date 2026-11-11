"""Actual saved parking states, delayed publication and hostile handoff cases."""
import copy,importlib.abc,json,math,sys,time
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1053_parked_refresh_handoff';sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import load,sha,dump,predict,checks,Geometry,REQUIRED,virtual
from handoff import prepare,publish,hold_permission,parked
def main():
 begun=time.monotonic();H=O/'inputs';setup=json.loads((H/'physics/SETUP.json').read_text());z=dict(np.load(H/'physics/NATIVE_TRACE.npz'));commands=json.loads((H/'physics/BODY_COMMANDS.json').read_text());evidence=json.loads((H/'CAUSAL_EVIDENCE.json').read_text());x=json.loads((R/'runs/v1051_retained_corridor_entry/INPUT_SOURCE.json').read_text());plan=json.loads((R/'runs/v1051_retained_corridor_entry/SELECTED_PLAN.json').read_text());norm=load('v1053_real_saved_norm',R/'experiments/v1037_periodic_norm_source/periodic_norm.py');periodic=norm.PeriodicSupport();constraints=iter(evidence['periodic_constraints']);pending=next(constraints,None);integrals=[0.];integral=0.
 for command in commands:
  v,w,mv,mw,stale=command[1:6];integral=0. if stale or abs(v)<.005 else float(np.clip(integral+(abs(v)-(1 if v>0 else-1)*mv)*.01,-.4,.4));integrals.append(integral)
 def snapshot(tick):
  nonlocal pending
  k=23640+tick;q=z['qpos'][k-1];vel=z['qvel'][k-1];command=commands[k];yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));stamp=command[0];packet=dict(body=[*q[:2],yaw,command[3],command[4]],native_tick=k,sim_time=x['packet']['sim_time']+tick*.01,body_measured_at=stamp,sent_at=stamp,dynamic_discovered=True,steering=dict(position=q[setup['steering_qpos_addresses']].tolist(),velocity=vel[setup['steering_qvel_addresses']].tolist(),native_tick=k,measured_at=stamp),controller_memory=dict(last_ctrl=z['ctrl'][k-1,setup['actuator_ids']].tolist(),integral=integrals[k]))
  while pending is not None and pending['native_tick']<=k:periodic.update(pending['time'],pending['native_tick'],pending['support']);pending=next(constraints,None)
  scan_tick=k-k%5;source=dict(source_native_tick=scan_tick,source_age_s=(k-scan_tick)*.01,decision_at=stamp,periodic=periodic.snapshot());return packet,source
 ticks=[2437,3074,3884,6149,7367,8134,8889,9272,12800];rows=[];negatives=[]
 for tick in ticks:
  packet,source=snapshot(tick);parked(packet);hold=hold_permission(setup,packet,source);proposal=prepare(setup,packet,source,x['goal'],plan['actions'],tick);dump(O/('PROPOSAL_%05d.json'%tick),proposal);minimum=math.inf;waits=[]
  for delay in [0,50,500,1100]:
   fresh=copy.deepcopy(packet);fresh['native_tick']+=delay;fresh['sim_time']+=delay*.01;fresh['sent_at']+=delay*.01;fresh['body_measured_at']=fresh['sent_at'];fresh['steering'].update(native_tick=fresh['native_tick'],measured_at=fresh['sent_at']);latest=copy.deepcopy(source);latest.update(source_native_tick=fresh['native_tick'],source_age_s=0.,decision_at=fresh['sent_at']);published=publish(proposal,fresh,latest,fresh['sent_at']);ss,uu,rr,mm=predict(setup,packet,published['actions'],tail=False);delta=float(np.max(abs(ss-np.asarray(published['state_path']))));assert delta<=1e-8,'COMPOSED_PROFILE_DIFF';g=Geometry(setup['known'],source['periodic'],fresh['sim_time']);low=g.complete(ss);cc,upper=checks(ss,uu,rr,packet,setup,np.asarray(x['goal']),low,REQUIRED);assert all(cc.values()),cc;minimum=min(minimum,low);waits.append(published['phase_wait_ticks']);assert 0<published['next_checkpoint_native']<=len(rr)
  # Every rejected publication leaves the held command and candidate intact.
  signature=sha(O/('PROPOSAL_%05d.json'%tick))
  for name,mutate in [('stale_body',lambda p,s:p.update(sent_at=p['sent_at']+.051)),('encoder_tick',lambda p,s:p['steering'].update(native_tick=p['native_tick']+1)),('pose_drift',lambda p,s:p['body'].__setitem__(0,p['body'][0]+.002)),('control_owner_changed',lambda p,s:p['controller_memory']['last_ctrl'].__setitem__(0,p['controller_memory']['last_ctrl'][0]+.01)),('future_source',lambda p,s:s.update(source_native_tick=p['native_tick']+1)),('stale_sensor',lambda p,s:s.update(source_age_s=.052)),('expanded_domain',lambda p,s:s['periodic']['vertices'][0][0].__setitem__(0,s['periodic']['vertices'][0][0][0]+1.))]:
   bad=copy.deepcopy(packet);other=copy.deepcopy(source);mutate(bad,other)
   try:publish(proposal,bad,other,bad['sent_at'])
   except AssertionError:negatives.append(dict(tick=tick,case=name))
   else:raise AssertionError('NEGATIVE_NOT_REJECTED '+name)
   assert sha(O/('PROPOSAL_%05d.json'%tick))==signature
  rows.append(dict(saved_native=tick,passed=True,delays=[0,50,500,1100],selected_waits=waits,minimum_republished_raw_m=minimum,hold_raw_m=hold['minimum_raw_m'],prepare_wall_s=proposal['wall_s'],latest_periodic_tick=source['periodic']['source_tick']));dump(O/'PARTIAL.json',rows[-1]);print(json.dumps(rows[-1]),flush=True)
 result=dict(passed=True,rows=rows,negative_cases=negatives,models=0,integrations=0,saved_parking_states=len(rows),delayed_publications=4*len(rows),actual_dynamic_accepted=False,physical_ready=False,wall_s=time.monotonic()-begun);dump(O/'QUALIFICATION.json',result);print(json.dumps({k:v for k,v in result.items()if k not in ['rows','negative_cases']}))
if __name__=='__main__':main()
