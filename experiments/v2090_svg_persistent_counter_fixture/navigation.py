"""One fresh SVG command, original measured5+2200 gates and full physical stop."""
import copy,math,sys,concurrent.futures,os
from context import R,C,O,read,load,digest,sha

def run(v,binding,task,source,out,save,quota,refresh):
 cycle=0;q=binding['q'];np=q.np;setup=read(out/'physics/SETUP.json');goal=np.asarray(task['goal_xy'],float)
 observation=load('SVG_current_observation',C/'observation.py');response=load('SVG_original_response',C/'response.py');causal=load('SVG_original_causal_evidence',R/'experiments/v1024_full_route_execution/causal.py');evidence=causal.Evidence(setup['known']);last_scan=None;active=None
 def scan():
  nonlocal last_scan
  z=observation.scan_only(v.scan(),v.count,float(v.d.time))
  if last_scan is None or z['native_tick']>last_scan['native_tick']:evidence.update(z)
  last_scan=z;return z
 def proof_for(receipt,requests,label):
  p=receipt['packet'];causal_source=None if evidence.first is None else evidence.source(v);proof,ss,uu,mm=response.prove(q,setup,p,requests,goal,causal_source);proof.update(origin_packet_sha256=digest(p),receipt=receipt,executed_native=0,arrays=f'cycle_{cycle:04d}_'+label+'.npz');proof['hybrid_evidence']=binding['predictive_arrays'].persist(proof,dict(states=ss,controls=uu,memory=mm,requests=np.asarray(requests,float)));save(f'cycle_{cycle:04d}_'+label+'.json',proof);return proof,ss
 def move(request,predicted,index,phase):
  v.adapter.parked_target=None;v._chain_phase=phase;v.step(*request);p=binding['packet'](v);s=np.asarray(q.initial(p)['state']);delta=s-predicted[index+1];error=[float(np.linalg.norm(delta[:2])),abs(math.atan2(math.sin(delta[2]),math.cos(delta[2]))),abs(float(delta[6]))];assert np.all(np.asarray(error)<=[.04,.035,.015]),'SVG_CURRENT_ACTUAL_TRACKING_REFUSED'
  if v.count%5==0:scan()
 scan();receipt=observation.acquire(v,binding,last_scan);p=receipt['packet'];save('cycle_0000_origin.json',dict(cycle=0,origin_native=0,receipt=receipt));assert v.count==0
 # Public full-footprint nominal frontend, independent puremath on CPU4 only.
 before_path=sys.path[:]
 try:route=load('SVG_original_nominal_route_frontend',R/'experiments/v1370_overnight_controller_matrix/observed_route.py')
 finally:sys.path[:]=before_path
 def plan():
  os.sched_setaffinity(0,{4});path,report=route.propose(setup['known'],p['body'],task['goal_xy'],None,guard=.22);return path,report
 with concurrent.futures.ThreadPoolExecutor(max_workers=1)as pool:path,report=pool.submit(plan).result(timeout=30)
 save('SVG_CURRENT_NOMINAL_ROUTE.json',dict(path=None if path is None else path.tolist(),report=report,origin_packet_sha256=digest(p),public_geometry_only=True,cpu=4));assert path is not None,'SVG_NOMINAL_PATH_NOT_FOUND'
 valid,validation=route.revalidate(setup['known'],path,p['body'],None,guard=.22);save('SVG_INITIAL_PATH_VALIDATION.json',validation);assert valid,'SVG_CURRENT_PATH_REVALIDATION_REFUSED'
 before=sys.path[:];sys.path.insert(0,str(R/'experiments/v1370_overnight_controller_matrix'))
 try:segments=load('SVG_original_singlegear_segments',R/'experiments/v1370_overnight_controller_matrix/segments.py');pieces=segments.split(path)
 finally:sys.path[:]=before
 selected=pieces[0];poses=selected['poses'];save('SVG_SELECTED_SEGMENT.json',selected)
 interface=load('SVG_qualified_current_control',R/'experiments/v2054_svg_current_control_contract/interface.py');control=interface.CurrentControl(source,run_id=task['run_id'])
 client_class=load('SVG_persistent_native_client',C/'native_client.py').Client;client=None;raw_commands=[];stop_prediction=None
 try:
  for cycle,offset in enumerate([0,5]):
   assert v.count==offset
   current_receipt=receipt if offset==0 else observation.acquire(v,binding,last_scan)
   if cycle:save(f'cycle_{cycle:04d}_origin.json',dict(cycle=cycle,origin_native=offset,receipt=current_receipt))
   frame=control.frame(np,current_receipt,goal_xy=task['goal_xy'],rear_path=poses,gear=selected['gear']);save(f'SVG_QUERY_{cycle}_FRAME.json',frame)
   if client is None:client=client_class(save,frame);answer=client.query()
   else:answer=client.query(frame)
   assert answer['passed'],'SVG_CURRENT_NATIVE_OUTPUT_REFUSED'
   current=control.proposal(answer['raw'],now=__import__('time').monotonic());save(f'SVG_QUERY_{cycle}_PROPOSAL.json',current);raw=current['body_request'];raw_commands.append(raw)
   assert current['physical_authority']is False and current['actual_execution_permitted']is False
   # Ten-step shadow is a safety gate for each newly measured command, never a
   # prediction of a future optimizer output. Each executed five has its own proof.
   shadow,_=proof_for(current_receipt,[raw.copy()for _ in range(10)]+[[0.,0.,False]for _ in range(2200)],'shadow')
   assert shadow['passed'],'SVG_CURRENT_CYCLE_COMPLETE_STOP_REFUSED'
   one,ss=proof_for(current_receipt,[raw.copy()for _ in range(5)]+[[0.,0.,False]for _ in range(2200)],'admission_'+str(offset))
   assert one['passed'],'SVG_CURRENT_5_NATIVE_RETAINED_STOP_REFUSED'
   for i in range(5):move(raw,ss,i,'SVG_RECEDING_CURRENT')
   stop_prediction=ss
  for i in range(5,2205):move([0.,0.,False],stop_prediction,i,'SVG_INTERFACE_COMPLETE_STOP')
 except BaseException:
  if client is not None:
   try:client.close()
   except BaseException as close_error:save('SVG_NATIVE_CLOSE_SECONDARY_ERROR.json',dict(stage='SVG_NATIVE_CLOSE',error=repr(close_error),traceback=__import__('traceback').format_exc()))
   client=None
  raise
 finally:
  control.close()
  if client is not None:client.close()
 final=binding['packet'](v);assert binding['old'].previous.stopped(final);assert v.count==2210
 save('WHITELIST_CAUSAL_OBSERVATIONS.json',evidence.snapshots)
 save('SVG_INTERFACE_EXECUTED.json',dict(passed=True,normal_native=10,complete_stop_native=2200,raw_requests=raw_commands,current_queries=2,one_persistent_optimizer=True,first_discovery=None if evidence.first is None else evidence.first['native_tick'],component_not_whole_navigation=True))
 return dict(passed=True,current_interface_component=True,persistent_two_current_queries=True,actual_original_goal_reached=False,whole_goal_with_original_stop=False,complete_zero_stop_native=2200,actual_native=v.count,reference_counts=dict(native_SVG_queries=2,raw_commands=raw_commands,internal_native_work=None),original_goal_distance_m=math.dist(final['body'][:2],task['goal_xy']),formal_trial=False)
