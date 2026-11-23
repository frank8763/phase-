"""Source/API scope qualification; actual fresh component remains unexecuted."""
import ast,copy,ctypes,fcntl,importlib.abc,json,math,runpy,sys,time,traceback
from context import C,O,R,read,sha,load,put,digest

def main():
 start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy
 resource_policy.apply();load('v1670_original_write_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','rclpy','kernel','vehicle','factory','bindings'}:raise AssertionError('SOURCE_NO_MODEL_IMPORT:'+name)
 sys.meta_path.insert(0,Ban());original=ctypes.CDLL
 def banned(*a,**k):raise AssertionError('SOURCE_NO_DLL')
 ctypes.CDLL=banned
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 source=read(R/'runs/v1667_svg_original_response/SOURCE_FREEZE.json')['files'].copy()
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,author_constructor_calls=0,optimizer_calls=0,actual_runtime_qualified=False)
 try:
  assert read(R/'runs/v1667_svg_original_response/POST_ROUND_STORAGE_BARRIER.json')['passed']
  assert read(R/'runs/v1667_svg_original_response/CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
  for p in [O/n for n in ['PILOT_TASK.json','SOLVER_CONFIG.json','LIMITS_DRAFT.json']]+[R/'runs/v1667_svg_original_response'/n for n in ['SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','COMPLETION.json','RUNTIME_CLOSED_REVIEW.json','POST_ROUND_STORAGE_BARRIER.json']]:source[str(p.relative_to(R))]=sha(p)
  for p in [R/'experiments/v1195_eight_gib_timed_refuge/audit_refusal.py',R/'experiments/v1195_eight_gib_timed_refuge/route_tools.py',R/'experiments/v1179_frozen_recovery_native/audit.py']:
   source[str(p.relative_to(R))]=sha(p)
  for name in ['SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','FAILED_SOURCE_FREEZE.json']:
   p=R/'runs/v1670_svg_live_component'/name;source[str(p.relative_to(R))]=sha(p)
  for name in ['SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','FAILED_SOURCE_FREEZE.json']:
   p=R/'runs/v1671_svg_registered_component_audit'/name;source[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in source.items())
  reused=[]
  for name in ['capture.py','resources.py','quota.py','work.py','history_binding.py','transforms.py','runtime_binding.py']:
   assert sha(C/name)==sha(R/'experiments/v1639_original_evidence_stages'/name);reused.append(name)
  assert sha(C/'error_stop.py')==sha(R/'experiments/v1649_error_stop_sensor_capture/error_stop.py');reused.append('error_stop.py')
  task=read(O/'PILOT_TASK.json');old=read(R/'runs/v1639_original_evidence_stages/PILOT_TASK.json')
  for key in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','dynamic','course_id','original_pool_task']:assert task[key]==old[key]
  assert task['component_active_native']==70 and task['component_stop_native']==2200 and task['native_limit']==2470 and task['historical_prefix_native']==0
  limits=read(O/'LIMITS_DRAFT.json');assert limits['maximum_task_evidence_bytes']==224*1024**2 and limits['storage_limit_bytes']==15*1024**3 and limits['maximum_actual_native']==limits['maximum_replay_native']==2470
  config=read(O/'SOLVER_CONFIG.json');old_config=read(R/'runs/v1661_svg_binding_namespace/CONFIG.json');assert config['integers']==old_config['integers']
  delta=[i for i,(a,b)in enumerate(zip(config['parameters'],old_config['parameters']))if a!=b];assert delta==[1,2,3,6,7]
  assert [config['parameters'][i]for i in delta]==[.08,.42722137342572125,-.42722137342572125,.3,.3]
  maps=load('v1670_production_public_maps',C/'maps.py');known=dict(known_rectangles=[[0.,0.,.3,.3]],known_circles=[],actor_truth='FORBIDDEN_UNUSED',bootstrap_reference='FORBIDDEN_UNUSED')
  a=maps.make(known,[4.,-2.]);b=maps.make({k:known[k]for k in ['known_rectangles','known_circles']},[4.,-2.]);assert a==b
  assert len(a['collision_layer'])==10000 and sum(a['collision_layer'])==36 and set(a['speed_field'])=={.08}
  assert a['point_occupancy_only_not_footprint_certificate']and a['collision_layer'][49*100+49]==1. and a['collision_layer'][0]==0.
  audit=load('v1670_exact_audit_seam',C/'audit_component.py');fn,seam=audit.generic_ast(source)
  oldfn=next(n for n in ast.parse(audit.PARENT.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='audit');n=seam['generic_original_statements_preserved']
  assert all(ast.dump(x,include_attributes=False)==ast.dump(y,include_attributes=False)for x,y in zip(oldfn.body[:n],fn.body[:n]))
  preserved=ast.unparse(ast.Module(body=fn.body[:n],type_ignores=[]))
  for text in ['maximum_qpos_qvel_ctrl_mocap_error','memoryerror','self_margin','SENSORS.json.gz','CONTACTS.json.gz','subset','verify_saved','historical_controls_used']:assert text in preserved,'GENERIC_SAFETY_ASSERTION_NOT_COVERED:'+text
  import context as declared_context
  driver_tree=ast.parse((C/'driver.py').read_text())
  for node in driver_tree.body:
   if isinstance(node,ast.ImportFrom)and node.module=='context':
    assert all(hasattr(declared_context,item.name)for item in node.names),'EXPLICIT_DRIVER_CONTEXT_IMPORT_MISMATCH'
  assert 'FORMAL_TASK'not in (C/'driver.py').read_text()and 'audit_kind'not in (C/'driver.py').read_text(),'NO_FORMAL_DISPATCH_DEPENDENCY'
  negatives=[]
  for name in ['pilot_entry.py','driver.py']:
   try:runpy.run_path(str(C/name),run_name='__main__')
   except AssertionError as e:assert str(e)=='SVG_LIVE_COMPONENT_NOT_ADMITTED';negatives.append('actual_'+name+'_missing_admission_before_model')
   else:raise AssertionError('ACTUAL_CLI_ACCEPTED')
  tree=ast.parse((C/'component.py').read_text());text=ast.unparse(tree)
  assert 'v.step(*request)'in text and 'v.scan()'in text and 'CURRENT_ADMISSION_RECEIPTS.json'in text and 'FRESH_SVG_CANDIDATE_ORIGINAL_RESPONSE_REFUSED'in text
  assert 'historical_controls_used'not in text and not any(isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in {'mj_resetData','reset','mj_setState'}for n in ast.walk(tree))
  for n in ast.walk(tree):
   if isinstance(n,ast.Assign):assert all(ast.unparse(t)not in {'v.count','v.d.time','v.adapter.last','v.adapter.integral'}for t in n.targets),'LIVE_STATE_RESET_WRITE'
  assert all(sha(R/name)==h for name,h in source.items())
  (O/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files=source,source_only=True,models_authorized=False),sort_keys=True,separators=(',',':'))+'\n')
  result.update(passed=True,source_members=len(source),negative_cases=negatives,unchanged_actual_pipeline_modules=reused,actual_task_and_seed_phase_preserved=True,explicit_geometry_and_speed_config_delta=delta,public_maps_exclude_truth_and_bootstrap_reference=True,generic_actual_safety_auditor_seam=seam,original_error_stop_scanner_reused=True,live_component_not_yet_executed=True,source_pass_not_actual_runtime_pass=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());(O/'FAILED_SOURCE_FREEZE.json').write_text(json.dumps(dict(files=source)))
 finally:
  ctypes.CDLL=original;result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
