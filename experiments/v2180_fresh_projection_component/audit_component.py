"""Independent current actual-prefix audit; success additionally needs goal-stop."""
import ast,gzip,sys,math
from pathlib import Path
from context import SOURCE,C,R,read,load,digest,sha

def audit(task,result,source,*,predictive_arrays):
 old=load('v1691_original_generic_ast',C/'generic_audit.py')
 dependency=R/'experiments/v1195_eight_gib_timed_refuge';before=sys.path[:];sys.path.insert(0,str(dependency))
 try:
  module=load('v1691_original_actual_auditor',old.PARENT);fn,seam=old.generic_ast(source);space=vars(module).copy()
  exec(compile(ast.Module(body=[fn],type_ignores=[]),str(C/'audit_component.py'),'exec'),space)
  scratch=dict(result,passed=False,error=None,functional_failure=dict(canonical_first_error=result['first_error'],scope='CURRENT_FILTER_COMMON_TASK_PREFIX'))
  generic=space['audit'](task,result_override=scratch)
 finally:sys.path[:]=before
 np=module.np;q=module.q;out=Path(task['output']);n=generic['n'];states=generic['states'];trace=generic['trace'];commands=generic['commands']
 assert n>0 and n<=60000 and result['own_replay_native']==n
 observation=load('v1691_independent_current_observation',C/'observation.py')
 files=sorted(out.glob('cycle_*_origin.json'));previous=-1
 for path in files:
  row=read(path);receipt=row['receipt'];k=row['origin_native'];assert k>previous;previous=k
  p=observation.verify(receipt,k,.01*k)
  assert abs(np.asarray(q.initial(p)['state'])-states[k]).max()<=1e-8,'CURRENT_ORIGIN_ACTUAL_STATE_BINDING'
  assert abs(np.asarray(receipt['scan']['xy'])-states[receipt['scan']['native_tick'],:2]).max()<=1e-8
 # Rebuild causal information from the saved whitelist scans only. Verify each
 # dynamic-source snapshot and recompute geometry/profile gates on saved arrays;
 # no second physical rollout or controller decision is executed here.
 causal=load('v1691_independent_causal_tracker',R/'experiments/v1024_full_route_execution/causal.py')
 evidence=causal.Evidence(generic['setup']['known']);seen={}
 for scan in generic['sensors']:
  z=observation.scan_only(scan,scan['native_tick'],scan['time'])
  if z['native_tick']in seen:assert seen[z['native_tick']]==z
  else:seen[z['native_tick']]=z
 scans=iter(sorted(seen.values(),key=lambda z:z['native_tick']));pending=next(scans,None)
 proof_files=[p for p in out.glob('cycle_*.json')if p.stem.endswith(('shadow','goal_stop','segment_stop','admission_0','admission_5'))]
 proof_files.sort(key=lambda p:(read(p)['origin_packet']['native_tick'],p.name))
 kernel=sys.modules['kernel'];all_geometry=[];stop_covered=set()
 for path in proof_files:
  proof=read(path);p=proof['origin_packet'];k=p['native_tick']
  while pending is not None and pending['native_tick']<=k:evidence.update(pending);pending=next(scans,None)
  receipt=proof['receipt'];assert observation.verify(receipt,k,.01*k)==p and receipt['scan']==seen[receipt['scan']['native_tick']]
  source_snapshot=proof['causal_source']
  if evidence.first is None:assert source_snapshot is None
  else:
   assert source_snapshot['periodic']==evidence.periodic.snapshot()and source_snapshot['source_native_tick']==evidence.last_scan['native_tick']
   assert abs(source_snapshot['source_age_s']-(p['sim_time']-evidence.last_scan['time']))<=1e-8
   assert source_snapshot['decision_at']>=receipt['after_monotonic']
  with predictive_arrays.load_full(proof)as z:ss=z['states'];uu=z['controls'];rr=z['requests'];mm=z['memory']
  minimum=float(kernel.ref._old.Geometry(generic['setup']['known'],None).clearances(ss[:,:3])[0].min())
  terminal=float(kernel.ref._old.Geometry(generic['setup']['known'],None).clearances(ss[-1:,:3])[0].min())
  if source_snapshot is not None:
   minimum=min(minimum,float(kernel.Geometry(generic['setup']['known'],source_snapshot['periodic'],p['sim_time']).clearances(ss[:,:3],np.arange(len(ss)),.005).min()))
   sa,da=kernel.ref._old.Geometry(generic['setup']['known'],source_snapshot['periodic']).clearances(ss[-1:,:3]);terminal=float(min(sa[0],da[0]))
  checks,upper=q.helper.checks(ss,uu,rr,p,generic['setup'],np.asarray(task['goal_xy']),minimum,kernel.REQUIRED)
  checks={key:bool(v)for key,v in checks.items()if key!='goal_upper'}
  checks.update(full2200=bool(len(rr)>=2200 and np.array_equal(rr[-2200:],np.zeros((2200,3)))),terminal_body_rest=bool(abs(ss[-50:,3:6]).max()<=.003),terminal_steering_rest=bool(abs(ss[-50:,7]).max()<=.015),memory_shape=mm.shape==(len(ss),5),terminal_full_cycle_hold=terminal>=kernel.REQUIRED)
  assert checks==proof['checks']and bool(all(checks.values()))==proof['passed']
  assert abs(minimum-proof['minimum_raw_m'])<=1e-8 and abs(terminal-proof['terminal_full_cycle_raw_m'])<=1e-8 and abs(upper-proof['original_goal_upper_m'])<=1e-8
  if path.stem.endswith(('segment_stop','goal_stop')):
   count=0
   while count<2200 and k+count<n and generic['journal'][k+count]['phase']in {'FILTER_SEGMENT_COMPLETE_STOP','FILTER_ORIGINAL_GOAL_STOP'}:count+=1
   if count:
    assert np.array_equal(rr[:count],commands[k:k+count][:,[1,2,5]])
    e=states[k:k+count+1]-ss[:count+1];assert np.linalg.norm(e[:,:2],axis=1).max()<=.04 and abs(np.arctan2(np.sin(e[:,2]),np.cos(e[:,2]))).max()<=.035 and abs(e[:,6]).max()<=.015
    stop_covered.update(range(k,k+count))
  all_geometry.append(minimum)
  predictive_arrays.confirm_full_geometry(proof)
 # Every actually applied normal command must have an accepted measured5+2200
 # proof. Failed/unexecuted next queries remain saved without creating coverage.
 covered=set();maximum=np.zeros(3)
 for path in sorted(out.glob('cycle_*_admission_*.json')):
  proof=read(path);a=proof['origin_packet']['native_tick']
  if not proof['passed']:continue
  receipt=proof['receipt'];p=observation.verify(receipt,a,.01*a)
  assert proof['origin_packet']==p and proof['origin_packet_sha256']==digest(p)and all(proof['checks'].values())
  assert abs(np.asarray(q.initial(p)['state'])-states[a]).max()<=1e-8
  with predictive_arrays.load_prefix_after_full(proof)as z:ss=z['states'];rr=z['requests']
  count=0
  while count<5 and a+count<n and generic['journal'][a+count]['phase']=='FILTER_RECEDING_CURRENT':count+=1
  if count:
   assert np.array_equal(rr[:count],commands[a:a+count][:,[1,2,5]])
   e=states[a:a+count+1]-ss[:count+1];value=np.array([np.linalg.norm(e[:,:2],axis=1).max(),abs(np.arctan2(np.sin(e[:,2]),np.cos(e[:,2]))).max(),abs(e[:,6]).max()]);maximum=np.maximum(maximum,value)
   covered.update(range(a,a+count))
 normal={i for i,row in enumerate(generic['journal'])if row['phase']=='FILTER_RECEDING_CURRENT'}
 assert covered==normal and(maximum<=[.04,.035,.015]).all(),'ALL_NORMAL_ACTUAL_HAS_CURRENT_ADMISSION'
 with np.load(out/'FULL_STATE_NPLUS1.npz')as z:
  for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat','time']:
   value=z[key];assert len(value)==n+1
   if value[1:].size:assert abs(value[1:]-trace[key]).max()<=1e-8
 final=read(out/'ACTUAL_FINAL_PACKET.json');assert module.previous.stopped(final)
 nav=result.get('navigation')or{};whole=bool(nav.get('passed')and nav.get('whole_goal_with_original_stop'))
 if whole:
  assert nav['whole_goal_with_original_stop']and nav['complete_zero_stop_native']==2200
  assert np.array_equal(commands[-2200:][:,[1,2,5]],np.zeros((2200,3)))and np.linalg.norm(states[-1,:2]-task['goal_xy'])<=.45
  stops=[read(p)for p in out.glob('cycle_*_executed.json')if read(p)['kind']=='whole_goal_stop'];assert len(stops)==1;proof=read(out/stops[0]['proof']);assert proof['passed']and proof['original_whole_checks']['goal_upper']
  a=proof['origin_packet']['native_tick']
  with predictive_arrays.load_goal_after_full(proof)as z:ss=z['states'];rr=z['requests']
  assert a+2200==n and np.array_equal(rr,commands[a:][:,[1,2,5]])
  e=states[a:]-ss;assert np.linalg.norm(e[:,:2],axis=1).max()<=.04 and abs(np.arctan2(np.sin(e[:,2]),np.cos(e[:,2]))).max()<=.035 and abs(e[:,6]).max()<=.015
 query=load('projection_independent_query_cursor',C/'audit_query_cursor.py');query_audit=query.audit(out,task,source,np,require_complete=bool(nav.get('passed')))
 if nav.get('passed'):assert n==2320 and len(normal)==120 and len(all_geometry)==49 and len(stop_covered)==2200
 # All executed non-error stop ticks also require their full original proof.
 assert stop_covered=={i for i,row in enumerate(generic['journal'])if row['phase']in {'FILTER_SEGMENT_COMPLETE_STOP','FILTER_ORIGINAL_GOAL_STOP'}}
 answer=dict(passed=True,scope='ORIENTATION_PROJECTION_CP_ORIGINAL_PHYSICAL_STOP_COMPONENT'if nav.get('passed')else'INDEPENDENT_ACTUAL_PREFIX_ONLY_CANONICAL_FAILURE_PRESERVED',whole_navigation_passed=False,component_complete_original_stop=bool(nav.get('passed')),actual_native=n,own_replay_native=result['own_replay_native'],maximum_controller_error=generic['maximum_controller_error'],maximum_memory_error=generic['maximum_memory_error'],maximum_actual_tracking=maximum.tolist(),normal_native_with_current_admission=len(covered),minimum_actual_clearance_m=float(trace['clearance'].min()),canonical_first_error=result['first_error'],original_generic_audit_seam=seam,causal_sources_rebuilt_from_whitelist=True,independent_saved_prediction_geometry_profiles=len(all_geometry),internal_Allocator_constructions=None,total_modelwork=None,new_physical_native_during_audit=0,compact_query_audit=query_audit)
 answer.update(native_author_PRIEST=False,own_learned_actor_calls=0,factory_internal_policy_calls=None)
 module.dump(out/'FINAL_INDEPENDENT_AUDIT.json',answer);return answer
