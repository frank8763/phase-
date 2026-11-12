"""Full-goal candidate first, then a separately labelled finite observer.

Only the physical driver can declare arrival; a completed information corridor
is never a completed navigation trial. Every corridor includes the full stop.
"""
import copy,math,time
import numpy as np
from kernel import C,load,predict,checks,initial,ref,Geometry,REQUIRED
from information import propose
from planner import construct
legacy=load('v1067_one_legacy_candidate',C/'legacy_handoff.py')

def forecast_packet(packet,state,memory,ticks):
 p=copy.deepcopy(packet);k=math.tan(state[6])/.6;kd=(1+math.tan(state[6])**2)/.6*state[7];p.update(body=[*state[:4],state[5]],native_tick=packet['native_tick']+ticks,sim_time=packet['sim_time']+.01*ticks,analytical_forecast_only=True);p['steering'].update(position=[math.atan(.6*k/(1-.27*k)),math.atan(.6*k/(1+.27*k))],velocity=(.6*kd/(np.array([1-.27*k,1+.27*k])**2+(.6*k)**2)).tolist(),native_tick=p['native_tick']);p['controller_memory']=dict(last_ctrl=memory[:4].tolist(),integral=float(memory[4]));return p

def prepare(setup,packet,source,goal,actions,elapsed):
 begun=time.monotonic();legacy.hold_permission(setup,packet,source);rejections=[]
 try:
  remaining=legacy.refresh_module.remainder(actions,elapsed);test_s,test_u,test_r,test_m=predict(setup,packet,remaining,tail=False);assert float(np.linalg.norm(test_s[-1,:2]-goal))+.08<=.45,'COMPLETE_INPUT_ENDPOINT_OR_CONTROL_REJECTED'
  result=legacy.prepare(setup,packet,source,goal,actions,elapsed);result.update(source_kind='COMPLETE_GOAL',functional_goal_source=True);return result
 except AssertionError as e:
  assert str(e)in ['NO_ABSOLUTE_LAUNCH_INTERVAL','COMPLETE_INPUT_ENDPOINT_OR_CONTROL_REJECTED','NO_REQUALIFIED_REMAINDER','PREFIX_NOT_PHASE_INDEPENDENT','TERMINAL_HOLD','GENERIC_EPOCH_NATIVE_LIMIT','WAIT_NOT_STATIONARY','WAIT_COMPOSITION_NOT_EQUIVALENT'],'UNKNOWN_LEGACY_SOURCE_EXCEPTION '+str(e);rejections.append(str(e))
 hold=[dict(kind='wait',gear=0,target=0.,ticks=1001)];s,u,r,m=predict(setup,packet,hold,tail=False);projected=forecast_packet(packet,s[-1],m[-1],1001);candidate=construct(setup,projected,source,goal,wall_s=4.,max_expansions=5000)
 assert not candidate['terminated_by_wall'],'DETERMINISTIC_SOURCE_SEARCH_WALL_EXCEPTION'
 if candidate['passed']:
  suffix=candidate['actions'];source_kind='COMPLETE_GOAL'if candidate['functional_goal_source']else'SAFE_PROGRESS_RECOVERY_NOT_ARRIVAL';extra=dict(search_result={k:v for k,v in candidate.items()if k not in ['state_path','predicted_actuator_controls','planned_body_requests','actions']})
 else:
  info=propose(setup,projected,source,goal);suffix=info['actions'];source_kind='INFORMATION_RECOVERY_NOT_ARRIVAL';extra=dict(information=info,goal_search_rejected={k:v for k,v in candidate.items()if k not in ['state_path','predicted_actuator_controls','planned_body_requests','actions']})
 joined=[dict(kind='wait',gear=0,target=0.,ticks=800),dict(kind='wait',gear=0,target=0.,ticks=200),dict(kind='wait',gear=0,target=0.,ticks=1)]+suffix;full_s,full_u,full_r,full_m=predict(setup,packet,joined,tail=False);ss=full_s[800:];uu=full_u[800:];rr=full_r[800:];expected_time=packet['sim_time']+8.;minimum=Geometry(setup['known'],source['periodic'],expected_time).complete(ss);memory=dict(last_ctrl=full_m[800,:4].tolist(),integral=float(full_m[800,4]));cc,upper=checks(ss,uu,rr,dict(controller_memory=memory),setup,np.asarray(goal),minimum,REQUIRED);safety=dict(cc);safety.pop('goal_upper');assert all(safety.values())and minimum>=REQUIRED+1e-7,'COMPLETE_RECOVERY_INPUT_SAFETY_REJECTED'
 if source_kind=='COMPLETE_GOAL':assert cc['goal_upper'],'COMPLETE_RECOVERY_GOAL_REJECTED'
 elif source_kind=='INFORMATION_RECOVERY_NOT_ARRIVAL':
  a,b=ref._old.Geometry(setup['known'],source['periodic']).clearances(ss[:,:3]);assert min(a.min(),b.min())>=REQUIRED+1e-7,'INFORMATION_NOT_FULL_CYCLE_SAFE'
 else:
  a,b=ref._old.Geometry(setup['known'],source['periodic']).clearances(ss[-1:,:3]);assert min(a[0],b[0])>=REQUIRED+.02,'FINITE_PROGRESS_TERMINAL_OBSERVATION_RESERVE'
 a,b=ref._old.Geometry(setup['known'],source['periodic']).clearances(ss[:201,:3]);prefix_lower=float(np.minimum(a,b).min());assert prefix_lower>=REQUIRED+1e-7,'RECOVERY_PREFIX_NOT_FULL_CYCLE_SAFE';q=201
 return dict(passed=True,source_kind=source_kind,functional_goal_source=source_kind=='COMPLETE_GOAL',information_never_counts_as_arrival=True,packet=packet,source=source,source_planes=legacy.base.planes(source['periodic']['vertices']),goal=goal,prefix=[dict(kind='wait',gear=0,target=0.,ticks=200)],suffix=suffix,prefix_states=ss[:201].tolist(),prefix_controls=uu[:200].tolist(),prefix_requests=rr[:200].tolist(),wait_states=ss[200:q+1].tolist(),wait_controls=uu[200:q].tolist(),cross_states=ss[q:].tolist(),cross_controls=uu[q:].tolist(),cross_requests=rr[q:].tolist(),launch_bounds=[minimum],minimum_prefix_raw_m=prefix_lower,complete_profile_checks=safety,original_goal_profile_checks=cc,terminal_goal_upper_m=upper,generic_complete_profile_checked=True,publication_clock_kind='FIXED_ZERO_HOLD_NATIVE',expected_publication_native=packet['native_tick']+800,expected_publication_sim_time=expected_time,fixed_launch_wait=1,pre_adoption_hold_native=800,nominal_controller_at_publication=memory,nominal_state_at_publication=ss[0].tolist(),wait_equivalence_proof='FULL_ORIGINAL_PYTHON_HOLD_AND_RECOVERY_COMPOSITION',wall_s=time.monotonic()-begun,models=0,legacy_candidate_rejections=rejections,**extra)
