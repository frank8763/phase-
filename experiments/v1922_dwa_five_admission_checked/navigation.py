"""Current-only receding DWA with original complete-stop admission, no rescue."""
import copy,math,sys
from context import C,O,R,read,load,digest

def run(v,binding,task,source,out,save,quota,refresh):
 q=binding['q'];np=q.np
 setup=read(out/'physics/SETUP.json');goal=np.asarray(task['goal_xy'],float)
 observation=load('v1691_causal_scan_packet',C/'observation.py')
 response=load('v1691_original_response_gate',C/'response.py')
 static_points=load('v1691_static_cost_points',C/'obstacles.py').make(setup['known']);save('DWA_PUBLIC_STATIC_POINTS.json',static_points)
 reference=load('v1691_exact_pinned_DWA',R/'experiments/v1676_dwa_bounded_proposal/reference.py')
 causal=load('v1691_original_causal_tracker',R/'experiments/v1024_full_route_execution/causal.py')
 evidence=causal.Evidence(setup['known']);last_scan=None;cycles=[];active=None
 totals=dict(query_attempts=0,query_returns=0,candidate_trajectory_calls=0,candidate_trajectory_returns=0,reference_motion_calls=0,total_modelwork=None)
 def scan():
  nonlocal last_scan
  z=observation.scan_only(v.scan(),v.count,float(v.d.time))
  if last_scan is None or z['native_tick']>last_scan['native_tick']:evidence.update(z)
  last_scan=z;return z
 def snapshot():
  save('NAVIGATION_PROGRESS.json',dict(actual_native=v.count,completed_cycles=len(cycles),active_cycle=active,reference_counts=totals,first_causal_discovery_native=None if evidence.first is None else evidence.first['native_tick'],whole_navigation_passed=False))
 def proof_for(receipt,requests,label,cycle):
  p=receipt['packet'];causal_source=None if evidence.first is None else evidence.source(v)
  proof,ss,uu,mm=response.prove(q,setup,p,requests,goal,causal_source)
  proof.update(origin_packet_sha256=digest(p),receipt=receipt,executed_native=0,arrays=f"cycle_{cycle:04d}_{label}.npz")
  proof['hybrid_evidence']=binding['predictive_arrays'].persist(proof,dict(states=ss,controls=uu,memory=mm,requests=np.asarray(requests,float)))
  save(f'cycle_{cycle:04d}_{label}.json',proof)
  return proof,ss
 def move(request,predicted,index):
  v.adapter.parked_target=None;v.step(*request)
  p=binding['packet'](v);s=np.asarray(q.initial(p)['state']);delta=s-predicted[index+1]
  error=[float(np.linalg.norm(delta[:2])),abs(math.atan2(math.sin(delta[2]),math.cos(delta[2]))),abs(float(delta[6]))]
  assert np.all(np.asarray(error)<=[.04,.035,.015]),'DWA_CURRENT_ACTUAL_TRACKING_REFUSED'
  if v.count%5==0:scan()
 scan()
 for cycle in range(task['maximum_control_native']//10+1):
  refresh('STOPPED_EVENT_PREPARATION')
  receipt=observation.acquire(v,binding,last_scan);p=receipt['packet'];distance=float(np.linalg.norm(np.asarray(p['body'][:2])-goal))
  active=dict(cycle=cycle,origin_native=v.count,receipt=receipt,query_returned=False,executed_native=0)
  save(f'cycle_{cycle:04d}_origin.json',active);snapshot()
  if distance<=.37:
   requests=[[0.,0.,False]for _ in range(2200)]
   proof,ss=proof_for(receipt,requests,'goal_stop',cycle)
   assert proof['passed']and proof['original_whole_checks']['goal_upper'],'DWA_ORIGINAL_COMPLETE_GOAL_STOP_REFUSED'
   active.update(kind='goal_stop',proof=f'cycle_{cycle:04d}_goal_stop.json')
   for i,request in enumerate(requests):
    v._chain_phase='DWA_ORIGINAL_GOAL_STOP';move(request,ss,i);active['executed_native']+=1
   cycles.append(active);snapshot();save(f'cycle_{cycle:04d}_executed.json',cycles[-1])
   final=binding['packet'](v);assert binding['old'].previous.stopped(final)
   assert math.dist(final['body'][:2],task['goal_xy'])<=.45,'DWA_ACTUAL_WHOLE_GOAL_NOT_REACHED'
   save('WHITELIST_CAUSAL_OBSERVATIONS.json',evidence.snapshots)
   return dict(passed=True,actual_original_goal_reached=True,whole_goal_with_original_stop=True,actual_native=v.count,complete_zero_stop_native=2200,cycles=len(cycles),reference_counts=totals,first_causal_discovery_native=None if evidence.first is None else evidence.first['native_tick'],original_goal_distance_m=math.dist(final['body'][:2],task['goal_xy']),not_oldG4CC3=True,common_benchmark=True)
  assert v.count<task['maximum_control_native'],'DWA_NATIVE_LIMIT_NO_WHOLE_GOAL'
  # One independent current query per original .1s control interval. Numerical
  # functions/configuration are unchanged; no retry, fallback or output clipping.
  query,counts,ast_proof,space,cfg=reference.bind(np,source,read(O/'REFERENCE_CONFIG.json'))
  cost_points=static_points+observation.points(receipt['scan'])
  totals['query_attempts']+=1
  command,trajectory=query(np.asarray(p['body'],float),goal,np.asarray(cost_points,float))
  for key in totals:
   if key not in {'query_attempts','total_modelwork'}:totals[key]+=counts.get(key,0)
  command=np.asarray(command,float);trajectory=np.asarray(trajectory,float)
  active.update(query_returned=True,command=command.tolist()if np.isfinite(command).all()else None,command_raw_double_hex=command.tobytes().hex(),trajectory_raw_double_hex=trajectory.tobytes().hex(),reference_counts=counts,static_points_sha256=digest(static_points),scan_cost_points=observation.points(receipt['scan']),AST_proof=ast_proof)
  save(f'cycle_{cycle:04d}_query.json',active);snapshot()
  assert command.shape==(2,)and np.isfinite(command).all()and np.isfinite(trajectory).all(),'DWA_NONFINITE_CURRENT_OUTPUT'
  assert reference.admissible(float(command[0]),float(command[1]),cfg.maximum_curvature)and command[0]<=.08 and abs(command[1])<=.16,'DWA_CURRENT_COMMAND_OUTSIDE_FIXED_DOMAIN'
  assert math.isfinite(float(space['calc_obstacle_cost'](trajectory,np.asarray(cost_points,float),cfg))),'DWA_REFERENCE_NO_FINITE_CURRENT_COMMAND'
  request=[float(command[0]),float(command[1]),False]
  full=[request.copy()for _ in range(10)]+[[0.,0.,False]for _ in range(2200)]
  proof,shadow=proof_for(receipt,full,'shadow',cycle)
  assert proof['passed'],'DWA_CURRENT_CYCLE_COMPLETE_STOP_REFUSED'
  active.update(kind='DWA_control_cycle',proof=f'cycle_{cycle:04d}_shadow.json',admissions=[])
  for offset in [0,5]:
   current=receipt if offset==0 else observation.acquire(v,binding,last_scan)
   short=[request.copy()for _ in range(5)]+[[0.,0.,False]for _ in range(2200)]
   one,ss=proof_for(current,short,f'admission_{offset}',cycle)
   active['admissions'].append(dict(offset=offset,path=f'cycle_{cycle:04d}_admission_{offset}.json'))
   assert one['passed'],'DWA_CURRENT_5_NATIVE_RETAINED_STOP_REFUSED'
   for i in range(5):
    v._chain_phase='DWA_RECEDING_CURRENT';move(request,ss,i);active['executed_native']+=1
   snapshot()
  cycles.append(copy.deepcopy(active));save(f'cycle_{cycle:04d}_executed.json',cycles[-1]);snapshot()
 raise AssertionError('DWA_FIXED_NATIVE_WORK_FINISHED_WITHOUT_WHOLE_GOAL')
