"""Pure source transformation and data authority checks, no planner propagation."""
import ast,copy,ctypes,fcntl,importlib.abc,json,math,runpy,sys,time,traceback
from context import C,O,R,put,read,sha,load,validate,fixed_input
def main():
 start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy
 resource_policy.apply();load('v1676_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','rclpy','kernel','vehicle','factory','bindings'}:raise AssertionError('SOURCE_NO_NUMERIC_IMPORT:'+name)
 sys.meta_path.insert(0,Ban());original=ctypes.CDLL
 def banned(*a,**k):raise AssertionError('SOURCE_NO_DLL')
 ctypes.CDLL=banned
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 source=read(R/'runs/v1672_svg_direct_live_component/SOURCE_FREEZE.json')['files'].copy()
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,reference_queries=0,response_model_constructors=0,old_numeric_suite_rerun=False)
 try:
  assert read(R/'runs/v1672_svg_direct_live_component/POST_ROUND_STORAGE_BARRIER.json')['passed']
  assert read(R/'runs/v1672_svg_direct_live_component/CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
  inp=fixed_input()
  files=[O/'INPUT.json',O/'REFERENCE_CONFIG.json',R/'runs/v1672_svg_direct_live_component/POST_ROUND_STORAGE_BARRIER.json',R/'runs/v1672_svg_direct_live_component/CURRENT_SOURCE_REMOTE_RECOVERY.json']
  intake=R/'runs/v1675_dwa_reference_intake';capture=read(intake/'EXACT_CAPTURE_RESULT.json');assert capture['passed']and capture['distinct_reference_identity']
  for row in capture['rows']:
   p=R/row['saved_path'];assert sha(p)==row['sha256']and p.stat().st_size==row['bytes'];files.append(p)
  files.extend([intake/n for n in ['EXACT_CAPTURE_RESULT.json','CAPTURE_RESULT.json','OLD_IMPLEMENTATION_AVAILABILITY.json','COMMIT.json']])
  for row in inp['bound_inputs']:files.extend([R/row['path'],R/row['archive_index_path']])
  for p in files:source[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in source.items())
  reference=load('v1676_actual_reference_transform',C/'reference.py');nodes,proof=reference.source_nodes(source)
  assert len(nodes)==8 and sum(row['only_Ackermann_sample_mask_added']for row in proof.values())==1
  for name,row in proof.items():
   if name!='calc_control_and_trajectory':assert row['original_AST_SHA256']==row['phase_AST_SHA256']
  cfg=inp['reference_config'];assert cfg['max_speed']==.08 and cfg['max_accel']==.2 and cfg['dt']==.1 and cfg['predict_time']==3. and cfg['robot_stuck_flag_cons']==0.
  assert [cfg[k]for k in ['to_goal_cost_gain','speed_cost_gain','obstacle_cost_gain']]==[.15,1.,1.]
  negatives=[];curve=cfg['maximum_curvature']
  for label,v,w in [('inplace',0.,.01),('reverse',-.01,0.),('deadband',.004,0.),('excess_curvature',.01,.01*curve+1e-8)]:
   assert not reference.admissible(v,w,curve);negatives.append(label)
  assert reference.admissible(.01,0.,curve)and reference.admissible(.01,-.01*curve,curve)
  # Math declaration only, not rollout: source mask preserves every original search statement.
  a=dict(scope='DWA_REFERENCE_ORIGINAL_RESPONSE_STATIC_SAVED_INPUT',numerical_authorized=True,physical_authorized=False,benchmark_authorized=False,boot_id='s',source_freeze_sha256='f',input_sha256='i',constructor_limit=1,solve_limit=1,step_limit=2205,start_wall=100,start_mono=200,normal_stop_wall=280,normal_stop_mono=380,root_stop_wall=400,root_stop_mono=500)
  args=dict(wall=101,mono=201,boot='s',freeze_sha='f',input_sha='i');assert validate(a,**args)
  for key,value in [('physical_authorized',True),('benchmark_authorized',True),('boot_id','wrong'),('solve_limit',2),('step_limit',2206),('normal_stop_wall',99),('normal_stop_mono',200),('root_stop_wall',401)]:
   bad=copy.deepcopy(a);bad[key]=value
   try:validate(bad,**args)
   except AssertionError:negatives.append(key)
   else:raise AssertionError('BAD_AUTHORITY_ACCEPTED:'+key)
  try:runpy.run_path(str(C/'entry.py'),run_name='__main__')
  except AssertionError as e:assert str(e)=='DWA_REFERENCE_NUMERIC_ADMISSION_MISSING';negatives.append('actual_CLI_no_numeric_admission')
  else:raise AssertionError('UNADMITTED_NUMERIC_CLI_ACCEPTED')
  tree=ast.parse((C/'response.py').read_text());calls=[ast.unparse(n.func)for n in ast.walk(tree)if isinstance(n,ast.Call)]
  assert calls.count('query')==calls.count('q.model.Predictor')==calls.count('predictor.step')==1
  assert 'q.main'not in calls and 'q.search'not in calls
  assert inp==fixed_input()and all(sha(R/n)==h for n,h in source.items())
  (O/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files=source,source_only=True,numerical_admission=False),sort_keys=True,separators=(',',':'))+'\n')
  result.update(passed=True,source_members=len(source),negative_cases=negatives,reference_AST_proof=proof,original_goal_preserved=True,distinct_old_G4C_identity=True,public_obstacle_points=len(inp['obstacle_points']),actual_planner_queries=0,numeric_runtime_not_yet_qualified=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());(O/'FAILED_SOURCE_FREEZE.json').write_text(json.dumps(dict(files=source)))
 finally:
  ctypes.CDLL=original;result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
