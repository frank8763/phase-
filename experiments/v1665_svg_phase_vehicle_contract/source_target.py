"""Only measured-data geometry conversion; no numerical vehicle model imports."""
import ast,copy,ctypes,fcntl,importlib.abc,json,math,sys,time,traceback
from context import C,O,R,put,read,sha,load

def main():
 start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
 import resource_policy
 resource_policy.apply();load('v1665_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','rclpy','kernel','vehicle','factory'}:raise AssertionError('GEOMETRY_CONVERSION_NO_NUMERICAL_MODEL_IMPORT:'+name)
 sys.meta_path.insert(0,Ban());original=ctypes.CDLL
 def no_dll(*args,**kwargs):raise AssertionError('SOURCE_NO_DLL')
 ctypes.CDLL=no_dll
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 source=read(R/'runs/v1661_svg_binding_namespace/SOURCE_FREEZE.json')['files'].copy()
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,author_constructor_calls=0,optimizer_calls=0,Allocator_calls=0)
 try:
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
  for folder,names in [(R/'runs/v1661_svg_binding_namespace',['CURRENT_SOURCE_REMOTE_RECOVERY.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','COMPLETION.json','RUNTIME_CLOSED_REVIEW.json','POST_ROUND_STORAGE_BARRIER.json','numeric/RESULT.json']),
   (R/'experiments/v1003_causal_recovery_execution',['predictor.py']),
   (R/'experiments/v993_steering_transient_diagnosis',['vehicle_control.py'])]:
   for name in names:p=folder/name;source[str(p.relative_to(R))]=sha(p)
  assert read(R/'runs/v1661_svg_binding_namespace/COMPLETION.json')['passed']and read(R/'runs/v1661_svg_binding_namespace/POST_ROUND_STORAGE_BARRIER.json')['passed']
  assert all(sha(R/n)==h for n,h in source.items())
  b=load('v1665_actual_bridge',C/'bridge.py');packet=read(R/'runs/v1661_svg_binding_namespace/INPUT.json')['original_packet'];original_packet=copy.deepcopy(packet)
  # Execute ONLY original pure virtual geometry function, no numpy dependency/model module.
  source_path=R/'experiments/v1003_causal_recovery_execution/predictor.py';tree=ast.parse(source_path.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='virtual')
  class Two:
   def __init__(self,v):self.v=v
   def __getitem__(self,i):return self.v[i]
  class Tiny:
   @staticmethod
   def asarray(v,dtype):return v
   @staticmethod
   def tan(v):return Two([math.tan(x)for x in v])
  space=dict(np=Tiny,math=math);exec(compile(ast.Module(body=[node],type_ignores=[]),str(source_path),'exec'),space)
  rows=[];maxerror=0.;roundtrip=0.
  for center in [-b.CENTER_LIMIT,-.2,0.,.2,b.CENTER_LIMIT]:
   k=math.tan(center)/.6;wheels=[math.atan(.6*k/(1-.27*k)),math.atan(.6*k/(1+.27*k))]
   current=copy.deepcopy(packet);current['steering']['position']=wheels;before=copy.deepcopy(current)
   origin=b.decode(current,expected_native=0,expected_sim_time=0.,expected_packet_sha256=b.digest(current))
   exact=space['virtual'](wheels);maxerror=max(maxerror,abs(exact-origin['author_state'][4]));roundtrip=max(roundtrip,abs(center-origin['author_state'][4]));assert current==before
   rows.append(dict(center=center,wheels=wheels,decoder=origin['author_state'][4],original_virtual=exact))
  assert maxerror==0. and roundtrip<=1e-15
  transient=copy.deepcopy(packet);transient['steering']['position']=[.12,.08];transient['steering']['velocity']=[.03,-.04];transient['controller_memory']=dict(last_ctrl=[.1,.09,.2,.2],integral=.012);transient['body_lateral']=.002;transient['body'][4]=.01
  original_transient=copy.deepcopy(transient);origin=b.decode(transient,expected_native=0,expected_sim_time=0.,expected_packet_sha256=b.digest(transient));assert transient==original_transient and origin['unrepresented_author_states']['controller_memory']==transient['controller_memory']and origin['measured_wheel_curvature_disagreement']>0.
  negatives=[]
  def refuse(label,fn):
   try:fn()
   except(AssertionError,ValueError):negatives.append(label)
   else:raise AssertionError('EXPECTED_REFUSAL:'+label)
  for label,change in [('steering_native',lambda p:p['steering'].update(native_tick=1)),('body_time',lambda p:p.update(sim_time=.01)),('nonfinite_encoder',lambda p:p['steering'].update(position=[float('inf'),0.])),('invalid_memory',lambda p:p['controller_memory'].update(last_ctrl=[0.])),('time_order',lambda p:p.update(body_measured_at=p['sent_at']+1))]:
   altered=copy.deepcopy(packet);change(altered)
   def check(altered=altered):return b.decode(altered,expected_native=0,expected_sim_time=0.,expected_packet_sha256=b.digest(altered))
   refuse(label,check)
  refuse('packet_SHA',lambda:b.decode(packet,expected_native=0,expected_sim_time=0.,expected_packet_sha256='0'*64))
  clean=b.decode(packet,expected_native=0,expected_sim_time=0.,expected_packet_sha256=b.digest(packet));requests=[]
  for speed,gear in [(.08,1),(-.03,-1),(0.,0)]:
   delta=.2 if speed else 0.;req=b.request(delta,longitudinal_speed=speed,declared_gear=gear,origin=clean,expected_origin_sha256=b.digest(packet));assert req['body_request']==[speed,speed*math.tan(delta)/.6,False]and not req['physical_authorized'];requests.append(req)
  for label,delta,speed,gear in [('outside_cap',b.CENTER_LIMIT+1e-9,.08,1),('gear_mismatch',.1,.08,-1),('speed_cap',0.,.1000001,1),('deadband',.1,.001,1),('parked_mode',.1,0.,0)]:
   refuse(label,lambda delta=delta,speed=speed,gear=gear:b.request(delta,longitudinal_speed=speed,declared_gear=gear,origin=clean,expected_origin_sha256=b.digest(packet)))
  refuse('output_foreign_origin',lambda:b.request(0.,longitudinal_speed=.08,declared_gear=1,origin=clean,expected_origin_sha256='0'*64))
  refuse('actual_physical_entry',b.physical_permission)
  assert packet==original_packet and transient==original_transient and all(sha(R/n)==h for n,h in source.items())
  (O/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files=source,source_only=True,physical_admission=False),sort_keys=True,separators=(',',':'))+'\n')
  result.update(passed=True,source_members=len(source),negative_cases=negatives,measured_decoder_cases=rows,maximum_error_vs_original_virtual=maxerror,maximum_ideal_wheel_inverse_roundtrip_error=roundtrip,noncoordinated_measured_wheels_and_memory_preserved=True,original_packet_no_mutation=True,request_cases=requests,physical_admission=False)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());(O/'FAILED_SOURCE_FREEZE.json').write_text(json.dumps(dict(files=source)))
 finally:
  ctypes.CDLL=original;result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
