"""Two measured learned-controller prefixes and complete ORIGINAL stopping gates."""
import math
from context import R,C,read,load,digest

def run(v,binding,task,source,out,save,quota,refresh):
 q=binding['q'];np=q.np;setup=read(out/'physics/SETUP.json');goal=np.asarray(task['goal_xy']);observation=load('SCCR_CP_original_observation',C/'observation.py');response=load('SCCR_CP_original_full_response',C/'response.py');causal=load('SCCR_CP_original_causal_tracker',R/'experiments/v1024_full_route_execution/causal.py');evidence=causal.Evidence(setup['known'])
 controller=load('SCCR_CP_persistent_controller',C/'cp_controller.py').Controller(task['run_id'])
 def current(cycle):
  z=observation.scan_only(v.scan(),v.count,float(v.d.time));evidence.update(z);r=observation.acquire(v,binding,z);save(f'cycle_{cycle:06d}_origin.json',dict(origin_native=v.count,receipt=r));return r
 def proof(r,requests,label,cycle):
  p=r['packet'];cs=None if evidence.first is None else evidence.source(v);z,ss,uu,mm=response.prove(q,setup,p,requests,goal,cs);z.update(origin_packet_sha256=digest(p),receipt=r,executed_native=0,arrays=f'cycle_{cycle:06d}_{label}.npz');z['hybrid_evidence']=binding['predictive_arrays'].persist(z,dict(states=ss,controls=uu,memory=mm,requests=np.asarray(requests,float)));save(f'cycle_{cycle:06d}_{label}.json',z);assert z['passed'],'SCCR_CP_ORIGINAL_FULL_RESPONSE_REFUSED';return ss
 def move(ss,i,request,phase):
  v.adapter.parked_target=None;v._chain_phase=phase;before=v.count;v.step(*request);assert v.count==before+1
  e=np.asarray(q.initial(binding['packet'](v))['state'])-ss[i+1]
  assert np.linalg.norm(e[:2])<=.04 and abs(math.atan2(math.sin(e[2]),math.cos(e[2])))<=.035 and abs(e[6])<=.015,'SCCR_CP_ORIGINAL_TRACKING_REFUSED'
 r=current(0);sampler=load('SCCR_CP_actual_full_sensor_policy_union',C/'union_sampler.py').Sampler(v,np,save,quota,source,out,task,binding,controller)
 try:
  for cycle in range(2):
   record=sampler.capture(r);proposal=controller.propose(record,episode_id=task['run_id']);save(f'SCCR_CP_{cycle:06d}_PROPOSAL.json',proposal)
   request=proposal['request'];assert len(request)==3
   contract=load('SCCR_CP_unchanged_command_domain',R/'experiments/v1288_baseline_interface/contract.py');contract.twist(*request[:2])
   proof(r,[list(request)for _ in range(10)]+[[0.,0.,False]for _ in range(2200)],'shadow',cycle)
   ss=proof(r,[list(request)for _ in range(5)]+[[0.,0.,False]for _ in range(2200)],'admission_0',cycle)
   a=v.count
   for i in range(5):move(ss,i,request,'FILTER_RECEDING_CURRENT')
   assert a==cycle*5 and len(v.commands)==a+5
   applied=[]
   for i,row in enumerate(v.commands[a:a+5]):
    actual=[row[1],row[2],row[5]];assert actual==request
    applied.append(dict(episode_id=task['run_id'],before_native=a+i,request=actual,applied=True))
   r=current(cycle+1);committed=controller.commit(r['packet'],episode_id=task['run_id'],token=proposal['token'],applied_rows=applied);save(f'SCCR_CP_COMMIT_{v.count:06d}.json',committed)
   save(f'cycle_{cycle:06d}_executed.json',dict(kind='SCCR_CP_learned_prefix',origin_native=a,executed_native=5,request=request,proposal_token=proposal['token'],actual_applied_prefix_sha256=digest(applied)))
  sampler.capture(r);ss=proof(r,[[0.,0.,False]for _ in range(2200)],'segment_stop',2)
  for i in range(2200):
   move(ss,i,[0.,0.,False],'FILTER_SEGMENT_COMPLETE_STOP')
   if v.count%5==0:evidence.update(observation.scan_only(v.scan(),v.count,float(v.d.time)))
  save('cycle_000002_executed.json',dict(kind='SCCR_CP_component_stop',origin_native=10,executed_native=2200));assert binding['old'].previous.stopped(binding['packet'](v))and sampler.frames==3 and controller.proposals==controller.commits==2 and controller.pending is None
 finally:
  controller.close();sampler.close()
 return dict(passed=True,component_complete_original_stop=True,actual_sensor_frames=3,actual_depth_feature_dimensions=24,actual_complete_186_observation_frames=3,explicit_learned_policy_calls=6,explicit_actor_constructors=2,original_noise_profile_preserved=True,learned_control_prefixes=2,controller_identity='SCCR_CP_SHARED_ROUTE_V1',native_original_environment_equivalent=False,explicit_common_command_projection=True,upstream_detour_replaced_by_shared_public_route=True,policy_outputs_never_actuated=False,factory_internal_policy_calls=None,whole_goal_with_original_stop=False,actual_original_goal_reached=False,complete_zero_stop_native=2200,actual_native=v.count,normal_native=10,formal_trial=False,native_optimizer_queries=0,full186_or_original_SCCR_qualified=False)
