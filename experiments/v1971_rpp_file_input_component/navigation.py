"""Fresh exposed-course one-command RPP current interface and full physical stop."""
import copy,math,sys,concurrent.futures,os
from context import R,C,O,read,load,digest,sha

def run(v,binding,task,source,out,save,quota,refresh):
 q=binding['q'];np=q.np;setup=read(out/'physics/SETUP.json');goal=np.asarray(task['goal_xy'],float)
 observation=load('RPP_current_observation',C/'observation.py');response=load('RPP_original_response',C/'response.py');causal=load('RPP_original_causal_evidence',R/'experiments/v1024_full_route_execution/causal.py');evidence=causal.Evidence(setup['known']);last_scan=None;active=None
 def scan():
  nonlocal last_scan
  z=observation.scan_only(v.scan(),v.count,float(v.d.time))
  if last_scan is None or z['native_tick']>last_scan['native_tick']:evidence.update(z)
  last_scan=z;return z
 def proof_for(receipt,requests,label):
  p=receipt['packet'];causal_source=None if evidence.first is None else evidence.source(v);proof,ss,uu,mm=response.prove(q,setup,p,requests,goal,causal_source);proof.update(origin_packet_sha256=digest(p),receipt=receipt,executed_native=0,arrays='cycle_0000_'+label+'.npz');proof['hybrid_evidence']=binding['predictive_arrays'].persist(proof,dict(states=ss,controls=uu,memory=mm,requests=np.asarray(requests,float)));save('cycle_0000_'+label+'.json',proof);return proof,ss
 def move(request,predicted,index,phase):
  v.adapter.parked_target=None;v._chain_phase=phase;v.step(*request);p=binding['packet'](v);s=np.asarray(q.initial(p)['state']);delta=s-predicted[index+1];error=[float(np.linalg.norm(delta[:2])),abs(math.atan2(math.sin(delta[2]),math.cos(delta[2]))),abs(float(delta[6]))];assert np.all(np.asarray(error)<=[.04,.035,.015]),'RPP_CURRENT_ACTUAL_TRACKING_REFUSED'
  if v.count%5==0:scan()
 scan();receipt=observation.acquire(v,binding,last_scan);p=receipt['packet'];save('cycle_0000_origin.json',dict(cycle=0,origin_native=0,receipt=receipt));assert v.count==0
 # Public full-footprint nominal frontend, independent puremath on CPU4 only.
 before_path=sys.path[:]
 try:route=load('RPP_original_nominal_route_frontend',R/'experiments/v1370_overnight_controller_matrix/observed_route.py')
 finally:sys.path[:]=before_path
 def plan():
  os.sched_setaffinity(0,{4});path,report=route.propose(setup['known'],p['body'],task['goal_xy'],None,guard=.22);return path,report
 with concurrent.futures.ThreadPoolExecutor(max_workers=1)as pool:path,report=pool.submit(plan).result(timeout=30)
 save('RPP_CURRENT_NOMINAL_ROUTE.json',dict(path=None if path is None else path.tolist(),report=report,origin_packet_sha256=digest(p),public_geometry_only=True,cpu=4));assert path is not None,'RPP_NOMINAL_PATH_NOT_FOUND'
 valid,validation=route.revalidate(setup['known'],path,p['body'],None,guard=.22);save('RPP_INITIAL_PATH_VALIDATION.json',validation);assert valid,'RPP_CURRENT_PATH_REVALIDATION_REFUSED'
 before=sys.path[:];sys.path.insert(0,str(R/'experiments/v1370_overnight_controller_matrix'))
 try:segments=load('RPP_original_singlegear_segments',R/'experiments/v1370_overnight_controller_matrix/segments.py');pieces=segments.split(path)
 finally:sys.path[:]=before
 selected=pieces[0];poses=selected['poses'];save('RPP_SELECTED_SEGMENT.json',selected)
 wire_module=load('RPP_current_causal_wire',R/'experiments/v1938_current_causal_solver_wire/wire.py');wire=wire_module.CurrentWire(source,run_id=task['run_id'],method='RPP');request=wire.request(receipt,goal_xy=task['goal_xy'],public_route=[p[:2]for p in poses]);save('RPP_CURRENT_SOLVER_REQUEST.json',request)
 front=load('RPP_causal_current_costmap',R/'experiments/v1966_rpp_current_interface/current_map.py');frontend=front.Frontend(np,public_sha256=source[str(front.PUBLIC.relative_to(R))],parameter_sha256=source[str(front.PARAMS.relative_to(R))]);costmap=frontend.build(request);save('RPP_CURRENT_COSTMAP.json',costmap)
 client_class=load('RPP_serial_native_client',C/'native_client.py').Client;client=None
 try:
  client=client_class(save,request,costmap,poses);answer=client.query(request,costmap,poses);assert answer['passed']and answer['origin_native_tick']==0 and answer['input_sha256']==digest(request),'RPP_CURRENT_NATIVE_OUTPUT_REFUSED'
  vr,wr=answer['twist'];assert all(math.isfinite(x)for x in [vr,wr])and abs(vr)<=.1 and abs(wr)<=abs(vr)/1.32+1e-12,'RPP_RAW_COMMAND_DOMAIN_REFUSED';assert segments.direction_allowed(vr,selected['gear']),'RPP_RAW_COMMAND_GEAR_REFUSED'
  now=__import__('time').monotonic();reply=dict(schema='PHASE_CURRENT_SOLVER_REPLY_V1',run_id=task['run_id'],method='RPP',origin_native_tick=0,input_sha256=digest(request),sequence=0,issued_at=now,v=vr,w=wr);current=wire.reply(reply,now=now);save('RPP_CURRENT_WIRE_REPLY.json',dict(reply=reply,validated=current));raw=[float(vr),float(wr),False]
 finally:
  if client is not None:client.close()
 full=[raw.copy()for _ in range(10)]+[[0.,0.,False]for _ in range(2200)];proof,shadow=proof_for(receipt,full,'shadow');assert proof['passed'],'RPP_CURRENT_CYCLE_COMPLETE_STOP_REFUSED'
 for offset in [0,5]:
  current=receipt if offset==0 else observation.acquire(v,binding,last_scan);one,ss=proof_for(current,[raw.copy()for _ in range(5)]+[[0.,0.,False]for _ in range(2200)],'admission_'+str(offset));assert one['passed'],'RPP_CURRENT_5_NATIVE_RETAINED_STOP_REFUSED'
  for i in range(5):move(raw,ss,i,'RPP_RECEDING_CURRENT')
 for i in range(10,2210):move([0.,0.,False],shadow,i,'RPP_INTERFACE_COMPLETE_STOP')
 final=binding['packet'](v);assert binding['old'].previous.stopped(final);assert v.count==2210;save('WHITELIST_CAUSAL_OBSERVATIONS.json',evidence.snapshots);save('RPP_INTERFACE_EXECUTED.json',dict(passed=True,normal_native=10,complete_stop_native=2200,raw_request=raw,first_discovery=None if evidence.first is None else evidence.first['native_tick'],component_not_whole_navigation=True))
 return dict(passed=True,current_interface_component=True,actual_original_goal_reached=False,whole_goal_with_original_stop=False,complete_zero_stop_native=2200,actual_native=v.count,reference_counts=dict(native_RPP_queries=1,raw_command=raw,internal_native_work=None),original_goal_distance_m=math.dist(final['body'][:2],task['goal_xy']),formal_trial=False)
