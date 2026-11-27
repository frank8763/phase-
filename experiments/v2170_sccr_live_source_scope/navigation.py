"""Three actual sensor snapshots at fresh measured origins, zero policy controls."""
import math,sys
from context import R,C,read,load,digest
def run(v,binding,task,source,out,save,quota,refresh):
 q=binding['q'];np=q.np;setup=read(out/'physics/SETUP.json');goal=np.asarray(task['goal_xy']);observation=load('SCCR_original_observation',C/'observation.py');response=load('SCCR_original_full_response',C/'response.py');causal=load('SCCR_original_causal_tracker',R/'experiments/v1024_full_route_execution/causal.py');evidence=causal.Evidence(setup['known'])
 def current(cycle):
  z=observation.scan_only(v.scan(),v.count,float(v.d.time));evidence.update(z);r=observation.acquire(v,binding,z);save(f'cycle_{cycle:06d}_origin.json',dict(origin_native=v.count,receipt=r));return r
 def proof(receipt,requests,label,cycle):
  p=receipt['packet'];cs=None if evidence.first is None else evidence.source(v);z,ss,uu,mm=response.prove(q,setup,p,requests,goal,cs);z.update(origin_packet_sha256=digest(p),receipt=receipt,executed_native=0,arrays=f'cycle_{cycle:06d}_{label}.npz');z['hybrid_evidence']=binding['predictive_arrays'].persist(z,dict(states=ss,controls=uu,memory=mm,requests=np.asarray(requests,float)));save(f'cycle_{cycle:06d}_{label}.json',z);assert z['passed'],'SCCR_DEPTH_ORIGINAL_STOP_PREDICTION_REFUSED';return ss
 def move(ss,i,phase):
  v.adapter.parked_target=None;v._chain_phase=phase;v.step(0.,0.,False);e=np.asarray(q.initial(binding['packet'](v))['state'])-ss[i+1]
  assert np.linalg.norm(e[:2])<=.04 and abs(math.atan2(math.sin(e[2]),math.cos(e[2])))<=.035 and abs(e[6])<=.015,'SCCR_DEPTH_ORIGINAL_TRACKING_REFUSED'
 r=current(0);sampler=load('SCCR_actual_full_sensor_policy_union',C/'union_sampler.py').Sampler(v,np,save,quota,source,out,task,binding)
 try:
  for cycle in range(2):
   if cycle:r=current(cycle)
   sampler.capture(r);proof(r,[[0.,0.,False]for _ in range(2210)],'shadow',cycle);ss=proof(r,[[0.,0.,False]for _ in range(2205)],'admission_0',cycle)
   for i in range(5):move(ss,i,'FILTER_RECEDING_CURRENT')
   save(f'cycle_{cycle:06d}_executed.json',dict(kind='sensor_zero_hold',origin_native=5*cycle,executed_native=5))
  r=current(2);sampler.capture(r);ss=proof(r,[[0.,0.,False]for _ in range(2200)],'segment_stop',2)
  for i in range(2200):
   move(ss,i,'FILTER_SEGMENT_COMPLETE_STOP')
   if v.count%5==0:evidence.update(observation.scan_only(v.scan(),v.count,float(v.d.time)))
  save('cycle_000002_executed.json',dict(kind='sensor_component_stop',origin_native=10,executed_native=2200));assert binding['old'].previous.stopped(binding['packet'](v))and sampler.frames==3
 finally:sampler.close()
 return dict(passed=True,component_complete_original_stop=True,actual_sensor_frames=3,actual_depth_feature_dimensions=24,actual_complete_186_observation_frames=3,explicit_learned_policy_calls=6,explicit_actor_constructors=2,original_noise_profile_preserved=True,policy_outputs_never_actuated=True,factory_internal_policy_calls=None,whole_goal_with_original_stop=False,actual_original_goal_reached=False,complete_zero_stop_native=2200,actual_native=v.count,normal_native=10,formal_trial=False,native_optimizer_queries=0,full186_or_original_SCCR_qualified=False)
