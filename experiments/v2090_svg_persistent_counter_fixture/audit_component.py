"""Independent current actual-prefix audit; success additionally needs goal-stop."""
import ast,gzip,sys,math
from pathlib import Path
from context import C,R,read,load,digest

def audit(task,result,source,*,predictive_arrays):
 old=load('v1691_original_generic_ast',C/'generic_audit.py')
 dependency=R/'experiments/v1195_eight_gib_timed_refuge';before=sys.path[:];sys.path.insert(0,str(dependency))
 try:
  module=load('v1691_original_actual_auditor',old.PARENT);fn,seam=old.generic_ast(source);space=vars(module).copy()
  exec(compile(ast.Module(body=[fn],type_ignores=[]),str(C/'audit_component.py'),'exec'),space)
  scratch=dict(result,passed=False,error=None,functional_failure=dict(canonical_first_error=result['first_error'],scope='CURRENT_SVG_EXPOSED_COMPONENT_PREFIX'))
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
 proof_files=[p for p in out.glob('cycle_*.json')if p.stem.endswith(('shadow','goal_stop','admission_0','admission_5'))]
 proof_files.sort(key=lambda p:(read(p)['origin_packet']['native_tick'],p.name))
 kernel=sys.modules['kernel'];all_geometry=[];complete_final_stop_verified=False
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
  if path.name=='cycle_0001_admission_5.json'and (result.get('navigation')or{}).get('passed'):
   assert len(rr)==2205 and np.array_equal(rr,commands[5:][:,[1,2,5]])
   error=states[5:]-ss
   assert np.linalg.norm(error[:,:2],axis=1).max()<=.04 and abs(np.arctan2(np.sin(error[:,2]),np.cos(error[:,2]))).max()<=.035 and abs(error[:,6]).max()<=.015,'SVG_SECOND_QUERY_COMPLETE_STOP_TRACKING'
   complete_final_stop_verified=True
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
  while count<5 and a+count<n and generic['journal'][a+count]['phase']=='SVG_RECEDING_CURRENT':count+=1
  if count:
   assert np.array_equal(rr[:count],commands[a:a+count][:,[1,2,5]])
   e=states[a:a+count+1]-ss[:count+1];value=np.array([np.linalg.norm(e[:,:2],axis=1).max(),abs(np.arctan2(np.sin(e[:,2]),np.cos(e[:,2]))).max(),abs(e[:,6]).max()]);maximum=np.maximum(maximum,value)
   covered.update(range(a,a+count))
 normal={i for i,row in enumerate(generic['journal'])if row['phase']=='SVG_RECEDING_CURRENT'}
 assert covered==normal and(maximum<=[.04,.035,.015]).all(),'ALL_NORMAL_ACTUAL_HAS_CURRENT_ADMISSION'
 with np.load(out/'FULL_STATE_NPLUS1.npz')as z:
  for key in ['qpos','qvel','ctrl','mocap_pos','mocap_quat','time']:
   value=z[key];assert len(value)==n+1
   if value[1:].size:assert abs(value[1:]-trace[key]).max()<=1e-8
 final=read(out/'ACTUAL_FINAL_PACKET.json');assert module.previous.stopped(final)
 nav=result.get('navigation')or{};whole=False # This fixed interface component never asserts whole navigation.
 if whole:
  assert nav['whole_goal_with_original_stop']and nav['complete_zero_stop_native']==2200
  assert np.array_equal(commands[-2200:][:,[1,2,5]],np.zeros((2200,3)))and np.linalg.norm(states[-1,:2]-task['goal_xy'])<=.45
  stops=list(out.glob('cycle_*_goal_stop.json'));assert len(stops)==1;proof=read(stops[0]);assert proof['passed']and proof['original_whole_checks']['goal_upper']
  a=proof['origin_packet']['native_tick']
  with predictive_arrays.load_goal_after_full(proof)as z:ss=z['states'];rr=z['requests']
  assert a+2200==n and np.array_equal(rr,commands[a:][:,[1,2,5]])
  e=states[a:]-ss;assert np.linalg.norm(e[:,:2],axis=1).max()<=.04 and abs(np.arctan2(np.sin(e[:,2]),np.cos(e[:,2]))).max()<=.035 and abs(e[:,6]).max()<=.015
 if (result.get('navigation')or{}).get('passed'):
  assert n==2210 and len(normal)==10 and np.array_equal(commands[10:][:,[1,2,5]],np.zeros((2200,3)))
  independent=load('SVG_independent_current_control_rebuild',R/'experiments/v2054_svg_current_control_contract/interface.py');control=independent.CurrentControl(source,run_id=task['run_id']);selected=read(out/'SVG_SELECTED_SEGMENT.json')
  requests=[];acks=[]
  for cycle,offset in enumerate([0,5]):
   proof=read(out/f'cycle_{cycle:04d}_shadow.json');assert proof['passed']and proof['origin_packet']['native_tick']==offset and proof['native']==2210
   raw=read(out/f'SVG_QUERY_{cycle}_RESULT.json');frame=read(out/f'SVG_QUERY_{cycle}_FRAME.json');request=frame['request'];assert raw['passed']and raw['counts']['constructor_returns']==1 and raw['counts']['query_returns']==cycle+1 and raw['counts']['author_solve_attempts']==raw['counts']['author_solve_returns']==cycle+1 and raw['counts']['native_solve_returncode']==0
   assert raw['raw']['input_sha256']==digest(request)and raw['raw']['origin_native_tick']==offset and raw['raw']['map_sha256']==frame['maps_sha256']
   receipt=read(out/f'cycle_{cycle:04d}_origin.json')['receipt']
   rebuilt=control.frame(np,receipt,goal_xy=task['goal_xy'],rear_path=selected['poses'],gear=selected['gear']);assert rebuilt==frame,'SVG_CURRENT_CAUSAL_MAP_AND_STATE_REBUILD'
   proposal=control.proposal(raw['raw'],now=100.);saved=read(out/f'SVG_QUERY_{cycle}_PROPOSAL.json');assert proposal==saved and not proposal['actual_execution_permitted']
   assert np.array_equal(commands[offset:offset+5][:,[1,2,5]],np.tile(np.asarray(proposal['body_request']),[5,1]))
   assert request['measurement_source_packet_sha256']==receipt['packet_sha256']
   import hashlib,json
   line=json.dumps(frame,allow_nan=False).encode()+b'\n';ack=dict(sequence=cycle,bytes=len(line),sha256=hashlib.sha256(line).hexdigest());assert raw['transport_ack']==ack
   acks.append(ack);requests.append(proposal['body_request'])
  control.close();closed=read(out/'SVG_NATIVE_CLOSED.json')['counts']
  assert closed['DLL_loads']==closed['constructor_attempts']==closed['constructor_returns']==closed['destroy_calls']==1
  assert closed['query_attempts']==closed['query_returns']==2 and closed['author_solve_attempts']==closed['author_solve_returns']==2 and not closed['constructor_inflight']and not closed['query_inflight']
  assert complete_final_stop_verified and len(all_geometry)==4


 answer=dict(passed=True,scope='SVG_PERSISTENT_TWO_CURRENT_VEHICLE_COMPONENT_AND_COMPLETE_STOP'if (result.get('navigation')or{}).get('passed')else'INDEPENDENT_ACTUAL_PREFIX_SAFETY_ONLY_CANONICAL_FAILURE_PRESERVED',whole_navigation_passed=whole,actual_native=n,own_replay_native=result['own_replay_native'],maximum_controller_error=generic['maximum_controller_error'],maximum_memory_error=generic['maximum_memory_error'],maximum_actual_tracking=maximum.tolist(),normal_native_with_current_admission=len(covered),minimum_actual_clearance_m=float(trace['clearance'].min()),canonical_first_error=result['first_error'],original_generic_audit_seam=seam,causal_sources_rebuilt_from_whitelist=True,independent_saved_prediction_geometry_profiles=len(all_geometry),internal_Allocator_constructions=None,total_modelwork=None,new_physical_native_during_audit=0)
 module.dump(out/'FINAL_INDEPENDENT_AUDIT.json',answer);return answer
