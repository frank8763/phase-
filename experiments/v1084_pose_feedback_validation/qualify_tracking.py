"""Saved failure plus measured-pose policy feedback proxies; no physical model."""
import sys,json,math,copy,importlib.abc
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs/v1084_pose_feedback_validation';CORE=R/'experiments/rpccr_execution_core'
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));from resource_policy import apply
apply();sys.path.insert(0,str(CORE));import numpy as np
from prediction import Predictor,initial
from kernel import PARAMETERS,virtual
from path_tracking import reference,request,complete_from_measurement,MAX_ACTIVE,STOP_NATIVE,BLOCK,select_reference
REC=R/'records/nav2_v1077_v1078_20261112/v1079_dual_steering_qualification';inp=json.loads((REC/'REMAINDER_INPUT.json').read_text());setup=inp['setup'];source=inp['source'];root=inp['packet'];offset,candidate_checks=select_reference(setup,root,source);path,arc=reference(offset)
def packet_from_engine(p,n):
 x=copy.deepcopy(root);s=p.state;x.update(body=[*map(float,s[:4]),float(s[5])],native_tick=18074+n,sim_time=root['sim_time']+.01*n,speed_episode=bool(p.high_speed_episode));x['steering'].update(position=p.front.tolist(),velocity=p.front_rate.tolist(),native_tick=18074+n);x['controller_memory']=dict(last_ctrl=p.adapter.last.tolist(),integral=float(p.adapter.integral));return x
# Exact saved latest measured failure state/memory; not a restart or a plant.
out=R/'runs/v858_nav2_verified/v1083/main_saved_ns';z0=np.load(out/'physics/NATIVE_TRACE.npz');z={k:z0[k]for k in z0.files};cmd=np.array(json.loads((out/'physics/BODY_COMMANDS.json').read_text()));p=Predictor(setup,initial(root),PARAMETERS);ce=0.
for i in range(18074,len(cmd)):
 enc=np.r_[z['qpos'][i-1,setup['steering_qpos_addresses']],z['qvel'][i-1,setup['steering_qvel_addresses']]];p.adapter.encoders=lambda enc=enc:enc;u=p.adapter.compute(*cmd[i,[1,2,3,4,5]]);ce=max(ce,float(abs(u-z['ctrl'][i,setup['actuator_ids']]).max()))
q=z['qpos'][-1];v=z['qvel'][-1];yaw=math.atan2(2*(q[3]*q[6]+q[4]*q[5]),1-2*(q[5]**2+q[6]**2));saved=copy.deepcopy(root);saved.update(body=[float(q[0]),float(q[1]),yaw,float(v[0]*math.cos(yaw)+v[1]*math.sin(yaw)),float(v[5])],sim_time=float(z['time'][-1]),native_tick=len(cmd));saved['steering'].update(position=q[setup['steering_qpos_addresses']].tolist(),velocity=v[setup['steering_qvel_addresses']].tolist(),native_tick=len(cmd));saved['controller_memory']=dict(last_ctrl=p.adapter.last.tolist(),integral=p.adapter.integral);progress=int(np.argmin(np.linalg.norm(path[:,:2]-np.array(saved['body'][:2]),axis=1)));latest,*_=complete_from_measurement(setup,saved,source,progress,offset=offset);saved_progress=progress;assert ce<=1e-10
class ProxyPlant(Predictor):
 def __init__(self,*args,bias=0.,**kw):super().__init__(*args,**kw);self.bias=bias;self.ticks=0
 def step(self,v,w,stale=False):
  before=self.state.copy();s,u=super().step(v,w,stale);error=self.bias if not(stale or abs(v)<.005)else math.copysign(min(abs(self.bias),.02*abs(s[3])),self.bias);nv=s[3]+error;nd=s[6];nr=s[7];mv=(before[3]+nv)/2;md=(before[6]+nd)/2;da=self.p['gain_a']*mv*math.tan(md)/.6*.01+self.p['steering_rate_b']*(nd-before[6]);nw=self.p['gain_a']*nv*math.tan(nd)/.6+self.p['steering_rate_b']*nr;lc=self.p['lateral_discrete'];nl=lc[0]*nv*math.tan(nd)/.6+lc[1]*nr;ml=(before[4]+nl)/2;a=before[2]+da/2;self.state=np.array([before[0]+.01*(mv*math.cos(a)-ml*math.sin(a)),before[1]+.01*(mv*math.sin(a)+ml*math.cos(a)),before[2]+da,nv,nl,nw,nd,nr]);self.ticks+=1;return self.state.copy(),u
