"""Software-only qualification of once-call dispatch and error evidence."""
import ast,copy,ctypes,fcntl,importlib.abc,json,os,runpy,sys,time,traceback
from context import C,O,R,put,read,sha,load,validate,fixed_input

def main():
 start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'))
 import resource_policy
 resource_policy.apply();load('v1658_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','rclpy','kernel','vehicle','factory'}:raise AssertionError('SOURCE_NO_NUMERICAL_IMPORT:'+name)
 sys.meta_path.insert(0,Ban())
 original=ctypes.CDLL
 def banned(*args,**kwargs):raise AssertionError('SOURCE_NO_DLL')
 ctypes.CDLL=banned
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 source=read(R/'runs/v1656_svg_solver_interface/SOURCE_FREEZE.json')['files'].copy()
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,author_constructor_calls=0,optimizer_calls=0,software_fake_calls_only=True)
 try:
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
  for name in ['INPUT.json','MAPS.json','CONFIG.json','PREPARATION_CHECKPOINT.json']:
   source[str((O/name).relative_to(R))]=sha(O/name)
  for name in ['SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','CURRENT_SOURCE_REMOTE_RECOVERY.json']:
   path=R/'runs/v1656_svg_solver_interface'/name;source[str(path.relative_to(R))]=sha(path)
  assert all(sha(R/n)==h for n,h in source.items())
  inp,config,maps=fixed_input()
  authority=dict(scope='SVG_AUTHOR_CORE_ONCE_STATIC_SAVED_INPUT',numerical_authorized=True,physical_authorized=False,benchmark_authorized=False,boot_id='software',source_freeze_sha256='f',input_sha256='i',constructor_limit=1,solve_limit=1,start_wall=100,start_mono=200,normal_stop_wall=160,normal_stop_mono=260,root_stop_wall=280,root_stop_mono=380)
  args=dict(wall=101,mono=201,boot='software',freeze_sha='f',input_sha='i');assert validate(authority,**args)
  negatives=[]
  for key,value in [('physical_authorized',True),('benchmark_authorized',True),('boot_id','wrong'),('solve_limit',2),('source_freeze_sha256','wrong'),('normal_stop_wall',99),('normal_stop_mono',200),('root_stop_wall',281)]:
   altered=copy.deepcopy(authority);altered[key]=value
   try:validate(altered,**args)
   except AssertionError:negatives.append(key)
   else:raise AssertionError('BAD_AUTHORITY_ACCEPTED:'+key)
  try:runpy.run_path(str(C/'entry.py'),run_name='__main__')
  except AssertionError as e:assert str(e)=='SVG_NUMERIC_ADMISSION_MISSING';negatives.append('production_CLI_no_admission')
  else:raise AssertionError('UNADMITTED_CLI_ACCEPTED')
  transaction=load('v1658_software_transaction',C/'transaction.py');cases=[]
  class Fake:
   def __init__(self,kind):self.kind=kind;self.creates=0;self.solves=0;self.destroys=0
   def phase_svg_create(self,*args):self.creates+=1;return None if self.kind=='constructor_refusal'else 1
   def phase_svg_set_maps(self,*args):return -1 if self.kind=='map_refusal'else 0
   def phase_svg_solve(self,h,state,n,out,capacity,rate):
    self.solves+=1
    if self.kind=='solve_throw':raise RuntimeError('FIRST_SOLVE')
    for i in range(capacity):out[i]=float('nan')if self.kind=='nonfinite'else(.5 if self.kind=='out_of_bounds'else 0.)
    rate._obj.value=0.;return -1 if self.kind=='solve_refusal'else 0
   def phase_svg_error(self,buf,size):buf.value=b'SOFTWARE_INJECTED';return 17
   def phase_svg_call_counts(self,h,c,n):c[0]=1;c[1]=1;return 0
   def phase_svg_destroy(self,h):
    self.destroys+=1
    if self.kind=='solve_throw':raise RuntimeError('SECONDARY_DESTROY')
  for kind in ['success','constructor_refusal','map_refusal','solve_refusal','solve_throw','nonfinite','out_of_bounds','raw_save_failure','terminal_save_failure']:
   lib=Fake(kind);saved={};order=[]
   def save(name,value):
    order.append(name)
    if(kind=='raw_save_failure'and name=='RAW_SOLVE_RETURN.json')or(kind=='terminal_save_failure'and name=='RESULT.json'):raise RuntimeError('INJECTED_SAVE:'+name)
    saved[name]=copy.deepcopy(value)
   actual=transaction.execute(lib,inp,config,maps,save)
   assert lib.creates==1 and lib.solves<=1 and actual['passed']==(kind=='success')
   if kind in ['success','nonfinite','out_of_bounds','solve_refusal']:
    assert actual['raw_result_saved']and len(saved['RAW_SOLVE_RETURN.json']['control_double_bytes_hex'])==224
   if kind=='solve_throw':
    assert actual['solve_inflight']and 'FIRST_SOLVE'in actual['first_error']and 'SECONDARY_DESTROY'in actual['secondary_errors'][0]['error']
   if kind=='constructor_refusal':assert lib.solves==lib.destroys==0
   if kind=='map_refusal':assert lib.solves==0 and lib.destroys==1
   if kind=='raw_save_failure':assert not actual['raw_result_saved']and 'INJECTED_SAVE'in actual['first_error']
   if kind=='terminal_save_failure':assert actual['secondary_errors'][-1]['stage']=='TERMINAL_SAVE'
   assert order[0]=='CALL_JOURNAL.json';cases.append(dict(kind=kind,software_constructor_calls=lib.creates,software_solve_calls=lib.solves,first_error=actual['first_error'],secondary_errors=actual['secondary_errors']))
  assert all(sha(R/n)==h for n,h in source.items())
  # Manifest is larger than terminal result allowance; bounded SOURCE-only output.
  encoded=(json.dumps(dict(files=source,source_only=True,numerical_admission=False),sort_keys=True,separators=(',',':'))+'\n').encode();assert len(encoded)<4*1024**2
  (O/'SOURCE_FREEZE.json').write_bytes(encoded)
  result.update(passed=True,source_members=len(source),negative_cases=negatives,software_dispatch_cases=cases,fixed_input_shapes_checked=True,numerical_admission=False)
 except BaseException as e:
  result.update(first_error=repr(e),traceback=traceback.format_exc());(O/'FAILED_SOURCE_FREEZE.json').write_text(json.dumps(dict(files=source)))
 finally:
  ctypes.CDLL=original;result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
