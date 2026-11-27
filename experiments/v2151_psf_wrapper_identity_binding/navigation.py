"""One exposed full-route attempt; measured gear handoffs, unchanged PSF/gates."""
import concurrent.futures,math,os,sys
from context import R,C,read,load,digest
MAX_QUERIES=2500;MAX_PLANS=12;MAX_SEGMENT_STOPS=12
def validate_current_route(np,route,known,selected,body):
 poses=np.asarray(selected['poses'],float);gear=selected['gear'];assert poses.ndim==2 and poses.shape[1]==3 and gear in[-1,1]
 return route.revalidate(known,np.column_stack([poses,np.full(len(poses),gear)]),body,None,guard=.22)
def endpoint(packet,selected):
 b=packet['body'];rear=[b[0]-.3*math.cos(b[2]),b[1]-.3*math.sin(b[2])];p=selected['poses'][-1]
 return math.dist(rear,p[:2])<=.08 and abs(math.atan2(math.sin(b[2]-p[2]),math.cos(b[2]-p[2])))<=.15
def run(v,binding,task,source,out,save,quota,refresh):
 q=binding['q'];np=q.np;setup=read(out/'physics/SETUP.json');goal=np.asarray(task['goal_xy']);assert setup['known']==read(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json')
 observation=load('FILTER_original_observation',C/'observation.py');response=load('FILTER_original_full_response',C/'response.py');causal=load('FILTER_original_causal_tracker',R/'experiments/v1024_full_route_execution/causal.py');evidence=causal.Evidence(setup['known'])
 before=sys.path[:];sys.path.insert(0,str(R/'experiments/v1370_overnight_controller_matrix'))
 try:
  route=load('observed_route',R/'experiments/v1370_overnight_controller_matrix/observed_route.py');segments=load('FILTER_shared_singlegear_segments',R/'experiments/v1370_overnight_controller_matrix/segments.py')
 finally:sys.path[:]=before
 last=None;receipt=None;origins=set();client=None;queries=0;normal=0;plans=[];plan_id=-1;segment_id=0;stops=0
 def scan():
  nonlocal last
  last=observation.scan_only(v.scan(),v.count,float(v.d.time));evidence.update(last);return last
 def acquire():
  nonlocal receipt
  if last is None or last['native_tick']!=v.count:scan()
  receipt=observation.acquire(v,binding,last)
  if v.count not in origins:save(f'cycle_{v.count:06d}_origin.json',dict(origin_native=v.count,receipt=receipt));origins.add(v.count)
  else:assert read(out/f'cycle_{v.count:06d}_origin.json')['receipt']==receipt
  return receipt
 def proof_for(requests,label):
  p=receipt['packet'];cs=None if evidence.first is None else evidence.source(v);proof,ss,uu,mm=response.prove(q,setup,p,requests,goal,cs)
  proof.update(origin_packet_sha256=digest(p),receipt=receipt,executed_native=0,arrays=f'cycle_{v.count:06d}_{label}.npz')
  proof['hybrid_evidence']=binding['predictive_arrays'].persist(proof,dict(states=ss,controls=uu,memory=mm,requests=np.asarray(requests,float)))
  name=f'cycle_{v.count:06d}_{label}.json';save(name,proof);return proof,ss,name
 def move(request,ss,i,phase):
  v.adapter.parked_target=None;v._chain_phase=phase;v.step(*request);actual=np.asarray(q.initial(binding['packet'](v))['state']);e=actual-ss[i+1]
  assert np.linalg.norm(e[:2])<=.04 and abs(math.atan2(math.sin(e[2]),math.cos(e[2])))<=.035 and abs(e[6])<=.015,'FILTER_ACTUAL_RESPONSE_TRACKING_REFUSED'
 def stopped(goal_stop=False):
  nonlocal stops
  origin=v.count;label='goal_stop'if goal_stop else'segment_stop';requests=[[0.,0.,False]for _ in range(2200)];proof,ss,name=proof_for(requests,label)
  assert proof['passed'],'FILTER_CURRENT_MEASURED_COMPLETE_STOP_REFUSED'
  if goal_stop:assert proof['original_whole_checks']['goal_upper'],'FILTER_ORIGINAL_WHOLE_GOAL_STOP_REFUSED'
  else:assert stops<MAX_SEGMENT_STOPS,'FILTER_SEGMENT_STOP_LIMIT';stops+=1
  for i,request in enumerate(requests):
   move(request,ss,i,'FILTER_ORIGINAL_GOAL_STOP'if goal_stop else'FILTER_SEGMENT_COMPLETE_STOP')
   if v.count%5==0:scan()
  save(f'cycle_{origin:06d}_executed.json',dict(kind='whole_goal_stop'if goal_stop else'segment_stop',origin_native=origin,executed_native=2200,proof=name))
  assert binding['old'].previous.stopped(binding['packet'](v))
 def plan():
  nonlocal plans,plan_id,segment_id
  assert len(plans)<MAX_PLANS,'FILTER_PUBLIC_ROUTE_PLAN_LIMIT'
  body=receipt['packet']['body']
  def geometry():os.sched_setaffinity(0,{4});return route.propose(setup['known'],body,task['goal_xy'],None,guard=.22)
  with concurrent.futures.ThreadPoolExecutor(max_workers=1)as pool:path,report=pool.submit(geometry).result(timeout=30)
  row=dict(origin_native=v.count,body=body,path=None if path is None else path.tolist(),report=report,public_static_planner_only=True)
  save(f'FILTER_PLAN_{len(plans):02d}_PROPOSAL.json',row);assert path is not None,'FILTER_NOMINAL_PATH_NOT_FOUND'
  valid,validation=route.revalidate(setup['known'],path,body,None,guard=.22);assert valid,'FILTER_CURRENT_PATH_REVALIDATION_REFUSED'
  selected=segments.split(path);plan_id=len(plans);segment_id=0;plans.append(selected);save(f'FILTER_PLAN_{plan_id:02d}.json',dict(**row,segments=selected,validation=validation))
 try:
  acquire();assert v.count==0 and not receipt['packet']['dynamic_discovered'];plan()
  while queries<MAX_QUERIES:
   assert v.count<=57800 and normal<=12500,'FILTER_PHYSICAL_NATIVE_LIMIT'
   if queries and queries%50==0:refresh('STOPPED_EVENT_PREPARATION')
   if receipt['packet']['native_tick']!=v.count:acquire()
   if math.dist(receipt['packet']['body'][:2],task['goal_xy'])<=.30:
    stopped(True);final=binding['packet'](v);distance=math.dist(final['body'][:2],task['goal_xy']);assert distance<=.45,'FILTER_ORIGINAL_ACTUAL_GOAL_DISTANCE_REFUSED'
    return dict(passed=True,component_complete_original_stop=True,whole_goal_with_original_stop=True,actual_original_goal_reached=True,whole_navigation_passed=True,complete_zero_stop_native=2200,actual_native=v.count,normal_native=normal,native_optimizer_queries=queries,continuous_current_queries=queries,plans=len(plans),segment_stops=stops,original_goal_distance_m=distance,formal_trial=False,exposed_development=True,internal_optimizer_work=None)
   selected=plans[plan_id][segment_id]
   if endpoint(receipt['packet'],selected):
    stopped();acquire();segment_id+=1
    if segment_id==len(plans[plan_id]):plan()
    else:
     ok,review=segments.validate(plans[plan_id][segment_id],receipt['packet']['body'],setup['known'],None,guard=.22);save(f'FILTER_HANDOFF_{stops:02d}.json',dict(plan=plan_id,segment=segment_id,origin_native=v.count,validation=review));assert ok,'FILTER_MEASURED_GEAR_HANDOFF_REFUSED'
    continue
   local=load('FILTER_measured_route_projection',C/'nominal.py').reanchor(receipt['packet'],selected)
   valid,validation=validate_current_route(np,route,setup['known'],local,receipt['packet']['body']);save(f'FILTER_QUERY_{queries:04d}_ROUTE.json',dict(selected=local,validation=validation,plan=plan_id,segment=segment_id));assert valid,'NOMINAL_CURRENT_ROUTE_REVALIDATION_REFUSED'
   cs=None if evidence.first is None else evidence.source(v);causal_request=None if cs is None else dict(source_native_tick=evidence.last_scan['native_tick'],source_sim_time=evidence.last_scan['time'],periodic=cs['periodic'])
   frame=load('FILTER_fresh_whitelist_request',C/'current_request.py').build(np,receipt,None,local,source,run_id=task['run_id'],causal=causal_request);save(f'FILTER_QUERY_{queries:04d}_INPUT.json',frame)
   quota.admit(2*1024**2,'FILTER_NATIVE_AND_COMPLETE_PREDICTIONS_HEADROOM')
   if client is None:client=load('FILTER_persistent_CPU6_client',C/'native_client.py').Client(save,frame);answer=client.query()
   else:answer=client.query(frame)
   index=queries;queries+=1;proposal=answer['proposal'];save(f'FILTER_QUERY_{index:04d}_PROPOSAL.json',proposal);assert proposal is not None,'FILTER_CURRENT_NUMERICAL_OR_HARD_GEOMETRY_REFUSED'
   raw=proposal['raw_request'];origin=v.count;assert proposal['origin_native']==origin and not proposal['actual_execution_permitted']
   shadow,_,_=proof_for([raw.copy()for _ in range(10)]+[[0.,0.,False]for _ in range(2200)],'shadow');assert shadow['passed'],'FILTER_CURRENT_CYCLE_COMPLETE_STOP_REFUSED'
   admission,ss,name=proof_for([raw.copy()for _ in range(5)]+[[0.,0.,False]for _ in range(2200)],'admission_0');assert admission['passed'],'FILTER_CURRENT_5_PLUS2200_REFUSED'
   for i in range(5):move(raw,ss,i,'FILTER_RECEDING_CURRENT')
   normal+=5;save(f'cycle_{origin:06d}_executed.json',dict(kind='FILTER_control_cycle',origin_native=origin,executed_native=5,query=index,proof=name))
   save('FILTER_CONTINUOUS_PROGRESS.json',dict(queries=queries,normal_native=normal,actual_native=v.count,plans=len(plans),segment_stops=stops,whole_navigation_passed=False,dynamic_discovered=evidence.first is not None))
  raise AssertionError('FILTER_CURRENT_QUERY_LIMIT_BEFORE_ORIGINAL_GOAL')
 finally:
  if client is not None:
   active=sys.exc_info()[0]is not None
   try:client.close()
   except BaseException as error:
    if not active:raise
    binding.setdefault('native_peer_secondary_errors',[]).append(dict(stage='PERSISTENT_FILTER_PEER_CLOSE',error=repr(error)))
