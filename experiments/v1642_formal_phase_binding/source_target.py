"""Registered-phase authority and audit interfaces only; no numerical execution."""
import ast,copy,fcntl,importlib.abc,os,runpy,sys,time,traceback,types,json
from pathlib import Path
from context import C,O,R,ROOT,put,read,sha,load

def main():
 start=time.monotonic();assert O==ROOT and 'PHASE_FORMAL_ASSIGNMENT'not in os.environ
 os.environ['MUJOCO_GL']='osmesa';sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
 load('v1642_source_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(ROOT)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','OpenGL','jax','rclpy','kernel','runtime','factory','vehicle'}:raise AssertionError('FORMAL_SOURCE_ONLY:'+name)
 sys.meta_path.insert(0,Ban())
 def profile(frame,event,arg):
  if event=='call':assert not any(n in frame.f_code.co_filename for n in ['/coupled_model.py','/coupled_control.py','/factory.py','/vehicle.py'])
 sys.setprofile(profile)
 with(ROOT/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 source=read(R/'runs/v1639_original_evidence_stages/SOURCE_FREEZE.json')['files'].copy()
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,source_only=True,actual_runtime_qualified=False)
 try:
  assert read(R/'runs/v1639_original_evidence_stages/POST_ROUND_STORAGE_BARRIER.json')['passed']
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
  for n in ['TASKS_LOCKED.json','LIMITS.json']:source[str((ROOT/n).relative_to(R))]=sha(ROOT/n)
  for n in ['COMPLETION.json','RUNTIME_CLOSED_REVIEW.json','POST_ROUND_STORAGE_BARRIER.json','AUDIT_ACCOUNTING_SUPPLEMENT.json']:
   p=R/'runs/v1639_original_evidence_stages'/n;source[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in source.items())
  reused=[]
  for n in ['capture.py','resources.py','history_binding.py','work.py','quota.py','transforms.py']:
   assert(C/n).read_bytes()==(R/'experiments/v1639_original_evidence_stages'/n).read_bytes();reused.append(n)
  registry=load('v1642_registry_source',C/'phase_contract.py');seams=load('v1642_audit_source',C/'audit_seams.py');audit=load('v1642_dispatch_source',C/'audit_binding.py')
  locked=read(ROOT/'TASKS_LOCKED.json');order=[a['assignment_id']for row in locked['tasks']for a in row['assignments']]
  descriptions=[registry.select(locked,k,ROOT)for k in order]
  assert len(descriptions)==20 and len({d['scientific_task_sha256']for d in descriptions})==12
  assert order[:4]==['phase_01__full','phase_01__no_onward','phase_02__no_onward','phase_02__full']
  assert descriptions[0]['task']['phase']==2.2609711555894934 and descriptions[0]['task']['seed']==10060001
  assert all(not d['physical_authorized']and not d['models_authorized']for d in descriptions)
  negatives=[]
  def refuse(name,fn):
   try:fn()
   except(AssertionError,KeyError,FileNotFoundError):negatives.append(name)
   else:raise AssertionError('FORMAL_SOURCE_NEGATIVE_ACCEPTED:'+name)
  refuse('unregistered_assignment',lambda:registry.select(locked,'phase_99__full',ROOT))
  refuse('foreign_output_root',lambda:registry.select(locked,order[0],ROOT.parent/'foreign'))
  bad=copy.deepcopy(locked);bad['tasks'][0]['task']['sensor_seed_unchanged']=False;refuse('changed_sensor_seed_scope',lambda:registry.select(bad,order[0],ROOT))
  bad=copy.deepcopy(locked);bad['tasks'][0]['variants']=['full','no_time'];refuse('wrong_route_ablation',lambda:registry.select(bad,order[0],ROOT))
  bad=copy.deepcopy(locked);bad['tasks'][0]['task']['stop_native']=200;refuse('shortened_original_tail',lambda:registry.select(bad,order[0],ROOT))
  def stub(path,name):
   module=types.ModuleType('SOFTWARE_NONEXECUTED_ORIGINAL_AUDIT_CODE');module.__file__=str(path)
   code=compile(path.read_bytes(),str(path),'exec',dont_inherit=True);fn=next(v for v in code.co_consts if isinstance(v,types.CodeType)and v.co_name==name)
   setattr(module,name,types.FunctionType(fn,vars(module),name));return module
  module=stub(seams.PARENT,'audit');original_tree=ast.parse(seams.PARENT.read_text());fn=next(n for n in original_tree.body if isinstance(n,ast.FunctionDef)and n.name=='audit')
  removed=[n for n in fn.body if isinstance(n,ast.If)and ast.unparse(n.test)=="task['seed'] in [10060001, 10060002]"];assert len(removed)==1;fn.body.remove(removed[0])
  expected_module=compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(C/'audit_seams.py'),'exec',dont_inherit=True)
  expected=next(v for v in expected_module.co_consts if isinstance(v,types.CodeType))
  seam=seams.fresh_phase_auditor(module,source);assert seams.code_identity(module.audit.__code__)==seams.code_identity(expected)
  changed=stub(seams.PARENT,'audit');changed.audit=lambda:None;refuse('changed_original_audit_code',lambda:seams.fresh_phase_auditor(changed,source))
  badsource=source.copy();badsource[str(seams.PARENT.relative_to(R))]='0'*64;refuse('changed_original_audit_source',lambda:seams.fresh_phase_auditor(stub(seams.PARENT,'audit'),badsource))
  admission=stub(seams.ADMISSION,'verify_source');binding=seams.bind_admission(admission,source,'no_onward');assert binding['original_numeric_verify_source_unchanged']
  class Ref:
   def __len__(self):return 2201
   def __getitem__(self,index):assert index==(-1,slice(None,2,None));return [.4,-.2]
  ref=Ref();x=dict(goal=[4.,-2.],packet=dict(native_tick=123,sim_time=1.23,controller_memory={'last_ctrl':[1.,2.], 'integral':.1}))
  selection=dict(method='refuge_onward',measured_onward_still_required=True,prefix_counts_as_whole_arrival=False,prefix_rows=[[0,0,2200,False]],rows=[[0,0,2200,False]],prefix_native=2200,admission=dict(passed=True,shadow_memory_reset=False))
  before=copy.deepcopy(x);local=seams.prefix_proof_input(x,selection,ref,'no_onward');assert local['goal']==[.4,-.2]and x==before and local['packet']==x['packet']
  assert seams.prefix_proof_input(x,dict(method='direct'),ref,'no_onward')is x
  assert seams.prefix_proof_input(x,dict(method='refuge_onward'),ref,'full')is x
  refuse('flagged_ablation_cannot_enter_full',lambda:seams.prefix_proof_input(x,selection,ref,'full'))
  missing=copy.deepcopy(selection);missing.pop('measured_onward_still_required');refuse('missing_ablation_scope_flag',lambda:seams.prefix_proof_input(x,missing,ref,'no_onward'))
  for key,value in [('prefix_counts_as_whole_arrival',True),('prefix_native',2),('rows',[]),('admission',{'passed':True,'shadow_memory_reset':True})]:
   bad=copy.deepcopy(selection);bad[key]=value;refuse('bad_prefix_'+key,lambda bad=bad:seams.prefix_proof_input(x,bad,ref,'no_onward'))
  full=dict(evidence_saved=True,replay={'passed':True},new_actual_native=2,fully_recorded_native=2,first_error=None,actual_original_goal_reached=True)
  assert audit.audit_kind(full)=='full_goal'
  assert audit.audit_kind(dict(full,first_error={'error':'SOFTWARE_METHOD_REFUSAL'}))=='prefix_safety_only'
  assert audit.audit_kind(dict(full,actual_original_goal_reached=False))=='prefix_safety_only'
  for key,value in [('new_actual_native',None),('new_actual_native',0),('new_actual_native',True),('fully_recorded_native',1),('model_native_inflight_unknown',True),('evidence_saved',False),('replay',{'passed':False})]:assert audit.audit_kind(dict(full,**{key:value}))=='unreviewable'
  owner=load('v1642_metadata_owner_source',C/'owner.py')
  refuse('owner_unsupported_route_before_once',lambda:owner.main('phase_09__full'))
  refuse('owner_missing_predecessor_barrier_before_once',lambda:owner.main('phase_01__no_onward'))
  assert not(ROOT/'rounds/phase_01__no_onward/ROUND_ONCE_CLAIM.json').exists()
  target=ROOT/'source_target';target.mkdir()
  current=read(R/'CURRENT_EXPERIMENT.json');owner.put(target/'SOFTWARE_CURRENT_START.json',current)
  normal_used=owner.PARENT_USED;owner.PARENT_USED=owner.PARENT_LIMIT-owner.PARENT_CLOSE_RESERVE-1
  refuse('normal_metadata_cannot_steal_close_reserve',lambda:owner.put(target/'FORBIDDEN_START.json',{}));assert not(target/'FORBIDDEN_START.json').exists()
  owner.PARENT_USED=normal_used;owner.PARENT_CLOSING=True;owner.put(target/'SOFTWARE_CURRENT_CLOSE.json',dict(current,models_now_authorized=False,active_round=None))
  close_used=owner.PARENT_CLOSED_USED;owner.PARENT_CLOSED_USED=owner.PARENT_CLOSE_RESERVE-1
  refuse('close_metadata_stays_bounded',lambda:owner.put(target/'FORBIDDEN_CLOSE.json',{}));owner.PARENT_CLOSED_USED=close_used
  # Execute only the exact production finally block, with explicit SOFTWARE
  # control paths/no child. It does not execute publication, Popen or models.
  owner_tree=ast.parse((C/'owner.py').read_text());main_fn=next(n for n in owner_tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
  outer=next(n for n in main_fn.body if isinstance(n,ast.Try));close_fn=ast.FunctionDef(name='software_close',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=copy.deepcopy(outer.finalbody),decorator_list=[])
  close_code=compile(ast.fix_missing_locations(ast.Module(body=[close_fn],type_ignores=[])),str(C/'owner.py')+':SOFTWARE_FINALLY_ONLY','exec')
  close_cases=[]
  for fail in [None,'APPROVAL.json','EVALUATION_LEDGER.json','CURRENT_EXPERIMENT.json']:
   soft=target/('close_'+str(len(close_cases)));(soft/'runs/v648_static_unknown').mkdir(parents=True);(soft/'runs/v648_static_unknown/execution.lock').touch();dest=soft/'round';dest.mkdir()
   put(soft/'CURRENT_EXPERIMENT.json',dict(active_round='SOFTWARE',models_now_authorized=True))
   result_case=dict(passed=True,first_error={'error':'SOFTWARE_PRIMARY'},secondary_errors=[],canonical_vehicle_initializations=None,actual_native=None,own_replay_native=None,formal_assignments_executed=1)
   calls=[]
   def soft_put(path,value):
    calls.append(path.name)
    if path.name==fail:raise OSError('SOFTWARE_SAVE_FAILURE:'+fail)
    return put(path,value)
   ns=vars(owner).copy();ns.update(R=soft,O=dest,put=soft_put,result=result_case,child=None,identity=None,review=soft/'REVIEW_PENDING',original=b'SOFTWARE_REVIEW_BYTES',cleared=False,started=time.monotonic())
   exec(close_code,ns);ns['software_close']()
   assert result_case['first_error']=={'error':'SOFTWARE_PRIMARY'}and result_case['actual_native']is None and not result_case['passed']
   assert(soft/'REVIEW_PENDING').read_bytes()==b'SOFTWARE_REVIEW_BYTES'
   assert all(name in calls for name in ['APPROVAL.json','EVALUATION_LEDGER.json','CURRENT_EXPERIMENT.json','COMPLETION.json'])
   close_cases.append(dict(failed_save=fail,all_close_stages_attempted=True,primary_preserved=True,unknown_preserved=True,secondary_errors=result_case['secondary_errors']))
  # Actual production entry/driver refuse before any numerical lazy binding.
  for name in ['entry.py','driver.py']:
   try:runpy.run_path(str(C/name),run_name='__main__')
   except AssertionError as error:assert str(error)=='REGISTERED_PHASE_ASSIGNMENT_NOT_ADMITTED'
   else:raise AssertionError('UNADMITTED_FORMAL_CLI_EXECUTED:'+name)
  put(target/'QUALIFICATION.json',dict(passed=True,source_only=True,registered_assignments=20,unique_tasks=12,qualified_case_id='WEST_EAST',qualified_variants=['full','no_onward'],formal_assignments_executed=0,negative_cases=negatives,source_code_only_old_audit_not_executed=True,historical_prefix_seam=seam,unchanged_safety_numeric_auditor_not_called=True,prefix_goal_scoped_no_input_mutation=True,full_direct_goal_unchanged=True,owner_normal_charged_bytes=normal_used,owner_close_charged_bytes=close_used,parent_limit_bytes=owner.PARENT_LIMIT,parent_close_reserve_bytes=owner.PARENT_CLOSE_RESERVE,software_close_cases=close_cases,models=0,FFI_loads=0,FFI_calls=0,physical_native=0,replay_native=0))
  put(ROOT/'SOURCE_FREEZE.json',dict(files=source,source_only=True,models_authorized=False))
  result.update(passed=True,source_members=len(source),qualified_case_id='WEST_EAST',qualified_variants=['full','no_onward'],negative_cases=len(negatives),qualified_registered_assignments=8,total_registered_assignments=20,formal_assignments_executed=0,unchanged_modules_reused=reused,real_CLI_missing_admission_refused=True,source_proof_sha256=sha(target/'QUALIFICATION.json'))
 except BaseException as error:
  sys.setprofile(None);result.update(first_error=repr(error),traceback=traceback.format_exc());put(ROOT/'FAILED_SOURCE_FREEZE.json',dict(files=source,models_authorized=False))
 finally:
  sys.setprofile(None);result.update(closed=True,wall_s=time.monotonic()-start);put(ROOT/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