results=[]
for name,bias in [('nominal',0.),('persistent_lag',-.0012),('persistent_boost',.002)]:
 plant=ProxyPlant(setup,initial(root),PARAMETERS,bias=bias);progress=0;n=0;maximum=np.zeros(3);complete=False;speedmax=0.;actual_states=[plant.state.copy()]
 try:
  while n<MAX_ACTIVE:
   r,progress,done=request(plant.state,path,arc,progress)
   if done:complete=True;break
   packet=packet_from_engine(plant,n);pred=Predictor(setup,initial(packet),PARAMETERS);requests=[];states=[];idx=progress
   for j in range(BLOCK):
    rr,idx,done=request(pred.state,path,arc,idx)
    if done:break
    s,u=pred.step(*rr);requests.append(rr);states.append(s)
   assert len(requests)>0,'EMPTY_MOVING_BLOCK'
   for rr,ss in zip(requests,states):
    s,u=plant.step(*rr);actual_states.append(s);n+=1;speedmax=max(speedmax,abs(s[3]));da=s[2]-ss[2];err=np.array([np.linalg.norm(s[:2]-ss[:2]),abs(math.atan2(math.sin(da),math.cos(da))),abs(s[6]-ss[6])]);maximum=np.maximum(maximum,err)
  assert complete,'PROXY_NOT_COMPLETE'
  for _ in range(STOP_NATIVE):s,u=plant.step(0.,0.);actual_states.append(s);speedmax=max(speedmax,abs(s[3]))
  from kernel import Geometry,REQUIRED
  minimum=Geometry(setup['known'],source['periodic'],root['sim_time']).complete(np.array(actual_states));distance=float(np.linalg.norm(plant.state[:2]-setup['case']['goal_xy']));passed=minimum>=REQUIRED and distance<=.45 and speedmax<=.13+1e-10 and np.all(maximum<=[.04,.035,.015])and np.linalg.norm(plant.state[3:6])<=.03;results.append(dict(name=name,passed=bool(passed),moving_native=n,goal_distance_m=distance,maximum_block_tracking=maximum.tolist(),maximum_speed=speedmax,minimum_raw_m=minimum))
 except AssertionError as e:results.append(dict(name=name,passed=False,error=str(e),native=n))
# Frame/monotonicity and stopping negatives are direct policy contracts.
negative=[]
for body in [np.array([np.nan,0.,0.]),np.array([path[-1,0]+1.,path[-1,1],0.])]:
 try:request(body,path,arc,len(path)-1);negative.append(False)
 except AssertionError:negative.append(True)
r=dict(passed=latest['passed']and all(x['passed']for x in results)and all(negative),latest_actual_failure_replanned=latest,latest_actual_control_reconstruction_error=ce,selected_offset_m=offset,finite_candidate_checks=candidate_checks,saved_progress=saved_progress,feedback_proxy_cases=results,negative_cases=negative,models=0,integrations=0,scope='Software proxy qualification, not new physical or global uncertainty guarantee');(O/'TRACKING_QUALIFICATION.json').write_text(json.dumps(r,indent=2)+'\n');(O/'SAVED357_PACKET.json').write_text(json.dumps(saved,indent=2)+'\n');print(json.dumps(r,indent=2));assert r['passed']
