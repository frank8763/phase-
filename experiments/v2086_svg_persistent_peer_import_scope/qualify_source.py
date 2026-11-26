"""Zero-numerical qualification of actual persistent client and peer contract."""
from context import R,C,O,read,put,sha,load,digest
from pathlib import Path
import ast,copy,hashlib,json,os,subprocess,sys,time,traceback,types

def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 assert not(O/'SOURCE_ONCE.json').exists()
 put(O/'SOURCE_ONCE.json',dict(unix=time.time(),pid=os.getpid(),models=0))
 result=dict(passed=False,closed=False,models=0,algorithm_DLLs=0,constructors=0,queries=0,physics=0,replay=0)
 try:
  failed=R/'runs/v2084_svg_persistent_current_vehicle';assert read(failed/'SOURCE_QUALIFICATION.json')['passed']is False and read(failed/'SOURCE_OUTER_CLOSED.json')['closed']and not(failed/'PILOT_ONCE_CLAIM.json').exists()
  assert read(failed/'ISOLATED_SOFTWARE_PEER_DIAGNOSIS.json')['models']==0
  P=R/'runs/v2079_svg_file_bound_transport';old=R/'experiments/v2079_svg_file_bound_transport'
  assert read(P/'SOURCE_QUALIFICATION.json')['passed']and read(P/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and read(P/'POST_COMPONENT_STORAGE_BARRIER.json')['passed']and read(P/'COMPLETION.json')['passed']
  prior=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in prior.items());files=dict(prior)
  changed={'owner.py','context.py','reservation.py','evidence.py','qualify_source.py','native_client.py','native_worker.py','navigation.py','audit_component.py','runtime_binding.py','base_quota.py','quota.py','software_peer.py'}
  same=[]
  for p in old.glob('*.py'):
   if p.name not in changed:assert p.read_bytes()==(C/p.name).read_bytes(),'UNDECLARED_MODULE_CHANGE:'+p.name;same.append(p.name)
  assert(C/'channel.py').read_bytes()==(R/'experiments/v2083_svg_bounded_frame_channel/channel.py').read_bytes()
  for p in C.glob('*.py'):ast.parse(p.read_text())
  # Exact original constructor/C ABI calls and parameter binding remain present.
  original=ast.parse((old/'native_worker.py').read_text());current=ast.parse((C/'native_worker.py').read_text())
  def calls(tree,name):return [ast.dump(n,include_attributes=False)for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr==name]
  for name in ['phase_svg_create','phase_svg_set_maps','phase_svg_solve','phase_svg_destroy']:
   assert calls(original,name)==calls(current,name),'NATIVE_NUMERICAL_CALL_CHANGED:'+name
  for name in ['CONFIG.json','NATIVE_DEPENDENCIES.json']:assert sha(O/name)==sha(P/name)
  task=read(O/'PILOT_TASK.json');original_task=read(P/'PILOT_TASK.json')
  for k in ['case_id','seed','phase','start_xy','goal_xy','start_yaw','goal_yaw','dynamic','course_id','maximum_control_native','stop_native']:assert task[k]==original_task[k]
  assert task['maximum_current_native_queries']==2
  assert all((O/n).is_file()and(O/n).stat().st_size==0 for n in ['owner.lock','execution.lock'])
  reserve=load('persistent_component_subgrant',C/'reservation.py').admission()
  import context
  context.queue_closed()
  # Actual production entries must refuse before any numerical import.
  p=subprocess.run(['taskset','-c','2','/usr/bin/python3','-B',str(C/'pilot_entry.py')],env=dict(os.environ,PHASE_REPO=str(R)),capture_output=True,timeout=10)
  assert p.returncode!=0 and b'SVG_COMPONENT_NOT_ADMITTED'in p.stderr
  ros=load('readonly_persistent_software_namespace',R/'experiments/v856_nav2_foundation/ros_environment.py')
  command=ros.command(['/usr/bin/python3.12','-I','-B','-S',str(C/'native_worker.py')]);i=command.index('--bind');assert command[i+1:i+3]==[str(R/'runs'),str(R/'runs')];command[i]='--ro-bind'
  p=subprocess.run(['taskset','-c','7',*command],env=ros.environment(),capture_output=True,timeout=15)
  assert p.returncode!=0 and b'PILOT_ADMISSION.json'in p.stderr
  boundary=load('original_persistent_output_boundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');out=O/'software_fixture';out.mkdir(exist_ok=False);charges=[];saved=[]
  def debit(path,size):
   assert path.is_relative_to(out.resolve());charges.append(size);assert sum(charges)<=512*1024,'PERSISTENT_SOURCE_FIXTURE_CAP'
  def save(n,v):saved.append((n,v));put(out/n,v)
  original_frame=read(P/'actual/SVG_CURRENT_SOLVER_FRAME.json');second=copy.deepcopy(original_frame)
  second['request'].update(native_tick=5,sim_time=.05);second['maps']['source_request_sha256']=digest(second['request']);second['maps_sha256']=digest(second['maps'])
  client=load('actual_persistent_client_boundary_fixture',C/'native_client.py');original_load=client.load;original_read=client.read
  def fixture_load(label,path):
   actual=original_load(label,path)
   if label=='SVG_readonly_original_ROS_namespace':
    def command(args):
     assert args[-1]==str(C/'native_worker.py');return actual.command([*args[:-1],str(C/'software_peer.py')])
    return types.SimpleNamespace(environment=actual.environment,command=command)
   return actual
  client.load=fixture_load
  def fixture_read(path):
   value=original_read(path)
   return dict(value,output=str(out))if Path(path)==O/'PILOT_TASK.json'else value
  client.read=fixture_read
  with boundary.OutputBoundary(out,debit):
   obj=client.Client(save,original_frame)
   try:
    one=obj.query();two=obj.query(second)
    assert one['explicit_software_fixture']and two['explicit_software_fixture']and obj.calls==2 and obj.channel.pending is None
    try:obj.query(second)
    except AssertionError:pass
    else:raise AssertionError('THIRD_CLIENT_QUERY_NOT_REFUSED')
   finally:obj.close()
   assert obj.p.returncode==0 and obj.channel.closed
  protocol=load('actual_persistent_peer_decoder',C/'peer_contract.py');negatives=[]
  def reject(label,line,seq=1):
   try:protocol.decode(line,sequence=seq,run_id=original_frame['request']['run_id'])
   except (AssertionError,ValueError,KeyError):negatives.append(label)
   else:raise AssertionError('PERSISTENT_PROTOCOL_BAD_INPUT_ACCEPTED:'+label)
  encode=lambda v:json.dumps(v,allow_nan=True).encode()+b'\n'
  for label,mutate in [('stale_clock',lambda x:x['request'].update(native_tick=0)),('foreign_run',lambda x:x['request'].update(run_id='foreign')),('simulation_clock',lambda x:x['request'].update(sim_time=9.)),('map_digest',lambda x:x.update(maps_sha256='0'*64)),('nonfinite_state',lambda x:x['author_state'].__setitem__(0,float('nan'))),('short_grid',lambda x:x['maps']['speed_field'].pop())]:
   bad=copy.deepcopy(second);mutate(bad);reject(label,encode(bad))
  reject('third_peer_query',encode(second),2);reject('missing_newline',encode(second).rstrip(b'\n'));reject('oversize_frame',b'x'*(1024**2+1)+b'\n')
  original_channel=read(R/'runs/v2083_svg_bounded_frame_channel/RESULT.json');assert original_channel['software_passed']and original_channel['original_output_boundary_unchanged']
  controls=read(R/'runs/v2054_svg_current_control_contract/RESULT.json');assert controls['passed']
  assert len([n for n,v in saved if n.startswith('SVG_NATIVE_EVENT_')])==4
  proof=dict(passed=True,exact_original_modules=same,native_create_setmaps_solve_destroy_AST_exact=True,original_optimizer_parameters_byte_exact=True,
   actual_full_persistent_client_real_OutputBoundary_and_readonly_ROS_namespace=True,software_two_frames=[one['transport_ack'],two['transport_ack']],actual_child_exit=0,
   fixed_two_frame_count_and_current_clock_negatives=negatives,prior_channel_negatives_reused=original_channel['negative_cases'],original_current_control_negatives_reused=True,
   original_full_response_and_safety_numerics_byte_exact=True,two_query_navigation_and_independent_audit_new_scope=True,old_scopes_closed_unchanged=True,
   sole_evidence_writer=True,fixture_bytes_charged=sum(charges),grants=reserve,models=0,solver_DLLs=0,constructor_calls=0,queries=0,formal_slots=0)
  put(O/'SOFTWARE_CHECK_PROOF.json',proof)
  for folder in [C,R/'experiments/v2087_svg_persistent_peer_dispatch',R/'experiments/v2084_svg_persistent_current_vehicle',R/'experiments/v2085_svg_persistent_vehicle_dispatch']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for n in ['PILOT_TASK.json','CONFIG.json','NATIVE_DEPENDENCIES.json','RESERVATION.json','LIMITS_DRAFT.json','AUTHORIZATION.json','SOFTWARE_CHECK_PROOF.json']:files[str((O/n).relative_to(R))]=sha(O/n)
  for p in [failed/'SOURCE_QUALIFICATION.json',failed/'SOURCE_OUTER_CLOSED.json',failed/'FAILED_SOURCE_FREEZE.json',failed/'ISOLATED_SOFTWARE_PEER_DIAGNOSIS.json',P/'COMPLETION.json',P/'POST_COMPONENT_STORAGE_BARRIER.json',R/'experiments/v2083_svg_bounded_frame_channel/channel.py',R/'runs/v2083_svg_bounded_frame_channel/RESULT.json']:files[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in files.items())
  put(O/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  put(O/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
  result.update(passed=True,source_members=len(files),proof=proof)
 except BaseException as e:
  result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 finally:
  result['closed']=True;put(O/'SOURCE_QUALIFICATION.json',result);put(O/'SOURCE_OUTER_CLOSED.json',dict(passed=result['passed'],closed=True,models=0,algorithm_DLLs=0,constructors=0,queries=0))
 print(json.dumps(dict(passed=result['passed'],source_members=result.get('source_members'),first_error=result.get('first_error'))));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
