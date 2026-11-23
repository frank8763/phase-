"""Fresh DWA cycle source/data/audit checks only, no numerical model imports."""
import ast,copy,ctypes,fcntl,importlib.abc,json,math,runpy,sys,time,traceback
from context import C,O,R,read,sha,load,put,digest
def main():
 start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy
 resource_policy.apply();load('v1679_originalguard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','OpenGL','rclpy','kernel','vehicle','factory','bindings'}:raise AssertionError('SOURCE_NO_MODELS:'+name)
 sys.meta_path.insert(0,Ban());original=ctypes.CDLL
 def banned(*a,**k):raise AssertionError('SOURCE_NO_DLL')
 ctypes.CDLL=banned
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 source=read(R/'runs/v1676_dwa_bounded_proposal/SOURCE_FREEZE.json')['files'].copy()
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,reference_query_calls=0,actual_runtime_qualified=False)
 try:
  assert read(R/'runs/v1676_dwa_bounded_proposal/POST_ROUND_STORAGE_BARRIER.json')['passed']
  assert read(R/'runs/v1676_dwa_bounded_proposal/CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
  for p in [O/n for n in ['PILOT_TASK.json','REFERENCE_CONFIG.json','LIMITS_DRAFT.json']]+[R/'runs/v1676_dwa_bounded_proposal'/n for n in ['SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','COMPLETION.json','RUNTIME_CLOSED_REVIEW.json','POST_ROUND_STORAGE_BARRIER.json']]:source[str(p.relative_to(R))]=sha(p)
  for name in ['SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json','CURRENT_SOURCE_REMOTE_RECOVERY.json','PRELAUNCH_AUDIT_BINDING_CHECK.json']:
   p=R/'runs/v1679_dwa_live_component'/name;source[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in source.items())
  reused=[]
  for name in ['capture.py','resources.py','quota.py','work.py','history_binding.py','transforms.py','runtime_binding.py','error_stop.py']:
   assert sha(C/name)==sha(R/'experiments/v1672_svg_direct_live_component'/name);reused.append(name)
  assert sha(O/'REFERENCE_CONFIG.json')==sha(R/'runs/v1676_dwa_bounded_proposal/REFERENCE_CONFIG.json')
  task=read(O/'PILOT_TASK.json');old=read(R/'runs/v1672_svg_direct_live_component/PILOT_TASK.json')
  for key in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','dynamic','course_id','original_pool_task']:assert task[key]==old[key]
  assert task['task_id']=='dwa_fresh_component'and task['component_active_native']==10 and task['component_stop_native']==2200 and task['native_limit']==2410 and task['historical_prefix_native']==0
  limits=read(O/'LIMITS_DRAFT.json');assert limits['maximum_actual_native']==limits['maximum_replay_native']==2410 and limits['maximum_task_evidence_bytes']==224*1024**2 and limits['storage_limit_bytes']==15*1024**3
  reference=load('v1679_exactreferenceAST',R/'experiments/v1676_dwa_bounded_proposal/reference.py');nodes,proof=reference.source_nodes(source);assert len(nodes)==8
  assert proof==read(R/'runs/v1676_dwa_bounded_proposal/SOURCE_QUALIFICATION.json')['reference_AST_proof']
  obstacles=load('v1679_actualpublicobstacles',C/'obstacles.py')
  known=dict(known_rectangles=[[0.,0.,.2,.3]],known_circles=[[1.,1.,.1]],actor_truth=[9.,9.],bootstrap_reference=[[0.,0.],[4.,-2.]])
  clean={k:known[k]for k in ['known_rectangles','known_circles']};assert obstacles.make(known)==obstacles.make(clean)
  prior=read(R/'runs/v1676_dwa_bounded_proposal/INPUT.json');assert obstacles.make(prior['public_setup']['known'])==prior['obstacle_points']
  audit=load('v1679_generic_auditor_seam',C/'audit_component.py');fn,seam=audit.generic_ast(source)
  assert seam==read(R/'runs/v1672_svg_direct_live_component/SOURCE_QUALIFICATION.json')['generic_actual_safety_auditor_seam']
  text=(C/'audit_component.py').read_text();assert 'assert n==2210'in text and 'len(receipts)==2'in text and 'list(range(0,10,5))'in text
  assert "q.ref"not in text and "sys.modules['kernel'].ref._old.Geometry"in text,'EXPLICIT_ALREADY_LOADED_ORIGINAL_GEOMETRY_BINDING'
  search_tree=ast.parse((R/'experiments/v1160_safe_terminal_connection/search.py').read_text())
  assert not any(isinstance(node,ast.ImportFrom)and any(v.name=='ref'for v in node.names)for node in search_tree.body),'NUMERIC_SEARCH_REF_NAMESPACE_ASSUMPTION_CHANGED'
  kernel_tree=ast.parse((R/'experiments/v1067_causal_replan_brake_reserve/kernel.py').read_text())
  assert any(isinstance(node,ast.ImportFrom)and node.module=='geometry_model'and any(v.name=='ref'for v in node.names)for node in kernel_tree.body)
  import context as declared_context
  driver=ast.parse((C/'driver.py').read_text())
  for node in driver.body:
   if isinstance(node,ast.ImportFrom)and node.module=='context':assert all(hasattr(declared_context,item.name)for item in node.names)
  negatives=[]
  for name in ['pilot_entry.py','driver.py']:
   try:runpy.run_path(str(C/name),run_name='__main__')
   except AssertionError as e:assert str(e)=='DWA_LIVE_COMPONENT_NOT_ADMITTED';negatives.append('actual_'+name+'_unadmitted')
   else:raise AssertionError('CLI_ACCEPTED')
  tree=ast.parse((C/'component.py').read_text());calls=[ast.unparse(n.func)for n in ast.walk(tree)if isinstance(n,ast.Call)]
  assert calls.count('query')==1 and 'v.step'in calls and 'v.scan'in calls and 'reference.bind'in calls
  text=(C/'component.py').read_text();assert 'for _ in range(10)'in text and 'len(requests)==2210'in text and 'if i<10 and i%5==0'in text
  assert 'answer['not in text and 'author_solve'not in text
  for n in ast.walk(tree):
   if isinstance(n,ast.Assign):assert all(ast.unparse(t)not in {'v.count','v.d.time','v.adapter.last','v.adapter.integral'}for t in n.targets)
  assert all(sha(R/n)==h for n,h in source.items())
  (O/'SOURCE_FREEZE.json').write_text(json.dumps(dict(files=source,source_only=True,models_authorized=False),sort_keys=True,separators=(',',':'))+'\n')
  result.update(passed=True,source_members=len(source),negative_cases=negatives,exact_pipeline_modules_reused=reused,task_seed_phase_unchanged=True,reference_config_byteidentical=True,reference_AST_proof=proof,public_geometry_only_verified=True,original_generic_actual_audit_seam=seam,one_fresh_query_one_0p1sec_cycle_then2200stop=True,sourcepass_not_actualpass=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());(O/'FAILED_SOURCE_FREEZE.json').write_text(json.dumps(dict(files=source)))
 finally:
  ctypes.CDLL=original;result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
