"""One original Python response rollout; preserves goal failure separately."""
import copy,hashlib,io,json,math,sys,traceback
from context import C,O,R,put,read,sha,load

def execute(inp,source,save,write_arrays,append_event):
 result=dict(passed=False,closed=False,scope='SAVED_STATIC_ORIGINAL_RESPONSE_COMPONENT',constructor_attempts=0,constructor_returns=0,constructor_inflight=False,response_step_attempts=0,response_step_returns=0,response_step_inflight=False,explicit_original_Allocator_compute_invocations=0,internal_Allocator_constructions=None,total_modelwork=None,optimizer_calls=0,physical_native=0,replay_native=0,first_error=None,secondary_errors=[],whole_navigation_passed=False,dynamic_safety_certified=False)
 states=[];controls=[];memory=[];requests=[]
 try:
  sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
  q=load('v1667_unchanged_original_response',R/'experiments/v1160_safe_terminal_connection/search.py');np=q.np
  assert sha(R/'experiments/v1159_bounded_steering_load/model.py')==source['experiments/v1159_bounded_steering_load/model.py']
  assert q.model.Predictor.__init__.__code__.co_filename==str(R/'experiments/v1159_bounded_steering_load/model.py')
  assert q.model.Predictor.step.__code__.co_filename==str(R/'experiments/v1159_bounded_steering_load/model.py')
  # Reuse exact original module namespace, without invoking old main/search.
  identities={}
  for module in list(sys.modules.values()):
   file=getattr(module,'__file__',None)
   if file:
    path=__import__('pathlib').Path(file).resolve()
    if path.is_relative_to(R)and path.suffix=='.py':
     key=str(path.relative_to(R));assert key in source and sha(path)==source[key],'UNREGISTERED_NUMERICAL_IMPORT:'+key;identities[key]=source[key]
  save('NUMERICAL_BINDING.json',dict(paths_SHA256=identities,original_model_parameters_sha256=sha(R/'experiments/v1159_bounded_steering_load/PARAMETERS.json'),models_created_yet=0))
  p0=copy.deepcopy(inp['source_packet']);origin=dict(q.initial(p0),steering_load_episode=False)
  assert not origin.get('coupled_episode',False)and not origin.get('steering_motion_active',False)
  assert np.array_equal(origin['last_ctrl'],p0['controller_memory']['last_ctrl'])and origin['integral']==p0['controller_memory']['integral']
  schedule=load('v1667_fixed_request_schedule',C/'schedule.py').rows(inp)
  result.update(constructor_attempts=1,constructor_inflight=True);save('CALL_JOURNAL.json',result)
  predictor=q.model.Predictor(inp['public_setup'],origin)
  result.update(constructor_returns=1,constructor_inflight=False)
  states=[predictor.state.copy()];memory=[np.r_[predictor.adapter.last,predictor.adapter.integral]]
  for i,request in enumerate(schedule):
   result.update(response_step_attempts=i+1,response_step_inflight=True)
   append_event('A',i)
   state,control=predictor.step(*request)
   result.update(response_step_returns=i+1,response_step_inflight=False,explicit_original_Allocator_compute_invocations=i+1)
   append_event('R',i)
   states.append(state.copy());controls.append(control.copy());requests.append(request);memory.append(np.r_[predictor.adapter.last,predictor.adapter.integral])
  ss=np.asarray(states);uu=np.asarray(controls);rr=np.asarray(requests,float);mm=np.asarray(memory)
  buffer=io.BytesIO();np.savez_compressed(buffer,states=ss,controls=uu,requests=rr,memory=mm);data=buffer.getvalue();write_arrays(data)
  result.update(raw_arrays_saved=True,raw_arrays_sha256=hashlib.sha256(data).hexdigest(),N=2270,Nplus1=len(ss))
  save('PRE_GATE_ACCOUNTING.json',result)
  kernel=sys.modules['kernel'];geometry=kernel.ref._old.Geometry(inp['public_setup']['known'],None)
  static,_=geometry.clearances(ss[:,:3]);minimum=float(np.min(static));required=float(kernel.REQUIRED)
  checks,upper=q.helper.checks(ss,uu,rr,p0,inp['public_setup'],np.asarray(inp['public_goal']),minimum,required)
  original={k:bool(v)for k,v in checks.items()}
  component={k:v for k,v in original.items()if k!='goal_upper'}
  component.update(full2200zero_requests=bool(len(rr)>=2200 and np.array_equal(rr[-2200:],np.zeros((2200,3)))),all_memory_saved=mm.shape==(2271,5),memory_ctrl_exact=bool(np.array_equal(mm[1:,:4],uu)),initial_state_exact=bool(np.array_equal(ss[0],np.asarray(origin['state']))),initial_memory_exact=bool(np.array_equal(mm[0],np.r_[origin['last_ctrl'],origin['integral']])),terminal_body_rest=bool(np.max(abs(ss[-50:,3:6]))<=.003),terminal_steering_rest=bool(np.max(abs(ss[-50:,7]))<=.015),packet_memory_clock_unchanged=inp['source_packet']==p0)
  result.update(passed=all(component.values()),component_checks=component,original_whole_profile_checks=original,original_goal_upper_m=float(upper),public_goal_unchanged=inp['public_goal'],predicted_goal_distance_m=float(np.linalg.norm(ss[-1,:2]-inp['public_goal'])),minimum_static_fullfootprint_raw_m=minimum,original_required_raw_m=required,terminal_state=ss[-1].tolist(),maximum_body_speed=float(np.max(abs(ss[:,3]))),maximum_yaw_rate=float(np.max(abs(ss[:,5]))),maximum_virtual_steering=float(np.max(abs(ss[:,6]))),original_shadow_only_not_actual_evidence=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  result['closed']=True
  try:save('RESULT.json',result)
  except BaseException as e:result['secondary_errors'].append(dict(stage='TERMINAL_SAVE',error=repr(e)));result['passed']=False
 return result
