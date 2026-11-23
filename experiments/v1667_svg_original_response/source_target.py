"""New saved-candidate/request scope only, zero numerical model imports."""
import ast,copy,ctypes,fcntl,importlib.abc,json,math,runpy,sys,time,traceback
from context import C,O,R,put,read,sha,load,validate,fixed_input

def main():
 start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy
 resource_policy.apply();load('v1667_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','rclpy','kernel','vehicle','factory','bindings'}:raise AssertionError('SOURCE_NO_MODEL_IMPORT:'+name)
 sys.meta_path.insert(0,Ban());original=ctypes.CDLL
 def banned(*args,**kwargs):raise AssertionError('SOURCE_NO_DLL')
 ctypes.CDLL=banned
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 source=read(R/'runs/v1665_svg_phase_vehicle_contract/SOURCE_FREEZE.json')['files'].copy()
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,author_constructor_calls=0,optimizer_calls=0,Allocator_calls=0,old_numeric_suite_rerun=False)
 try:
  assert read(R/'runs/v1665_svg_phase_vehicle_contract/CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
  assert read(R/'runs/v1661_svg_binding_namespace/POST_ROUND_STORAGE_BARRIER.json')['passed']
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
  files=[O/'INPUT.json',R/'runs/v1665_svg_phase_vehicle_contract/CURRENT_SOURCE_REMOTE_RECOVERY.json',R/'runs/v1665_svg_phase_vehicle_contract/SOURCE_QUALIFICATION.json',R/'runs/v1665_svg_phase_vehicle_contract/SOURCE_OUTER_CLOSED.json']
  inp=fixed_input()
  for row in inp['bound_inputs']:files.extend([R/row['path'],R/row['archive_index_path']])
  for p in files:source[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in source.items())
  before=copy.deepcopy(inp);schedule=load('v1667_production_schedule',C/'schedule.py');requests=schedule.rows(inp)
  assert inp==before and len(requests)==2270 and all(r==[0.,0.,False]for r in requests[-2200:])
  for i,delta in enumerate(inp['raw_author_controls']):assert requests[5*i:5*(i+1)]==[[.08,.08*math.tan(delta)/.6,False]]*5
  negatives=[]
  def refuse(label,fn):
   try:fn()
   except(AssertionError,ValueError):negatives.append(label)
   else:raise AssertionError('MISSING_REFUSAL:'+label)
  for label,key,value in [('speed','external_speed',.1),('tail','stop_native',2199),('native_interval','native_per_control',4),('unregistered_count','raw_author_controls',[0.])]:
   bad=copy.deepcopy(inp);bad[key]=value;refuse(label,lambda bad=bad:schedule.rows(bad))
  for label,value in [('out_of_cap',.42722137342572125+1e-9),('nonfinite',float('nan'))]:
   bad=copy.deepcopy(inp);bad['raw_author_controls'][0]=value;refuse(label,lambda bad=bad:schedule.rows(bad))
  a=dict(scope='PHASE_ORIGINAL_RESPONSE_STATIC_SAVED_CANDIDATE',numerical_authorized=True,physical_authorized=False,benchmark_authorized=False,boot_id='software',source_freeze_sha256='f',input_sha256='i',constructor_limit=1,solve_limit=0,step_limit=2270,start_wall=100,start_mono=200,normal_stop_wall=280,normal_stop_mono=380,root_stop_wall=400,root_stop_mono=500)
  args=dict(wall=101,mono=201,boot='software',freeze_sha='f',input_sha='i');assert validate(a,**args)
  for key,value in [('physical_authorized',True),('benchmark_authorized',True),('boot_id','wrong'),('step_limit',2271),('solve_limit',1),('normal_stop_wall',99),('normal_stop_mono',200),('root_stop_wall',401)]:
   bad=copy.deepcopy(a);bad[key]=value;refuse('authority_'+key,lambda bad=bad:validate(bad,**args))
  try:runpy.run_path(str(C/'entry.py'),run_name='__main__')
  except AssertionError as e:assert str(e)=='ORIGINAL_RESPONSE_NUMERIC_ADMISSION_MISSING';negatives.append('actual_CLI_before_model_binding')
  else:raise AssertionError('ACTUAL_CLI_ACCEPTED')
  # Exact inherited original model/initial/checks identities, without importing them.
  identities={}
  for name in ['experiments/v1160_safe_terminal_connection/search.py','experiments/v1159_bounded_steering_load/model.py','experiments/v1159_bounded_steering_load/PARAMETERS.json','experiments/v1118_coupled_live_qualification/runtime.py','experiments/v1067_causal_replan_brake_reserve/kernel.py']:
   assert name in source and sha(R/name)==source[name];identities[name]=source[name]
  tree=ast.parse((C/'response.py').read_text());calls=[ast.unparse(n.func)for n in ast.walk(tree)if isinstance(n,ast.Call)]
  assert calls.count('q.model.Predictor')==calls.count('predictor.step')==calls.count('q.helper.checks')==1
  assert 'q.main'not in calls and 'q.search'not in calls
  oldproof=read(R/'runs/v1658_svg_bounded_numeric/SOURCE_QUALIFICATION.json');assert oldproof['passed']and len(oldproof['software_dispatch_cases'])==9
  assert all(sha(R/n)==h for n,h in source.items())
  (O/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files=source,source_only=True,numerical_admission=False),sort_keys=True,separators=(',',':'))+'\n')
  result.update(passed=True,source_members=len(source),negative_cases=negatives,request_rows=2270,zero_stop_rows=2200,exact_saved_input_and_no_mutation=True,source_identities_reused=identities,old_error_evidence_software_proof_sha256=sha(R/'runs/v1658_svg_bounded_numeric/SOURCE_QUALIFICATION.json'),original_profile_goal_check_preserved=True,numerical_runtime_binding_still_pending=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());(O/'FAILED_SOURCE_FREEZE.json').write_text(json.dumps(dict(files=source)))
 finally:
  ctypes.CDLL=original;result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
