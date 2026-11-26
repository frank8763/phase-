"""Current SVG-MPPI every five native ticks; original complete-stop admission."""
import concurrent.futures,copy,math,os,sys,time
from context import SOURCE,R,C,O,read,load,digest

def run(v,binding,task,source,out,save,quota,refresh):
 q=binding['q'];np=q.np;setup=read(out/'physics/SETUP.json');goal=np.asarray(task['goal_xy'],float)
 observation=load('SVG_current_observation',C/'observation.py');response=load('SVG_original_response',C/'response.py')
 causal=load('SVG_original_causal_evidence',R/'experiments/v1024_full_route_execution/causal.py');evidence=causal.Evidence(setup['known']);last_scan=None;client=None;cycles=0;plans=0;pieces=[];segment_index=0;queries=0
 before=sys.path[:]
 try:
  sys.path.insert(0,str(R/'experiments/v1370_overnight_controller_matrix'))
  route=load('observed_route',R/'experiments/v1370_overnight_controller_matrix/observed_route.py');segments=load('SVG_original_singlegear_segments',R/'experiments/v1370_overnight_controller_matrix/segments.py')
 finally:sys.path[:]=before
 control=load('SVG_qualified_current_control',R/'experiments/v2054_svg_current_control_contract/interface.py').CurrentControl(source,run_id=task['run_id'])
 codec=load('SVG_compact_current_evidence',C/'compact_record.py')
 def scan():
  nonlocal last_scan
  z=observation.scan_only(v.scan(),v.count,float(v.d.time))
  if last_scan is None or z['native_tick']>last_scan['native_tick']:evidence.update(z)
  last_scan=z;return z
 def snapshot():save('NAVIGATION_PROGRESS.json',dict(actual_native=v.count,cycles=cycles,plans=plans,segment_index=segment_index,queries=queries,whole_navigation_passed=False,internal_native_work=None))
 def proof_for(receipt,requests,label,cycle):
  p=receipt['packet'];cs=None if evidence.first is None else evidence.source(v);proof,ss,uu,mm=response.prove(q,setup,p,requests,goal,cs)
  proof.update(origin_packet_sha256=digest(p),receipt=receipt,executed_native=0,arrays=f'cycle_{cycle:06d}_{label}.npz');proof['hybrid_evidence']=binding['predictive_arrays'].persist(proof,dict(states=ss,controls=uu,memory=mm,requests=np.asarray(requests,float)));save(f'cycle_{cycle:06d}_{label}.json',proof);return proof,ss
 def move(request,predicted,index,phase):
  v.adapter.parked_target=None;v._chain_phase=phase;v.step(*request);p=binding['packet'](v);s=np.asarray(q.initial(p)['state']);delta=s-predicted[index+1]
  error=[float(np.linalg.norm(delta[:2])),abs(math.atan2(math.sin(delta[2]),math.cos(delta[2]))),abs(float(delta[6]))];assert np.all(np.asarray(error)<=[.04,.035,.015]),'SVG_CURRENT_ACTUAL_TRACKING_REFUSED'
  if v.count%5==0:scan()
 def plan(p):
  nonlocal plans,pieces,segment_index
  assert plans<12,'SVG_REGISTERED_PLAN_LIMIT';assert binding['old'].previous.stopped(p),'SVG_PLANNING_REQUIRES_MEASURED_REST'
  def geometry():
   os.sched_setaffinity(0,{4});return route.propose(setup['known'],p['body'],task['goal_xy'],None,guard=.22)
  with concurrent.futures.ThreadPoolExecutor(max_workers=1)as pool:path,report=pool.submit(geometry).result(timeout=30)
  index=plans;plans+=1;save(f'plan_{index:02d}_nominal.json',dict(path=None if path is None else path.tolist(),report=report,origin_packet_sha256=digest(p),public_geometry_only=True,cpu=4));assert path is not None,'SVG_NOMINAL_PATH_NOT_FOUND'
  valid,validation=route.revalidate(setup['known'],path,p['body'],None,guard=.22);save(f'plan_{index:02d}_validation.json',validation);assert valid,'SVG_CURRENT_PATH_REVALIDATION_REFUSED'
  pieces=segments.split(path);segment_index=0;save(f'plan_{index:02d}_segments.json',pieces)
 def endpoint(p,selected):
  rear=[p['body'][0]-.3*math.cos(p['body'][2]),p['body'][1]-.3*math.sin(p['body'][2])];end=selected['poses'][-1]
  return math.dist(rear,end[:2])<=.12 and abs(math.atan2(math.sin(p['body'][2]-end[2]),math.cos(p['body'][2]-end[2])))<=.20
 scan()
 try:
  while True:
   refresh('STOPPED_EVENT_PREPARATION');receipt=observation.acquire(v,binding,last_scan);p=receipt['packet'];cycle=cycles;cycles+=1
   save(f'cycle_{cycle:06d}_origin.json',dict(cycle=cycle,origin_native=v.count,receipt=receipt));snapshot();distance=math.dist(p['body'][:2],task['goal_xy'])
   whole=distance<=.37
   selected=pieces[segment_index]if pieces else None
   reached=selected is not None and endpoint(p,selected)
   if whole or reached:
    quota.admit(2*1024**2,'SVG_COMPLETE_STOP_EVIDENCE_HEADROOM')
    requests=[[0.,0.,False]for _ in range(2200)];label='goal_stop'if whole else'segment_stop';proof,ss=proof_for(receipt,requests,label,cycle)
    assert proof['passed'],'SVG_ORIGINAL_COMPLETE_STOP_REFUSED'
    if whole:assert proof['original_whole_checks']['goal_upper'],'SVG_ORIGINAL_WHOLE_GOAL_STOP_REFUSED'
    assert v.count+2200<=task['maximum_control_native']+2200,'SVG_STOP_TOTAL_LIMIT'
    for i,request in enumerate(requests):move(request,ss,i,'SVG_ORIGINAL_GOAL_STOP'if whole else'SVG_SEGMENT_COMPLETE_STOP')
    save(f'cycle_{cycle:06d}_executed.json',dict(kind='whole_goal_stop'if whole else'segment_stop',origin_native=p['native_tick'],executed_native=2200,proof=f'cycle_{cycle:06d}_{label}.json'));snapshot();final=binding['packet'](v);assert binding['old'].previous.stopped(final)
    if whole:
     assert math.dist(final['body'][:2],task['goal_xy'])<=.45,'SVG_ACTUAL_WHOLE_GOAL_NOT_REACHED';save('WHITELIST_CAUSAL_OBSERVATIONS.json',evidence.snapshots)
     return dict(passed=True,actual_original_goal_reached=True,whole_goal_with_original_stop=True,complete_zero_stop_native=2200,actual_native=v.count,reference_counts=dict(native_SVG_queries=queries,constructors=1,nominal_plans=plans,internal_native_work=None),original_goal_distance_m=math.dist(final['body'][:2],task['goal_xy']),formal_trial=True)
    segment_index+=1
    if segment_index>=len(pieces):plan(final)
    else:
     valid,validation=segments.validate(pieces[segment_index],final['body'],setup['known'],None,guard=.22);save(f'cycle_{cycle:06d}_next_segment.json',validation);assert valid,'SVG_MEASURED_CUSP_CAPTURE_REFUSED'
    continue
   assert v.count+5<=task['maximum_control_native'],'SVG_NATIVE_LIMIT_NO_WHOLE_GOAL'
   if selected is None:plan(p);selected=pieces[segment_index]
   quota.admit(2*1024**2,'SVG_CURRENT_QUERY_AND_TWO_COMPLETE_PROOFS_HEADROOM')
   poses=selected['poses'];frame=control.frame(np,receipt,goal_xy=task['goal_xy'],rear_path=poses,gear=selected['gear'])
   save(f'cycle_{cycle:06d}_selection.json',dict(plan_index=plans-1,segment_index=segment_index,selected_segment_sha256=digest(selected)))
   if client is None:client=load('SVG_persistent_native_client',C/'native_client.py').Client(save,frame);answer=client.query()
   else:answer=client.query(frame)
   # Retain raw output and the exact input recipe before applying any proposal
   # domain or response gate. No dense transport map is persisted each cycle.
   record=codec.pack(cycle=queries,receipt=receipt,selected=selected,frame=frame,reply=answer,source_freeze_sha256=__import__('context').sha(SOURCE/'SOURCE_FREEZE.json'))
   save(f'cycle_{cycle:06d}_query.json',record);queries+=1
   assert answer['passed']and answer['counts']['constructor_returns']==1 and answer['counts']['author_solve_attempts']==answer['counts']['author_solve_returns']==queries,'SVG_CURRENT_NATIVE_OUTPUT_REFUSED'
   current=control.proposal(answer['raw'],now=time.monotonic());save(f'cycle_{cycle:06d}_proposal.json',current);raw=current['body_request']
   assert current['physical_authority']is False and current['actual_execution_permitted']is False
   full,_=proof_for(receipt,[raw.copy()for _ in range(10)]+[[0.,0.,False]for _ in range(2200)],'shadow',cycle)
   assert full['passed'],'SVG_CURRENT_CYCLE_COMPLETE_STOP_REFUSED'
   proof,ss=proof_for(receipt,[raw.copy()for _ in range(5)]+[[0.,0.,False]for _ in range(2200)],'admission_0',cycle)
   assert proof['passed'],'SVG_CURRENT_5_NATIVE_RETAINED_STOP_REFUSED'
   for i in range(5):move(raw,ss,i,'SVG_RECEDING_CURRENT')
   save(f'cycle_{cycle:06d}_executed.json',dict(kind='SVG_control_cycle',origin_native=p['native_tick'],executed_native=5,proof=f'cycle_{cycle:06d}_admission_0.json'));snapshot()
 finally:
  control.close()
  if client is not None:
   primary=sys.exc_info()[1]
   try:client.close()
   except BaseException as e:
    failure=dict(stage='SVG_NATIVE_PEER_CLOSE',error=repr(e));save('SVG_NATIVE_SECONDARY_CLOSE_ERROR.json',failure);binding.setdefault('native_peer_secondary_errors',[]).append(failure)
    if primary is None:raise
