"""One irreversible attempt per author operation, journal before each call."""
import ctypes,math,traceback

def execute(lib,inp,config,maps,save):
 result=dict(passed=False,closed=False,constructor_attempts=0,constructor_returns=0,constructor_inflight=False,solve_attempts=0,solve_returns=0,solve_inflight=False,internal_kinematic_rollout_steps=None,physical_native=0,replay_native=0,Allocator_calls=0,first_error=None,secondary_errors=[],FFI_calls=0,raw_result_saved=False)
 handle=None
 def checkpoint(stage):save('CALL_JOURNAL.json',dict(result,stage=stage))
 def error():
  text=ctypes.create_string_buffer(2048);result['FFI_calls']+=1;lib.phase_svg_error(text,len(text));return text.value.decode('utf8',errors='replace')
 try:
  p=(ctypes.c_double*25)(*config['parameters']);k=(ctypes.c_int*7)(*config['integers'])
  result.update(constructor_attempts=1,constructor_inflight=True);checkpoint('BEFORE_CONSTRUCTOR')
  result['FFI_calls']+=1;handle=lib.phase_svg_create(p,25,k,7)
  result.update(constructor_returns=1,constructor_inflight=False);checkpoint('AFTER_CONSTRUCTOR')
  assert handle,'AUTHOR_CONSTRUCTOR_REFUSED:'+error()
  planes=[(ctypes.c_double*10000)(*maps[name])for name in ['collision_layer','distance_field','angle_field','speed_field']]
  result['FFI_calls']+=1;map_code=lib.phase_svg_set_maps(handle,100,100,.1,0.,0.,*planes)
  save('MAP_RETURN.json',dict(returncode=map_code,error=error()if map_code!=0 else None))
  assert map_code==0,'AUTHOR_MAP_REFUSED'
  state=(ctypes.c_double*5)(*inp['state']);out=(ctypes.c_double*14)(*[float('nan')]*14);rate=ctypes.c_double(float('nan'))
  result.update(solve_attempts=1,solve_inflight=True);checkpoint('BEFORE_SOLVE')
  result['FFI_calls']+=1;code=lib.phase_svg_solve(handle,state,5,out,14,ctypes.byref(rate))
  result.update(solve_returns=1,solve_inflight=False)
  # Preserve exact output bytes even for a refused/nonfinite response, BEFORE gates.
  raw=dict(returncode=code,control_double_bytes_hex=bytes(out).hex(),collision_double_bytes_hex=bytes(rate).hex(),byte_order=__import__('sys').byteorder,error=error()if code!=0 else None)
  save('RAW_SOLVE_RETURN.json',raw);result['raw_result_saved']=True;checkpoint('AFTER_RAW_SAVE')
  counts=(ctypes.c_ulonglong*2)();result['FFI_calls']+=1;counts_code=lib.phase_svg_call_counts(handle,counts,2)
  save('AUTHOR_OUTER_COUNTERS.json',dict(returncode=counts_code,attempts=int(counts[0]),returns=int(counts[1]),internal_rollouts=None))
  assert code==0,'AUTHOR_SOLVE_REFUSED:'+str(raw['error'])
  assert counts_code==0 and list(counts)==[1,1],'AUTHOR_OUTER_COUNTER_MISMATCH'
  assert all(math.isfinite(v)for v in out)and math.isfinite(rate.value),'NONFINITE_AUTHOR_OUTPUT'
  assert all(-.45<=v<=.45 for v in out),'AUTHOR_STEERING_LIMIT_OUTPUT'
  assert 0.<=rate.value<=1.,'AUTHOR_COLLISION_RATE_RANGE'
  result.update(passed=True,controls=list(out),author_internal_collision_rate=rate.value,whole_navigation_passed=False,physical_safety_certified=False)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  if handle:
   try:result['FFI_calls']+=1;lib.phase_svg_destroy(handle)
   except BaseException as e:result['secondary_errors'].append(dict(stage='DESTROY',error=repr(e)))
  result['closed']=True
  try:save('RESULT.json',result)
  except BaseException as e:
   result['secondary_errors'].append(dict(stage='TERMINAL_SAVE',error=repr(e)));result['passed']=False
   # Console is an independent bounded outer-owner witness, never a replacement RESULT.
  return result
