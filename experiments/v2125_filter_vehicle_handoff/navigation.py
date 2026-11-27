"""One live FILTER preview; original10+2200/5+2200 and fresh2200 stop."""
import concurrent.futures,math,os,sys
from context import R,C,read,load,digest

def run(v,binding,task,source,out,save,quota,refresh):
 q=binding['q'];np=q.np;setup=read(out/'physics/SETUP.json');assert setup['known']==read(R/'experiments/v855_renewal_worker/KNOWN_FIELD.json');goal=np.asarray(task['goal_xy']);observation=load('FILTER_original_observation',C/'observation.py');response=load('FILTER_original_full_response',C/'response.py');causal=load('FILTER_original_causal_tracker',R/'experiments/v1024_full_route_execution/causal.py');evidence=causal.Evidence(setup['known'])
 def scan():
  z=observation.scan_only(v.scan(),v.count,float(v.d.time));evidence.update(z);return z
 last=scan();receipt=observation.acquire(v,binding,last);p=receipt['packet'];assert v.count==0 and not p['dynamic_discovered']
 save('cycle_000000_origin.json',dict(origin_native=0,receipt=receipt))
 before=sys.path[:];sys.path.insert(0,str(R/'experiments/v1370_overnight_controller_matrix'))
 try:
  route=load('observed_route',R/'experiments/v1370_overnight_controller_matrix/observed_route.py');segments=load('FILTER_shared_singlegear_segments',R/'experiments/v1370_overnight_controller_matrix/segments.py')
 finally:sys.path[:]=before
 def geometry():os.sched_setaffinity(0,{4});return route.propose(setup['known'],p['body'],task['goal_xy'],None,guard=.22)
 with concurrent.futures.ThreadPoolExecutor(max_workers=1)as pool:path,report=pool.submit(geometry).result(timeout=30)
 save('FILTER_NOMINAL_ROUTE.json',dict(path=None if path is None else path.tolist(),report=report));assert path is not None,'FILTER_NOMINAL_PATH_NOT_FOUND'
 valid,validation=route.revalidate(setup['known'],path,p['body'],None,guard=.22);save('FILTER_ROUTE_VALIDATION.json',validation);assert valid,'FILTER_CURRENT_PATH_REVALIDATION_REFUSED';selected=segments.split(path)[0];assert selected['gear']==1,'FILTER_FIRST_FORWARD_COMPONENT_REQUIRED';save('FILTER_SELECTED_SEGMENT.json',selected)
 with np.load(out/'INITIAL_FULL_STATE.npz')as z:full={k:z[k].tolist()for k in z.files}
 frame=load('FILTER_fresh_whitelist_request',C/'current_request.py').build(np,receipt,full,selected,source,run_id=task['run_id']);save('FILTER_CURRENT_INPUT.json',frame['current']);save('FILTER_OPTIMIZER_REQUEST.json',frame['request'])
 quota.admit(2*1024**2,'FILTER_NATIVE_AND_COMPLETE_PREDICTIONS_HEADROOM')
 answer=load('FILTER_CPU6_optimizer_client',C/'native_client.py').solve(frame,save);proposal=answer['proposal'];save('FILTER_RAW_CURRENT_PROPOSAL.json',proposal);raw=proposal['raw_request'];assert not proposal['actual_execution_permitted']
 def proof_for(receipt,requests,label,cycle):
  p=receipt['packet'];cs=None if evidence.first is None else evidence.source(v);proof,ss,uu,mm=response.prove(q,setup,p,requests,goal,cs);proof.update(origin_packet_sha256=digest(p),receipt=receipt,executed_native=0,arrays=f'cycle_{cycle:06d}_{label}.npz');proof['hybrid_evidence']=binding['predictive_arrays'].persist(proof,dict(states=ss,controls=uu,memory=mm,requests=np.asarray(requests,float)));save(f'cycle_{cycle:06d}_{label}.json',proof);return proof,ss
 def move(request,ss,i,phase):
  v.adapter.parked_target=None;v._chain_phase=phase;v.step(*request);actual=np.asarray(q.initial(binding['packet'](v))['state']);e=actual-ss[i+1]
  assert np.linalg.norm(e[:2])<=.04 and abs(math.atan2(math.sin(e[2]),math.cos(e[2])))<=.035 and abs(e[6])<=.015,'FILTER_ACTUAL_RESPONSE_TRACKING_REFUSED'
 shadow,_=proof_for(receipt,[raw.copy()for _ in range(10)]+[[0.,0.,False]for _ in range(2200)],'shadow',0);assert shadow['passed'],'FILTER_CURRENT_CYCLE_COMPLETE_STOP_REFUSED'
 admission,ss=proof_for(receipt,[raw.copy()for _ in range(5)]+[[0.,0.,False]for _ in range(2200)],'admission_0',0);assert admission['passed'],'FILTER_CURRENT_5_PLUS2200_REFUSED'
 for i in range(5):move(raw,ss,i,'FILTER_RECEDING_CURRENT')
 save('cycle_000000_executed.json',dict(kind='FILTER_control_cycle',origin_native=0,executed_native=5))
 last=scan();receipt=observation.acquire(v,binding,last);save('cycle_000001_origin.json',dict(origin_native=5,receipt=receipt));requests=[[0.,0.,False]for _ in range(2200)];proof,ss=proof_for(receipt,requests,'segment_stop',1);assert proof['passed'],'FILTER_CURRENT_MEASURED_COMPLETE_STOP_REFUSED'
 for i,request in enumerate(requests):
  move(request,ss,i,'FILTER_SEGMENT_COMPLETE_STOP')
  if v.count%5==0:scan()
 save('cycle_000001_executed.json',dict(kind='component_stop',origin_native=5,executed_native=2200));assert binding['old'].previous.stopped(binding['packet'](v))
 return dict(passed=True,component_complete_original_stop=True,whole_goal_with_original_stop=False,actual_original_goal_reached=False,complete_zero_stop_native=2200,actual_native=v.count,normal_native=5,formal_trial=False,native_optimizer_queries=1,internal_optimizer_work=None)
