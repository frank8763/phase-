"""One fresh profile;24 current-proof prefixes and original2200stop. Not arrival."""
import math
from context import R,C,read,load,digest,sha

def run(v,binding,task,source,out,save,quota,refresh):
 q=binding['q'];np=q.np;setup=read(out/'physics/SETUP.json');goal=np.asarray(task['goal_xy']);observation=load('CP_unchanged_observation',C/'observation.py');response=load('CP_unchanged_full_response',C/'response.py');causal=load('CP_original_causal_tracker',R/'experiments/v1024_full_route_execution/causal.py');evidence=causal.Evidence(setup['known']);cursor_mod=load('CP_committed_profile_cursor',R/'experiments/v2179_current_plan_cursor/cursor.py');controller=cursor_mod.Cursor(task['run_id']);client=None;nonzero=0
 def current(cycle):
  z=observation.scan_only(v.scan(),v.count,float(v.d.time));evidence.update(z);r=observation.acquire(v,binding,z);save(f'cycle_{cycle:06d}_origin.json',dict(origin_native=v.count,receipt=r));return r
 def proof(r,requests,label,cycle):
  p=r['packet'];cs=None if evidence.first is None else evidence.source(v);z,ss,uu,mm=response.prove(q,setup,p,requests,goal,cs);z.update(origin_packet_sha256=digest(p),receipt=r,executed_native=0,arrays=f'cycle_{cycle:06d}_{label}.npz');z['hybrid_evidence']=binding['predictive_arrays'].persist(z,dict(states=ss,controls=uu,memory=mm,requests=np.asarray(requests,float)));save(f'cycle_{cycle:06d}_{label}.json',z);assert z['passed'],'PROJECTION_CP_ORIGINAL_FULL_RESPONSE_REFUSED';return z,ss
 def move(ss,i,request,phase):
  v.adapter.parked_target=None;v._chain_phase=phase;before=v.count;v.step(*request);assert v.count==before+1
  e=np.asarray(q.initial(binding['packet'](v))['state'])-ss[i+1]
  assert np.linalg.norm(e[:2])<=.04 and abs(math.atan2(math.sin(e[2]),math.cos(e[2])))<=.035 and abs(e[6])<=.015,'PROJECTION_CP_ORIGINAL_TRACKING_REFUSED'
 try:
  r0=current(0);initial=np.asarray(r0['packet']['body'][:2]);from client_once import Client
  client=Client(save,r0,task);profile=client.query();save('PROJECTION_PROFILE.json',profile)
  # New actual body/steer/memory acquisition after solve, reusing the SAME
  # current native0 scan; no duplicate sensor sampling or clock/state reset.
  r=observation.acquire(v,binding,r0['scan']);save('PROJECTION_POST_SOLVE_ORIGIN.json',r);controller.install(profile,r0,r)
  for cycle in range(24):
   quota.retire_grant();refresh('STOPPED_EVENT_PREPARATION')
   proposal=controller.propose(r);save(f'PROJECTION_{cycle:06d}_PROPOSAL.json',proposal)
   contract=load('CP_original_command_domain',R/'experiments/v1288_baseline_interface/contract.py')
   for request in proposal['shadow_requests']:contract.twist(*request[:2])
   shadow,ss_shadow=proof(r,proposal['shadow_requests']+[[0.,0.,False]for _ in range(2200)],'shadow',cycle)
   admission,ss=proof(r,proposal['requests']+[[0.,0.,False]for _ in range(2200)],'admission_0',cycle)
   leases=[]
   for label,z,head in [('shadow',shadow,proposal['shadow_requests']),('admission',admission,proposal['requests'])]:leases.append(dict(label=label,origin_packet_sha256=z['origin_packet_sha256'],requests_sha256=digest(head+[[0.,0.,False]for _ in range(2200)]),native=z['native'],passed=z['passed'],checks=z['checks'],arrays_sha256=digest(z['hybrid_evidence'])))
   controller.verify_response(proposal['token'],leases);save(f'PROJECTION_{cycle:06d}_MODEL_BINDING.json',leases);a=v.count
   for i,request in enumerate(proposal['requests']):move(ss,i,request,'FILTER_RECEDING_CURRENT');nonzero+=int(abs(request[0])>=.005)
   applied=[]
   for i,row in enumerate(v.commands[a:a+5]):
    actual=[row[1],row[2],row[5]];assert actual==proposal['requests'][i];applied.append(dict(episode_id=task['run_id'],before_native=a+i,request=actual,applied=True))
   assert len(applied)==5 and a==cycle*5;r=current(cycle+1);committed=controller.commit(proposal['token'],r,applied);save(f'PROJECTION_COMMIT_{v.count:06d}.json',committed)
   save(f'cycle_{cycle:06d}_executed.json',dict(kind='fresh_projection_committed_prefix',origin_native=a,executed_native=5,proposal_token=proposal['token'],actual_applied_prefix_sha256=digest(applied)))
  end=np.asarray(r['packet']['body'][:2]);progress=float(np.linalg.norm(end-initial));save('PROJECTION_NORMAL_RESPONSE.json',dict(normal_native=120,nonzero_requested_native=nonzero,body_displacement_m=progress,component_not_whole_goal=True))
  assert controller.expected==120 and controller.commits==24 and controller.pending is None and nonzero>0 and progress>1e-6,'PROJECTION_CP_NO_MEASURABLE_NONZERO_RESPONSE'
  quota.retire_grant();refresh('STOPPED_EVENT_PREPARATION');z,ss=proof(r,[[0.,0.,False]for _ in range(2200)],'segment_stop',24)
  for i in range(2200):
   move(ss,i,[0.,0.,False],'FILTER_SEGMENT_COMPLETE_STOP')
   if v.count%5==0:evidence.update(observation.scan_only(v.scan(),v.count,float(v.d.time)))
  save('cycle_000024_executed.json',dict(kind='projection_component_stop',origin_native=120,executed_native=2200));assert binding['old'].previous.stopped(binding['packet'](v))and v.count==2320
 finally:
  controller.close()
  if client is not None:client.close()
 return dict(passed=True,component_complete_original_stop=True,controller_identity='ORIENTATION_PROJECTION_CP_V1',native_author_PRIEST=False,whole_goal_with_original_stop=False,actual_original_goal_reached=False,complete_zero_stop_native=2200,actual_native=v.count,normal_native=120,nonzero_requested_native=nonzero,normal_body_displacement_m=progress,native_optimizer_queries=1,NLP_returns=1,internal_optimizer_work=None,formal_trial=False,monotonic_committed_plan=True,profile_replans=0)
