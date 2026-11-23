"""Once nonnumerical SCCR causal-interface and exact-code qualification."""
import ast,copy,fcntl,importlib.abc,os,runpy,sys,time,traceback,types,math
from context import C,O,R,read,sha,put,load

def main():
 start=time.monotonic();sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy
 resource_policy.apply();load('v1749_original_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in{'numpy','mujoco','torch','OpenGL','jax','rclpy','kernel','factory','vehicle','route_tools','ctypes'}:raise AssertionError('SCCR_SOURCE_NUMERICAL_IMPORT_FORBIDDEN:'+name)
 sys.meta_path.insert(0,Ban());lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 prior=R/'runs/v1744_formal_interface_qualification';source=read(prior/'SOURCE_FREEZE.json')['files'].copy();result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,FFI_loads=0,FFI_calls=0,original_SCCR_queries=0,source_only=True,actual_runtime_qualified=False)
 try:
  for case in ['phase_04__full','phase_04__no_onward']:
   b=read(R/'runs/v1643_formal_parent_metadata/rounds'/case/'POST_ROUND_STORAGE_BARRIER.json');assert b['passed']
   for x,y in [('closed_result_path','closed_result_sha256'),('remote_proof_path','remote_proof_sha256'),('cleanup_proof_path','cleanup_proof_sha256')]:assert sha(R/b[x])==b[y]
  pins=read(C/'PINNED_INPUTS.json')['files_SHA256'];assert all(sha(R/n)==h for n,h in pins.items());source.update(pins)
  for p in C.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in source.items())
  contract=load('v1749_public_contract',C/'contract.py');binding=load('v1749_original_binding',C/'binding.py')
  tree,helperproof=binding.helper_tree(source);assert len(helperproof)==6
  # Compile unchanged bodies with postponed annotations; never execute them.
  import __future__
  scope={};exec(compile(tree,str(C/'binding.py'),'exec',flags=__future__.annotations.compiler_flag,dont_inherit=True),scope);helpers=scope['OriginalGeometryHelpers']
  for path,names in binding.HELPERS.items():
   original=ast.parse((R/path).read_text())
   for name in names:
    node=next(v for v in ast.walk(original)if isinstance(v,ast.FunctionDef)and v.name==name);compiled=next(v for v in compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(node)],type_ignores=[])),str(R/path),'exec',flags=__future__.annotations.compiler_flag,dont_inherit=True).co_consts if isinstance(v,types.CodeType)and v.co_name==name)
    actual=helpers.__dict__[name];actual=actual.__func__ if isinstance(actual,staticmethod)else actual
    assert actual.__code__.co_code==compiled.co_code and actual.__code__.co_names==compiled.co_names and actual.__code__.co_consts==compiled.co_consts,'SCCR_HELPER_CODE_CHANGED'
  config=read(C/'PLANNER_CONFIG.json')['values']
  v4tree=ast.parse((R/binding.V4).read_text());init=next(v for v in ast.walk(v4tree)if isinstance(v,ast.FunctionDef)and v.name=='__init__');defaults={v.arg:ast.literal_eval(n)for v,n in zip(init.args.kwonlyargs,init.args.kw_defaults)if n is not None}
  for key in ['phase21_v4_min_known_margin','phase21_v4_min_sensor_margin','phase21_v4_max_p95_curvature','phase21_v4_max_heading_delta']:assert config[key]==defaults[key]
  worker=read(R/'evidence/phase22_formal/Final300/workers/phase22_v1_seed_22861.json');assert config['phase21_corridor_radius']==worker['runtime_attrs']['phase21_corridor_radius']
  positives=[];negatives=[]
  known=dict(known_rectangles=[[0.,0.,.2,.3]],known_circles=[[2.,2.,.1]])
  p=dict(native_tick=10,sim_time=.09999999999999,body=[0.,0.,0.,0.,0.],steering=dict(native_tick=10,measured_at=3.),body_measured_at=3.,sent_at=3.)
  scan=dict(native_tick=10,time=.09999999999999,xy=[0.,0.],yaw=0.,ranges=[1.]+[3.]*31)
  receipt=dict(schema='PHASE_CURRENT_MEASUREMENT_V1',packet_acquisitions=1,packet=p,packet_sha256=contract.digest(p),scan=scan,before_monotonic=2.9,after_monotonic=3.1)
  route=[[float(i),0.]for i in range(6)];old=copy.deepcopy(receipt);out=contract.causal_input(receipt,known,route,config);assert out['sensor_world_points']==[[1.,0.]]and receipt==old and not out['physical_admission'];positives.append('current_receipt_to_world_points_and_no_mutation')
  poisoned=copy.deepcopy(receipt);poisoned['packet'].update(actor_truth=[999.,999.],future_controls=[99.],hidden_actor_id='poison');poisoned['packet_sha256']=contract.digest(poisoned['packet']);out2=contract.causal_input(poisoned,known,route,config);assert out2['sensor_world_points']==out['sensor_world_points']and set(out2['observation'])==set(contract.PACKET_FIELDS);positives.append('nonwhitelisted_packet_fields_never_propagated')
  def reject(label,r=receipt,k=known,rr=route,cfg=config):
   try:contract.causal_input(r,k,rr,cfg)
   except(AssertionError,KeyError,ValueError,TypeError):negatives.append(label)
   else:raise AssertionError('SCCR_UNSAFE_INPUT_ACCEPTED:'+label)
  bad=copy.deepcopy(receipt);bad['scan']['actor_truth']=[0.,0.];reject('scan_truth_field',bad)
  bad=copy.deepcopy(receipt);bad['scan']['native_tick']=11;bad['scan']['time']=.11;reject('future_scan',bad)
  bad=copy.deepcopy(receipt);bad['scan']['native_tick']=4;bad['scan']['time']=.04;reject('stale_scan',bad)
  bad=copy.deepcopy(receipt);bad['packet_sha256']='bad';reject('packet_digest',bad)
  bad=copy.deepcopy(receipt);bad['packet_acquisitions']=2;reject('repeated_receipt',bad)
  bad=copy.deepcopy(receipt);bad['scan']['ranges'][0]=float('nan');reject('nonfinite_range',bad)
  bad=copy.deepcopy(receipt);bad['scan']['ranges']=bad['scan']['ranges'][:31];reject('short_scan',bad)
  bad=copy.deepcopy(receipt);bad['packet']['steering']['native_tick']=9;bad['packet_sha256']=contract.digest(bad['packet']);reject('steering_native_mismatch',bad)
  reject('hidden_map_geometry',k=dict(known,hidden_actor=[]));reject('short_route',rr=route[:5]);reject('parameter_tuning',cfg=dict(config,phase21_v4_min_known_margin=.01))
  proxy=binding.NoPlant(helpers,known,config,None)
  for key in ['model','d','sim','actor_truth','future','_phase21_v3_build_detour']:
   try:getattr(proxy,key)
   except AssertionError:negatives.append('no_plant_'+key)
   else:raise AssertionError('SCCR_UNDECLARED_ENV_ACCESS:'+key)
  try:runpy.run_path(str(C/'entry.py'),run_name='__main__')
  except AssertionError as e:assert str(e)=='SCCR_QUERY_NOT_ADMITTED';negatives.append('native_cli_before_numerical_import')
  else:raise AssertionError('UNADMITTED_SCCR_QUERY')
  planner=ast.parse((R/binding.PLANNER).read_text());attrs=sorted({v.attr for v in ast.walk(planner)if isinstance(v,ast.Attribute)and isinstance(v.value,ast.Name)and v.value.id=='env'})
  allowed=set(config)|{n for names in binding.HELPERS.values()for n in names};assert set(attrs)<=allowed,'SCCR_ORIGINAL_CORE_EXTRA_ENV_DEPENDENCY'
  proof=dict(passed=True,source_only=True,original_planner_not_executed=True,original_environment_not_constructed=True,helpers_AST_and_code_identity=helperproof,original_core_environment_attributes=attrs,constructor_threshold_defaults_unchanged=True,recorded_historical_corridor_radius_unchanged=True,query_trigger_and_map_adaptation_explicit=True,original_SAC_not_loaded=True,full_historical_SCCR_not_claimed=True,positive_cases=positives,negative_cases=negatives,models=0,physical_native=0,replay_native=0,original_planner_queries=0,automatic_next_round=False)
  target=O/'source_target';target.mkdir();put(target/'QUALIFICATION.json',proof);put(O/'SOURCE_FREEZE.json',dict(files=source,source_only=True,models_authorized=False));result.update(passed=True,source_members=len(source),negative_cases=len(negatives),source_proof_sha256=sha(target/'QUALIFICATION.json'))
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=source,models_authorized=False))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result);lock.close()
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
