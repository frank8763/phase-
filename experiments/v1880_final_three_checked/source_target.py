"""One closure-order SOURCE: no model/policy/FFI/audit numerical execution."""
import ast,copy,fcntl,importlib.abc,json,os,sys,time,traceback,zipfile,math,types
from context import C,O,R,read,put,sha,load

def main():
 start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
 load('v1875_unchanged_immutable_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','torch','jax','ctypes','kernel','vehicle','factory','planner','fast_predict','scipy','OpenGL','rclpy'}:raise AssertionError('CLOSE_SOURCE_NO_NUMERICAL:'+name)
 sys.meta_path.insert(0,Ban())
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 files={};result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,optimizer_calls=0,source_only=True,actual_runtime_qualified=False)
 try:
  prior=R/'runs/v1866_remaining_common_matrix';rec=read(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json');assert rec['passed']and not rec['uncovered_members']
  assert read(prior/'SOURCE_QUALIFICATION.json')['passed']and read(prior/'SOURCE_OUTER_CLOSED.json')['passed']
  for n,h in read(prior/'POST_SOURCE_STORAGE_BARRIER.json')['proof_paths_SHA256'].items():assert sha(R/n)==h
  files.update(read(prior/'SOURCE_FREEZE.json')['files']);inherited=[dict(root=str(prior.relative_to(R)),freeze_sha256=sha(prior/'SOURCE_FREEZE.json'),recovery_path=str((prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(prior/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]
  for n,h in read(O/'PRIOR_CLOSED_BARRIERS.json')['proof_paths_SHA256'].items():assert sha(R/n)==h
  P=R/'experiments/v1879_capture_before_nplus1_checked';OLD=R/'experiments/v1865_remaining_routes_rpccr_ew'
  for name in ['v1879_capture_before_nplus1_checked','v1880_final_three_checked','v1881_final_three_source_recovery','v1882_final_three_runtime_recovery']:
   for p in(R/'experiments'/name).iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for name in ['AUTHORIZATION.json','PLAN_LOCKED.json','PILOT_TASK.json','PRIOR_CLOSED_BARRIERS.json','SAVED_SHAPE_BINDING.json']:
   p=O/name;files[str(p.relative_to(R))]=sha(p)
  for p in(O/'rounds').rglob('PILOT_TASK.json'):files[str(p.relative_to(R))]=sha(p)
  shape=read(O/'SAVED_SHAPE_BINDING.json');initial=R/shape['path'];assert sha(initial)==shape['sha256'];files[shape['path']]=shape['sha256']
  # New functions do not change numerical driver statements: source-equivalent
  # original block moved after exact CaptureBudget.finish only, with fresh grant.
  old=(OLD/'driver.py').read_text();begin=old.index('     if initial is not None:');end=old.index('     if capture is not None:',begin);block=old[begin:end];expected=old[:begin]+old[end:];idx=expected.index("     if result.get('evidence_saved')and not inside")
  block=block.replace('resources.prepare_closed_capture(quota,phase,inside)',"resources.prepare_nplus1_after_capture(quota,phase,inside,result.get('evidence_saved'))")
  expected=expected[:idx]+block+expected[idx:];assert expected==(P/'driver.py').read_text(),'UNRELATED_DRIVER_CHANGED'
  oldtree=ast.parse((OLD/'resources.py').read_text());newtree=ast.parse((P/'resources.py').read_text());assert ast.dump(ast.Module(body=newtree.body[:-1],type_ignores=[]),include_attributes=False)==ast.dump(oldtree,include_attributes=False)
  unchanged=[]
  for p in OLD.glob('*.py'):
   if p.name in {'driver.py','resources.py'}:continue
   q=P/p.name;text=p.read_text().replace(OLD.name,P.name).replace('v1866_remaining_common_matrix','v1880_final_three_checked')
   assert text==q.read_text(),'UNEXPECTED_CHANGE:'+p.name;unchanged.append(p.name)
  # Original finish does not consume/remove the in-memory rows used for Nplus1.
  vpath=R/'experiments/v858_nav2_verified/vehicle.py';assert files[str(vpath.relative_to(R))]==sha(vpath)
  tree=ast.parse(vpath.read_text());cl=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Vehicle');fn=next(n for n in cl.body if isinstance(n,ast.FunctionDef)and n.name=='finish')
  assert not any(isinstance(n,(ast.Assign,ast.AugAssign,ast.Delete))and 'self.rows' in ast.unparse(n).split('=')[0]for n in ast.walk(fn))
  assert 'self.rows.clear'not in ast.unparse(fn)and 'self.rows.pop'not in ast.unparse(fn)
  contract=load('v1875_fixed_original3_contract',C/'contract.py');plan=read(O/'PLAN_LOCKED.json');registry=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');assert contract.validate(plan,registry);boot=__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip();contract.time_admission(read(O/'AUTHORIZATION.json'),time.time(),boot)
  original=read(R/plan['previous_plan_path']);assert sha(R/plan['previous_plan_path'])==plan['previous_plan_sha256']
  ledger=read(R/'runs/v1805_common_algorithm_registry/LEDGER.json')
  for row in plan['assignments']:
   originalrow=next(r for r in original['assignments']if r['round_id']==row['round_id']);a=read(R/originalrow['output_root']/'PILOT_TASK.json');b=read(R/row['output_root']/'PILOT_TASK.json');assert {k:v for k,v in a.items()if k not in {'output','run_root','run_id'}}=={k:v for k,v in b.items()if k not in {'output','run_root','run_id'}}
   slot=next(x for x in ledger['slots']if x['method']==row['method']and x['task_id']==row['common_task']);assert not slot['registered']and not slot['closed']
  # Reproduce old conservative precharge rejection, using original quota and
  # exact Nplus1 byte count from saved headers. No large array or physical call.
  sizes={}
  with zipfile.ZipFile(initial)as archive:
   for name in archive.namelist():
    raw=archive.read(name);version=raw[6:8];hlen=int.from_bytes(raw[8:10]if version==b'\x01\x00'else raw[8:12],'little');off=10 if version==b'\x01\x00'else 12;header=ast.literal_eval(raw[off:off+hlen].decode().strip());descr=header['descr'];assert descr[-1]in '1248'and len(descr)<=4;sizes[name]=math.prod(header['shape'])*int(descr[2:])
  logical_per_state=sum(sizes.values());assert logical_per_state>0
  pending=lambda n:2*((n*logical_per_state+4095)//4096*4096)+65536+8192*len(sizes)
  sys.path.insert(0,str(P));from quota import EvidenceQuota,base
  resources=load('v1875_new_close_resources',P/'resources.py');oldresources=load('v1875_old_close_resources',OLD/'resources.py')
  root=O/'software_capture_fixture';root.mkdir();q=EvidenceQuota(root,read(R/'runs/v1643_formal_parent_metadata/LIMITS.json'));q.bind_external_names([]);q.write_enforcement_active=True
  resources.reserve_terminal(q);q.hold('canonical-physical-prefix',174*1024**2)
  oldresources.prepare_closed_capture(q,'normal',False)
  try:q.admit(pending(60001),'SOFTWARE_ORIGINAL_NPLUS1_PRECHARGE')
  except AssertionError as e:assert str(e)=='BYTE_GRANT_EXHAUSTED';red=repr(e)
  else:raise AssertionError('OLD_PRECAPTURE_RED_NOT_REPRODUCED')
  negatives=[]
  def refuse(name,fn):
   try:fn()
   except AssertionError:negatives.append(name)
   else:raise AssertionError('BAD_CLOSE_AUTHORITY:'+name)
  refuse('capture_hold_still_pending',lambda:resources.prepare_nplus1_after_capture(q,'normal',False,True))
  # Execute the EXACT original CaptureBudget.finish with explicit software
  # vehicle/write callback, not the physical finish method or simulator.
  sourcepath=R/'experiments/v1439_actual_ros_startup_close/capture_budget.py';tree=ast.parse(sourcepath.read_text());cl=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='CaptureBudget');fn=next(n for n in cl.body if isinstance(n,ast.FunctionDef)and n.name=='finish');space={};exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(sourcepath),'exec'),space)
  boundary=load('v1875_original_output_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');written=[]
  def charge(path,n):q.charge_write(path,n);written.append(n)
  def software_finish():
   (root/'SOFTWARE_CAPTURE_ONLY.bin').write_bytes(b'EXPLICIT_NO_MODEL_CAPTURE_FIXTURE\n'*64);return {'software_only':True}
  obj=types.SimpleNamespace(quota=q,key='canonical-physical-prefix',update=lambda _:174*1024**2)
  with boundary.OutputBoundary(root,charge):value=space['finish'](obj,types.SimpleNamespace(finish=software_finish))
  assert value['software_only']and 'canonical-physical-prefix'not in q.holds
  good=[]
  for n in [50935,60001]:
   resources.prepare_nplus1_after_capture(q,'normal',False,True);q.admit(pending(n),'SOFTWARE_FULL_LOGICAL_NPLUS1_PRECHARGE');good.append(dict(states=n,raw_state_bytes=n*logical_per_state,original_precharge_bytes=pending(n)))
  refuse('not_quiescent',lambda:resources.prepare_nplus1_after_capture(q,'normal',True,True))
  refuse('capture_not_saved',lambda:resources.prepare_nplus1_after_capture(q,'normal',False,False))
  refuse('wrong_phase',lambda:resources.prepare_nplus1_after_capture(q,'replay',False,True))
  refuse('no_full_task_capacity',lambda:resources.prepare(q,'COMPLETE_ZERO_TAIL_OR_CLOSURE',cap=224*1024**2,ttl=300))
  assert resources.TERMINAL_KEY in q.holds and q.holds[resources.TERMINAL_KEY]==1024**2
  proof=dict(passed=True,original_quota_red=red,original_capture_finish_function_executed_with_software_callback=True,physical_finish_not_called=True,exact_saved_shape_logical_bytes=logical_per_state,Nplus1_precharges=good,negative_cases=negatives,unchanged_numeric_modules=unchanged,only_driver_capture_before_Nplus1_order=True,original_capture_contents_and_original_NPZ_saver_unchanged=True,old_failed_RESULT_not_reconstructed=True,software_fixture_not_actual_capture=True,no_large_arrays_created=True,models=0,physical_native=0,FFI_calls=0,all_raw_IO_charged=bool(written))
  put(O/'CLOSE_ORDER_SOFTWARE_PROOF.json',proof)
  # Current production real admission/driver bootstrap across original3tasks.
  regression=load('v1875_actual_admission_software',C/'admission_regression.py').run(read,sha,load);assert regression['passed']and len(regression['valid_remaining_assignments'])==3;put(O/'VALID_ADMISSION_SOFTWARE_PROOF.json',regression)
  assert all(sha(R/n)==h for n,h in files.items());put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=inherited));put(O/'SOURCE_QUALIFICATION_PROOF.json',proof)
  put(O/'SOURCE_FREEZE.json',dict(files=files,models_authorized=False));result.update(passed=True,source_members=len(files),negative_cases=len(negatives)+len(regression['negative_cases']),valid_admission_software_cases=3)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=files,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
