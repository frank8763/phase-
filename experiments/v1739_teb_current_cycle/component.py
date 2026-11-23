"""Fresh measured-origin author solve, original response proof, actual feedback."""
import copy,math,time,sys
from context import C,O,R,read,load,sha,digest

def run(v,binding,task,source,out,save,quota,measured_origin):
 q=binding['q'];np=q.np;packet=binding['packet'];setup=read(out/'physics/SETUP.json')
 bridge=load('v1670_measured_Phase_bridge',R/'experiments/v1665_svg_phase_vehicle_contract/bridge.py')
 causal=load('v1670_original_whitelist_evidence',R/'experiments/v1024_full_route_execution/causal.py');evidence=causal.Evidence(setup['known'])
 p0=copy.deepcopy(measured_origin);assert p0['native_tick']==0 and p0['sim_time']==0.
 assert not evidence.update(v.scan()),'TEB_COMPONENT_DYNAMIC_VISIBLE_AT_T0'
 origin=bridge.decode(p0,expected_native=0,expected_sim_time=0.,expected_packet_sha256=bridge.digest(p0))
 config=read(O/'TEB_CONFIG.json')
 points=load('v1739_current_public_obstacles',C/'obstacles.py').make(setup['known'])
 frames=load('v1739_rear_axle_mapping',C/'frames.py')
 receipt=frames.observation_receipt(read(out/'CURRENT_MEASURED_ORIGIN.json'),v.scan())
 wire=frames.encode(receipt,[*task['goal_xy'],task['goal_yaw']],points,config)
 save('TEB_CURRENT_RECEIPT.json',receipt)
 save('CURRENT_SOLVER_INPUT.json',dict(origin=origin,config=config,public_obstacle_points=points,wire=wire,physical_packet_not_historical=True,pointcost_not_footprintcertificate=True))
 client=load('v1739_readonly_original_TEB_query',C/'client.py')
 raw=client.query(wire,source,out,save)
 assert raw['passed'],'TEB_NATIVE_ORIGINAL_QUERY_REFUSED'
 selected=raw['proposal'];mapped=frames.command(selected,config);trajectory=frames.trajectory(selected,config)
 body_request=mapped['body_request'];delta=mapped['virtual_steering']
 decoded=bridge.request(delta,longitudinal_speed=body_request[0],declared_gear=mapped['gear'],origin=origin,expected_origin_sha256=bridge.digest(p0))['body_request']
 assert abs(decoded[1]-body_request[1])<=1e-15
 dwa_counts=raw['counts']
 save('TEB_SELECTED_CURRENT_PROPOSAL.json',dict(command=body_request[:2],virtual_steering=delta,rear_trajectory=selected['trajectory'],reference_trajectory_body_centre=trajectory,counts=dwa_counts,source_packet=p0,receipt_sha256=digest(receipt),raw_optimizer_proposal_retained=True,original_ROS_saturation_explicit_port=mapped,reference_cost_not_stopcertificate=True))
 requests=[body_request.copy()for _ in range(10)]+[[0.,0.,False]for _ in range(2200)];assert len(requests)==2210
 geometry=sys.modules['kernel'].ref._old.Geometry(setup['known'],None);required=float(sys.modules['kernel'].REQUIRED)
 counts=dict(Predictor_constructor_attempts=0,Predictor_constructor_returns=0,Python_step_attempts=0,Python_step_returns=0,step_inflight_unknown=False,total_modelwork=None)
 def prove(p,rr):
  save('TEB_RESPONSE_ACCOUNTING.json',counts)
  counts['Predictor_constructor_attempts']+=1
  current=dict(q.initial(p),steering_load_episode=False);pred=q.model.Predictor(setup,current);counts['Predictor_constructor_returns']+=1
  ss=[pred.state.copy()];uu=[];mm=[np.r_[pred.adapter.last,pred.adapter.integral]]
  for vr,wr,stale in rr:
   counts['Python_step_attempts']+=1;counts['step_inflight_unknown']=True
   s,u=pred.step(vr,wr,stale);counts['Python_step_returns']+=1;counts['step_inflight_unknown']=False
   ss.append(s.copy());uu.append(u.copy());mm.append(np.r_[pred.adapter.last,pred.adapter.integral])
  ss=np.asarray(ss);uu=np.asarray(uu);mm=np.asarray(mm);minimum=float(geometry.clearances(ss[:,:3])[0].min())
  original,upper=q.helper.checks(ss,uu,np.asarray(rr,float),p,setup,np.asarray(task['goal_xy']),minimum,required)
  checks={k:bool(value)for k,value in original.items()if k!='goal_upper'}
  checks.update(full2200=bool(len(rr)>=2200 and np.array_equal(np.asarray(rr[-2200:],float),np.zeros((2200,3)))),terminal_body_rest=bool(abs(ss[-50:,3:6]).max()<=.003),terminal_steering_rest=bool(abs(ss[-50:,7]).max()<=.015),memory_shape=mm.shape==(len(ss),5))
  proof=dict(passed=all(checks.values()),checks=checks,original_whole_checks={k:bool(value)for k,value in original.items()},original_goal_upper_m=float(upper),minimum_static_raw_m=minimum,required_static_raw_m=required,origin_packet=p,origin_packet_sha256=bridge.digest(p),source_native=p['native_tick'],source_sim_time=p['sim_time'],scope='ORIGINAL_CURRENT_RESPONSE_STATIC_PREFIX_COMPLETE_STOP_NOT_ARRIVAL')
  save('TEB_RESPONSE_ACCOUNTING.json',counts)
  return proof,ss,uu,mm
 proof,ss,uu,mm=prove(p0,requests);quota.save_npz(out/'CURRENT_SHADOW.npz',dict(states=ss,controls=uu,memory=mm,requests=np.asarray(requests,float)),np);save('CURRENT_SHADOW_CERTIFICATE.json',proof)
 assert proof['passed'],'FRESH_TEB_CANDIDATE_ORIGINAL_RESPONSE_REFUSED'
 admissions=[];maximum=np.zeros(3)
 for i,request in enumerate(requests):
  if i<10 and i%5==0:
   current=copy.deepcopy(p0)if i==0 else packet(v);block=requests[i:i+5]+[[0.,0.,False]for _ in range(2200)]
   one,_,_,_=prove(current,block);admissions.append(dict(offset=i,proof=one));save('CURRENT_ADMISSION_RECEIPTS.json',admissions)
   assert one['passed'],'CURRENT_TEB_PREFIX_RETAINED_STOP_REFUSED'
  v._chain_phase='TEB_CURRENT_CANDIDATE'if i<10 else'TEB_COMPLETE_ZERO_STOP'
  v.adapter.parked_target=None;v.step(*request)
  measured=packet(v);b=np.asarray(measured['body']);dyaw=b[2]-ss[i+1,2]
  error=[np.linalg.norm(b[:2]-ss[i+1,:2]),abs(math.atan2(math.sin(dyaw),math.cos(dyaw))),abs(bridge.decode(measured,expected_native=v.count,expected_sim_time=float(v.d.time),expected_packet_sha256=bridge.digest(measured))['author_state'][4]-ss[i+1,6])]
  maximum=np.maximum(maximum,error);assert np.all(maximum<=[.04,.035,.015]),'TEB_ORIGINAL_ACTUAL_TRACKING_REFUSED'
  if v.count%5==0:
   assert not evidence.update(v.scan()),'TEB_COMPONENT_CAUSAL_DYNAMIC_BRANCH_UNQUALIFIED_STOP'
 final=packet(v);distance=math.dist(final['body'][:2],task['goal_xy'])
 save('CURRENT_ADMISSION_RECEIPTS.json',admissions);save('WHITELIST_CAUSAL_OBSERVATIONS.json',evidence.snapshots);save('TEB_RESPONSE_ACCOUNTING.json',counts)
 result=dict(passed=True,scope='FRESH_T0_TEB_CONTROL_CYCLE_COMPONENT_NOT_NAVIGATION',actual_native=v.count,reference_query_attempts=dwa_counts['query_attempts'],reference_query_returns=dwa_counts['query_returns'],reference_counts=dwa_counts,original_TEB_HCP=True,internal_modelwork=None,component_active_native=10,complete_zero_stop_native=2200,measured_maximum_tracking=maximum.tolist(),current_5native_admissions=len(admissions),original_task_goal_distance_m=distance,actual_original_goal_reached=distance<=.45,whole_navigation_passed=False,initial_fresh_packet_sha256=bridge.digest(p0),first_causal_discovery=None,response_counts=counts)
 save('TEB_COMPONENT_FUNCTIONAL_RESULT.json',result)
 return result
