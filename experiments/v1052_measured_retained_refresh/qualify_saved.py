"""Saved real states only: local forecast test and complete fresh-state suffix.

No vehicle is loaded. Future counterfactual certification is not execution.
"""
import importlib.abc,json,math,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1052_measured_retained_refresh'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
from refresh import refresh,remainder,roll,certify,validate_measured_packet
from kernel import load,virtual,sha,dump,Predictor,PARAMETERS
def main():
 begun=time.monotonic();raw=R/'runs/v858_nav2_verified/v1051/full_main';setup=json.loads((raw/'physics/SETUP.json').read_text());z=dict(np.load(raw/'physics/NATIVE_TRACE.npz'));commands=json.loads((raw/'physics/BODY_COMMANDS.json').read_text());x=json.loads((R/'runs/v1051_retained_corridor_entry/INPUT_SOURCE.json').read_text());plan=json.loads((R/'runs/v1051_retained_corridor_entry/SELECTED_PLAN.json').read_text());base=load('v1052_measured_encoder',R/'experiments/v1003_causal_recovery_execution/predictor.py');integrals=[0.];integral=0.
 for c in commands:
  v,w,mv,mw,stale=c[1:6]
  if stale or abs(v)<.005:integral=0.
  else:integral=float(np.clip(integral+(abs(v)-(1 if v>0 else-1)*mv)*.01,-.4,.4))
  integrals.append(integral)
 assert integrals[23640]==x['packet']['controller_memory']['integral'];q=z['qpos'];vel=z['qvel'];ctrl=z['ctrl'][:,setup['actuator_ids']];source_steps=len(commands)-23640
 def packet(i):
  k=23640+i;pose=q[k-1];yaw=math.atan2(2*(pose[3]*pose[6]+pose[4]*pose[5]),1-2*(pose[5]**2+pose[6]**2));c=commands[k];steer=pose[setup['steering_qpos_addresses']];rate=vel[k-1,setup['steering_qvel_addresses']];out=dict(x['packet']);out.update(body=[*pose[:2],yaw,c[3],c[4]],native_tick=k,sim_time=x['packet']['sim_time']+i*.01,body_measured_at=c[0],sent_at=c[0],steering=dict(position=steer.tolist(),velocity=rate.tolist(),native_tick=k,measured_at=c[0]),controller_memory=dict(last_ctrl=ctrl[k-1].tolist(),integral=integrals[k]));return out
 rows=[]
 for horizon in [100,200,400]:
  maximum=heading=0.;count=0
  for i in range(100,source_steps-horizon,100):
   p=packet(i);engine=Predictor(setup,__import__('kernel').initial(p),PARAMETERS);pred=[]
   for request in np.array(plan['planned_body_requests'])[i:i+horizon]:s,u=engine.step(*request);pred.append(s)
   pred=np.array(pred);actual=q[23640+i:23640+i+horizon];yaw=np.arctan2(2*(actual[:,3]*actual[:,6]+actual[:,4]*actual[:,5]),1-2*(actual[:,5]**2+actual[:,6]**2));maximum=max(maximum,float(np.linalg.norm(actual[:,:2]-pred[:,:2],axis=1).max()));d=yaw-pred[:,2];heading=max(heading,float(abs(np.arctan2(np.sin(d),np.cos(d))).max()));count+=1
  rows.append(dict(horizon_native=horizon,windows=count,maximum_position_m=maximum,maximum_heading_rad=heading,within_original_tracking_gates=maximum<=.04 and heading<=.035))
 dump(O/'LOCAL_FORECAST_AUDIT.json',dict(passed=all(z['within_original_tracking_gates']for z in rows),rows=rows,original_cumulative_40mm_failure_retained=True,overlapping_saved_windows_not_independent_samples=True,models=0,integrations=0))
 results=[]
 for i in [2000,4000,6000,8000,10000,12000,14000]:
  observed=packet(i);dump(O/('SAVED_PACKET_%05d.json'%i),observed);result=refresh(setup,observed,x['source'],x['goal'],plan['actions'],i);result['saved_source_native']=i;results.append(result);dump(O/('REFRESH_%05d.json'%i),result);print(json.dumps({k:v for k,v in result.items()if k!='actions'}),flush=True)
 # The action slicer preserves exact already-executed tick accounting.
 total=sum(a['ticks']for a in plan['actions']);negative=[]
 for elapsed in [-1,total+1]:
  try:remainder(plan['actions'],elapsed)
  except AssertionError:negative.append('invalid_elapsed_'+str(elapsed))
  else:raise AssertionError('ELAPSED_NOT_REJECTED')
 import copy
 for name,alter in [('stale',lambda p:p.update(sent_at=p['sent_at']+.051)),('encoder_tick',lambda p:p['steering'].update(native_tick=p['native_tick']+1)),('nan_pose',lambda p:p['body'].__setitem__(0,float('nan')))]:
  bad=copy.deepcopy(packet(2000));alter(bad)
  try:validate_measured_packet(bad,bad['sent_at'])
  except AssertionError:negative.append(name)
  else:raise AssertionError('PACKET_NOT_REJECTED '+name)
 for i in [0,1,200,14503,total]:assert sum(a['ticks']for a in remainder(plan['actions'],i))==total-i
 result=dict(local_forecasts=rows,complete_remainders_checked=len(results),complete_remainders_passed=sum(z['passed']for z in results),all_remainders_passed=all(z['passed']for z in results),original_actual_failure_retained=True,physical_ready=False,actual_goals=0,models=0,integrations=0,negative_cases=negative,raw_input_sha256=sha(raw/'physics/NATIVE_TRACE.npz'),commands_sha256=sha(raw/'physics/BODY_COMMANDS.json'),wall_s=time.monotonic()-begun)
 dump(O/'QUALIFICATION.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
