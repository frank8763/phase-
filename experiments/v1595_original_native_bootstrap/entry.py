"""Once new native environment/factory contract SOURCE check; no OS/model suite."""
import ast,copy,fcntl,importlib.abc,importlib.util,json,os,sys,time,traceback
from pathlib import Path
C=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('v1595_bootstrap_common',C/'common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)

def main():
 start=time.monotonic();resources=c.bootstrap();c.guard();lock=(c.R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(c.O/'ENTRY_ONCE_CLAIM.json').open('x')as f:json.dump(dict(unix=time.time(),models_authorized=False),f)
 result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,Allocator_recomputations=0,optimizer_calls=0,phase_FFI_loads=0,OS_library_loads=0,actual_runtime_qualified=False,complete_actual_source_target_passed=False,whole_route_passed=False)
 class NoNumerics(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','mujoco','OpenGL','torch','rclpy','factory','vehicle','kernel','runtime'}:raise AssertionError('BOOTSTRAP_SOURCE_IMPORT_FORBIDDEN:'+name)
 finder=NoNumerics();sys.meta_path.insert(0,finder)
 def profile(frame,event,arg):
  if event=='call':
   path=Path(frame.f_code.co_filename)
   if path.is_absolute()and path.is_relative_to(c.R):
    assert frame.f_code.co_name not in {'physical_binding','load_definitions','initial','all_future','create_vehicle'}
    assert not(path.name in {'engine.py','coupled_model.py','prediction.py','coupled_control.py'}and frame.f_code.co_name in {'__init__','compute','step','simulate'})
   assert time.monotonic()-start<120
 def audit(event,args):
  assert event!='ctypes.dlopen','BOOTSTRAP_SOURCE_NO_DLOPEN'
 sys.addaudithook(audit);sys.setprofile(profile)
 try:
  source=c.draft_sources();assert all(c.sha(c.R/n)==h for n,h in source.items())
  prior=c.read(c.R/'runs/v1592_ordered_phase_binding/ENTRY_QUALIFICATION.json');rec=c.read(c.R/'runs/v1592_ordered_phase_binding/CURRENT_SOURCE_REMOTE_RECOVERY.json')
  assert prior['passed']and prior['complete_actual_source_target_passed']and prior['models']==prior['physical_native']==0
  assert rec['all_frozen_members_remote_chain_covered']and rec['source_freeze_sha256']==c.sha(c.BASE)
  target=c.O/'source_target';target.mkdir();wm=c.load('v1595_original_writer',c.R/'experiments/v1436_pathlib_control_rename/writer_budget.py');io=c.load('v1595_original_boundary',c.R/'experiments/v1436_pathlib_control_rename/bounded_io.py');writer=wm.WriterBudget(target,role='PLANNER',maximum_bytes=2*1024**2,source_identity=c.sha(C/'entry.py'));negative=[]
  def refused(name,fn):
   try:fn()
   except(AssertionError,KeyError,ValueError)as error:negative.append(dict(name=name,error=repr(error)));return
   raise AssertionError('BOOTSTRAP_NEGATIVE_ACCEPTED:'+name)
  helper=c.load('v1595_real_original_bootstrap',C/'bootstrap_contract.py');task=c.read(C/'TASKS.json')[0]
  authority=dict(scope='REVISION12_FIRST_GOAL_BOUND_SEGMENT_ACTUAL_RUNTIME',scientific_revision=12,physical_authorized=True,models_authorized=True,whole_route_admission=False,repeat_authorized=False,absolute_deadline_unix=time.time()+60,software_only_not_an_actual_admission=True)
  with io.OutputBoundary(target,writer.reserve):
   env=helper.environment(source);assert env['PYOPENGL_PLATFORM']=='osmesa'and env['LD_LIBRARY_PATH'].startswith(str(c.R/'runs'))
   bad=dict(source);asset=c.read(C/'MESA_BINDING.json');bad[asset['real_path']]='0'*64
   refused('OSMesa_content_not_bound',lambda:helper.environment(bad))
   admitted=helper.factory_authority(authority,task=task,output=Path(task['output']));assert admitted['allowed_task_ids']==[task['task_id']]
   assert not(c.O/'ACTUAL_ADMISSION.json').exists()and not(c.O/'APPROVAL.json').exists()
   # Execute ONLY the original exact assertions before its first import, not
   # original create_vehicle or any OS/model initializer. The path is SOFTWARE.
   path=c.R/'experiments/v1067_causal_replan_brake_reserve/scene_binding.py';assert c.sha(path)==source[str(path.relative_to(c.R))]
   function=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='create_vehicle')
   nodes=[]
   for node in function.body:
    if isinstance(node,(ast.Import,ast.ImportFrom)):break
    nodes.append(node)
   assert len(nodes)==3 and isinstance(nodes[0],ast.Assign)and all(isinstance(n,ast.Assert)for n in nodes[1:])
   code=compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec');software=target/'SOFTWARE_FACTORY';software.mkdir()
   c.put(software/'APPROVAL.json',admitted)
   scope=dict(O=software,json=json,time=time,task=task);exec(code,scope);assert scope['approval']==admitted
   for name,key,value in [('wrong_allowed_task','allowed_task_ids',['OTHER']),('model_not_authorized','models_authorized',False),('factory_deadline_expired','absolute_deadline_unix',time.time()-1)]:
    bad=copy.deepcopy(admitted);bad[key]=value;c.put(software/'APPROVAL.json',bad);refused(name,lambda:exec(code,dict(O=software,json=json,time=time,task=task)))
   c.put(software/'APPROVAL.json',admitted)
   bad=copy.deepcopy(authority);bad['scope']='OLD_SCOPE';refused('wrong_actualscope',lambda:helper.factory_authority(bad,task=task,output=Path(task['output'])))
   bad=copy.deepcopy(authority);bad['allowed_task_ids']=['OTHER'];refused('no_preexisting_broad_tasklist',lambda:helper.factory_authority(bad,task=task,output=Path(task['output'])))
   # Production changes are exactly original env binding and same authority
   # root publication. All remaining numerical/policy/lifecycle source reused.
   base=c.R/'experiments/v1592_ordered_phase_binding';reused=[]
   for path in C.glob('*.py'):
    if path.name in {'entry.py','common.py','source_owner_entry.py','bootstrap_contract.py','source_cases.py','phase_cases.py','writer_coverage.py'}:continue
    before=(base/path.name).read_text();text=path.read_text().replace('v1595_original_native_bootstrap','v1592_ordered_phase_binding').replace('v1595','v1592')
    if path.name=='supervisor.py':
     oldline="c.put(c.O/'ACTUAL_ADMISSION.json',a);c.put(out/'APPROVAL.json',a);caps=c.read(C/'WRITER_CAPS.json')"
     newlines="bootstrap=c.load('v1592_original_native_bootstrap',C/'bootstrap_contract.py')\n a=bootstrap.factory_authority(a,task=task,output=out)\n c.put(c.O/'ACTUAL_ADMISSION.json',a);c.put(c.O/'APPROVAL.json',a);c.put(out/'APPROVAL.json',a);caps=c.read(C/'WRITER_CAPS.json')"
     before=before.replace(oldline,newlines)
     before=before.replace("e=dict(os.environ,CUDA_VISIBLE_DEVICES='',MUJOCO_GL='osmesa',LIBGL_ALWAYS_SOFTWARE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');e.pop('LD_PRELOAD',None)","e=bootstrap.environment(source)")
    assert ast.dump(ast.parse(before))==ast.dump(ast.parse(text)),path.name;reused.append(path.name)
   barrier=c.load('v1595_closed_previous_round_barrier',C/'round_barrier.py').before_next(c.read(c.R/'runs/v1382_weekend_campaign/LEDGER.json'),current_round=C.name)
   assert 'v1592_ordered_phase_binding'in barrier['reviewed_new_authority_rounds']
   c.put(target/'QUALIFICATION.json',dict(passed=True,source_only=True,negative_cases=negative,original_environment_source_SHA=asset['original_environment_source_sha256'],library_content_SHA=asset['real_sha256'],OSMesa_library_not_loaded=True,original_factory_prelude_AST_sha256=c.digest(ast.dump(ast.Module(body=nodes,type_ignores=[]))),SOFTWARE_factory_guard_positive=True,original_factory_not_called=True,production_source_reuse=reused,previousround_barrier=barrier,models=0,physical_native=0))
  assert all(c.sha(c.R/n)==h for n,h in source.items())
  c.put(c.O/'SOURCE_FREEZE.json',dict(files=source,base_manifest_sha256=c.sha(c.BASE),source_only=True,models_authorized=False,complete_actual_source_target_passed=True,actual_runtime_qualified=False,whole_route_passed=False),maximum=4*1024**2)
  result.update(passed=True,complete_actual_source_target_passed=True,source_gates=prior['source_gates'],writer_source_coverage=prior['writer_source_coverage'],source_members=len(source),negative_cases=len(negative),writer_charged_bytes=writer._read()['charged_bytes'],resources=resources,old_suites_reused_not_rerun=True,library_content_pinned_not_loaded=True)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  sys.setprofile(None);sys.meta_path.remove(finder);result.update(closed=True,wall_s=time.monotonic()-start);c.put(c.O/'ENTRY_QUALIFICATION.json',result);lock.close()
 print(json.dumps({k:result.get(k)for k in ['passed','closed','first_error','models','physical_native']}));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
