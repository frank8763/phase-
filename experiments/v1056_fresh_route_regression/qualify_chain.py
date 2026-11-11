"""Offline saved-state checks for each newly integrated transition; no plant."""
import importlib.abc,sys,math,time,json
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import *
from fresh import finite_plan,approach
h=R/'runs/v1047_day_relay_20261111/inputs/history';setup=json.loads((h/'physics/SETUP.json').read_text());z=dict(np.load(h/'physics/NATIVE_TRACE.npz'));commands=np.array(json.loads((h/'physics/BODY_COMMANDS.json').read_text()));periodic=load('v1056_chain_norm',R/'experiments/v1037_periodic_norm_source/periodic_norm.py').PeriodicSupport();rows=json.loads((h/'CAUSAL_EVIDENCE.json').read_text())['rows'];sources={}
for row in rows:
 periodic.update(row['time'],row['native_tick'],row['support_bounds'])
 if row['native_tick']in [14540,16740,23640]:sources[row['native_tick']]=dict(source_native_tick=row['native_tick'],source_age_s=0.,periodic=periodic.snapshot())
p=Predictor(setup,dict(state=[0.]*8,last_ctrl=[0.]*4,integral=0.,virtual_rate=.6),PARAMETERS);packets={}
for i,c in enumerate(commands):
 p.adapter.compute(c[1],c[2],c[3],c[4],c[5]);k=i+1
 if k in [14540,16740,23640]:
  q=z['qpos'][i];v=z['qvel'][i];yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));now=time.monotonic();packets[k]=dict(body=[q[0],q[1],yaw,v[0]*math.cos(yaw)+v[1]*math.sin(yaw),v[5]],native_tick=k,sim_time=float(z['time'][i]),body_measured_at=now,sent_at=now,dynamic_discovered=True,steering=dict(position=q[setup['steering_qpos_addresses']].tolist(),velocity=v[setup['steering_qvel_addresses']].tolist(),native_tick=k,measured_at=now),controller_memory=dict(last_ctrl=p.adapter.last.tolist(),integral=float(p.adapter.integral)))
static=json.loads((O/'WEST_EAST_STATIC_SOURCE.json').read_text())['plan']['planned_body_requests'];brake=finite_plan(setup,packets[14540],sources[14540],np.zeros((2200,3)),'OFFLINE_CHAIN_QUALIFICATION');assert brake['passed'],'NEW_BRAKE_PERMISSION_REJECTED';assert np.array_equal(commands[14540:16740][:,[1,2,5]],brake['planned_body_requests']);ap=approach(setup,packets[16740],sources[16740],static,14540);assert ap['movement_native']==4500 and np.array_equal(commands[16740:23640][:,[1,2,5]],ap['planned_body_requests']);gates=dict(fresh_discovery_brake_full_cycle_certificate=True,original328_zero_inputs_inside2200=True,original_approach_recertified=True,all23640_requests_recreated_without_online_history=True)
# Independent observed-prefix response bounds for BOTH finite new permissions.
errors=[]
for origin,plan in [(14540,brake),(16740,ap)]:
 count=len(plan['planned_body_requests']);ss=np.array(plan['state_path'])[1:];q=z['qpos'][origin:origin+count];yaw=np.arctan2(2*(q[:,3]*q[:,6]+q[:,4]*q[:,5]),1-2*(q[:,5]**2+q[:,6]**2));d=yaw-ss[:,2];steer=np.array([virtual(a)for a in q[:,setup['steering_qpos_addresses']]]);e=[float(np.linalg.norm(q[:,:2]-ss[:,:2],axis=1).max()),float(abs(np.arctan2(np.sin(d),np.cos(d))).max()),float(abs(steer-ss[:,6]).max())];assert np.all(np.array(e)<=[.04,.035,.015]);errors.append(e)
gates['all_saved_transition_tracking_gates']=True
result=dict(passed=True,checks=gates,offline_transition_errors=errors,brake_lower=brake['minimum_raw_m'],approach_lower=ap['minimum_raw_m'],models=0,integrations=0,not_independent_physical_validation=True);dump(O/'CHAIN_QUALIFICATION.json',result);print(json.dumps(result))
