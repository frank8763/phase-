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
 query_audit=dict(query_records=0,optimizer_work_total=None)
 current_path=out/'FILTER_CURRENT_INPUT.json';raw_path=out/'FILTER_NATIVE_RESULT.json'
 if current_path.exists():
  with np.load(out/'INITIAL_FULL_STATE.npz')as z:full={k:z[k].tolist()for k in z.files}
  original_receipt=read(out/'cycle_000000_origin.json')['receipt'];selected=read(out/'FILTER_SELECTED_SEGMENT.json')
  rebuilt=load('FILTER_independent_current_request',C/'current_request.py').build(np,original_receipt,full,selected,source,run_id=task['run_id'])
  assert rebuilt['current']==read(current_path)and rebuilt['request']==read(out/'FILTER_OPTIMIZER_REQUEST.json')
  if raw_path.exists():
   raw=read(raw_path);answer=raw['answer'];numeric=answer['numerical'];returns=answer['returns'];counts=answer['work_accounting']
   assert counts['optimizer_call_attempts']==counts['optimizer_calls']==1 and counts['NLP_returns']==len(returns)<=2 and not counts['inflight_unknown']and counts['models']==0
   request=rebuilt['request'];case=request['case'];known=request['public_known'];method=request['method']
   math_modules=load('FILTER_independent_scoped_dependencies',C/'filter_scope.py').snapshot(source);callbacks=math_modules.filter;slack=None
   for row in returns:
    z=row['x'];values,_,labels=callbacks.values_jac(z[:16],case,known,method)
    assert len(z)>=16 and max(max(.005-z[2*i],z[2*i]-.1,abs(z[2*i+1])-1/1.32)for i in range(8))<=1e-7
    if row['stage']=='AUXILIARY':
     assert method=='PCBF'and len(z)==16+len(values);slack=z[16:];residual=max(v-t for v,t in zip(values,slack));assert min(slack)>=-1e-7
     width=len(values)//9;weights=[1.]*(len(values)-width)+[100.]*width;objective=sum(w*t for w,t in zip(weights,slack));assert abs(objective-row['objective'])<=1e-7
    else:
     assert row['stage']=='PERFORMANCE'and len(z)==16
     fixed=[0.]*len(values)if method=='PSF'else[max(t,0.)for t in slack]
     residual=max(v-t for v,t in zip(values,fixed));gear=case['gear'];v=gear*z[0];w=v*z[1];objective=(v-case['nominal'][0])**2+(w-case['nominal'][1])**2;assert abs(objective-row['objective'])<=1e-10
    assert abs(residual-row['maximum_constraint_residual'])<=1e-8
   proposal=answer.get('proposal');allowed=bool(numeric.get('passed')and numeric.get('original_hard_geometry_passed')and numeric.get('maximum_slack',float('inf'))<=1e-7)
   assert(proposal is not None)==allowed
   if allowed:
    assert returns and returns[-1]['stage']=='PERFORMANCE'and returns[-1]['success']and returns[-1]['maximum_constraint_residual']<=1e-7
    assert proposal==read(out/'FILTER_RAW_CURRENT_PROPOSAL.json')and proposal['raw_request']==numeric['commands'][0]and proposal['input_sha256']==rebuilt['current']['input_sha256']and not proposal['actual_execution_permitted']
    poses,_=callbacks.rollout_jac(returns[-1]['x'],case['pose'],case['gear']);assert np.max(abs(np.asarray(poses)-numeric['states']))<=1e-12
    oracle=math_modules.oracle;assert max(callbacks.REQUIRED-min(oracle.distances(p,known))for p in poses)<=1e-7
    if normal:assert np.array_equal(commands[:5][:,[1,2,5]],np.tile(proposal['raw_request'],[5,1]))
   else:assert not normal and not nav.get('passed')
   query_audit.update(query_records=1,NLP_returns=len(returns),numeric_accepted=bool(numeric.get('passed')),hard_gate_not_relaxed_by_slack=True)
   console=read(out/'FILTER_NATIVE_CONSOLE.json');wire=(out/'FILTER_CURRENT_INPUT_WIRE.json').read_bytes()
   assert len(console['text'].encode())==console['bytes']and __import__('hashlib').sha256(console['text'].encode()).hexdigest()==console['sha256']
   assert raw['input_bytes']==len(wire)and raw['input_byte_sha256']==__import__('hashlib').sha256(wire).hexdigest()and __import__('json').loads(wire)==rebuilt
 else:assert not normal and not raw_path.exists()and not nav.get('passed')
 if nav.get('passed'):assert n==2205 and len(normal)==5 and len(all_geometry)==3 and len(stop_covered)==2200 and query_audit['query_records']==1

 # All executed non-error stop ticks also require their full original proof.
 assert stop_covered=={i for i,row in enumerate(generic['journal'])if row['phase']in {'FILTER_SEGMENT_COMPLETE_STOP','FILTER_ORIGINAL_GOAL_STOP'}}
 answer=dict(passed=True,scope='FILTER_FRESH_CURRENT_VEHICLE_COMPONENT_WITH_COMPLETE_STOP'if nav.get('passed')else'INDEPENDENT_ACTUAL_PREFIX_ONLY_CANONICAL_FAILURE_PRESERVED',whole_navigation_passed=False,component_complete_original_stop=bool(nav.get('passed')),actual_native=n,own_replay_native=result['own_replay_native'],maximum_controller_error=generic['maximum_controller_error'],maximum_memory_error=generic['maximum_memory_error'],maximum_actual_tracking=maximum.tolist(),normal_native_with_current_admission=len(covered),minimum_actual_clearance_m=float(trace['clearance'].min()),canonical_first_error=result['first_error'],original_generic_audit_seam=seam,causal_sources_rebuilt_from_whitelist=True,independent_saved_prediction_geometry_profiles=len(all_geometry),internal_Allocator_constructions=None,total_modelwork=None,new_physical_native_during_audit=0,compact_query_audit=query_audit)
 module.dump(out/'FINAL_INDEPENDENT_AUDIT.json',answer);return answer
