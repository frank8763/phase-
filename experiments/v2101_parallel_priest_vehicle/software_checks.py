"""Bounded pure-software checks; original client and namespace, no optimizer."""
import ast,copy,hashlib,importlib.abc,json,os,subprocess,sys,time,traceback,types
from pathlib import Path
from context import R,C,SOURCE,O,read,put,sha,load,predecessors_closed,digest
P=R/'runs/v2099_svg_direct_array_scope'
def main():
 os.sched_setaffinity(0,{4});assert not(SOURCE/'SOURCE_ONCE.json').exists()
 out=SOURCE/'software_fixture_04';out.mkdir(exist_ok=False)
 result=dict(passed=False,models=0,DLLs=0,constructors=0,optimizer_queries=0,physics=0,replay=0,formal_trials=0)
 try:
  class Ban(importlib.abc.MetaPathFinder):
   def find_spec(self,n,*a):
    if n.split('.')[0]in{'mujoco','torch','jax','kernel','factory','vehicle','fast_predict','OpenGL'}:raise AssertionError('SOFTWARE_NO_MODEL_IMPORT:'+n)
  sys.meta_path.insert(0,Ban());import numpy as np
  predecessors_closed();source=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in source.items())
  fixture=R/'runs/v2090_svg_persistent_counter_fixture/actual'
  receipt=read(fixture/'cycle_0000_origin.json')['receipt'];selected=read(fixture/'SVG_SELECTED_SEGMENT.json')
  with np.load(fixture/'INITIAL_FULL_STATE.npz')as z:full={k:z[k].tolist()for k in z.files}
  builder=load('software_current_request',C/'current_request.py')
  frame=builder.build(np,receipt,full,selected,source,run_id='EXPLICIT_SOFTWARE_ONLY_NEVER_PHYSICAL')
  assert frame['request']['constructor_kwargs']['num_batch']==110 and frame['request']['constructor_kwargs']['maxiter_cem']==12 and not frame['request']['dynamic_points_world']
  assert 'fullstate'not in frame['current'] and 'qpos'not in frame['current']and not frame['current']['fullstate_or_actor_truth_transmitted']
  boundary=load('software_original_candidate',R/'experiments/v1485_priest_current_polynomial_seam/candidate_output.py');api=load('software_original_preview',R/'experiments/v2076_priest_current_control/interface.py')
  current=frame['current'];x,y,yaw=current['rear_pose_world'];assert abs(yaw)<1e-8
  reply=dict(kind='PRIEST_AUTHOR_POLYNOMIAL_PROPOSAL',schema=1,run_id=current['run_id'],input_sha256=current['input_sha256'],core_identity_sha256=current['core_identity_sha256'],origin_native=0,origin_sim_time=0.,horizon_s=10.,coordinate_frame='REAR_AXLE_WORLD_XY',gear=1,coefficients_x=[x+(__import__('math').comb(i,3)/120 if i>=3 else 0.)for i in range(11)],coefficients_y=[y]*11,optimizer_accounting=dict(optimizer_calls=0,iterations_completed=0,mathematical_candidate_evaluations=None,inflight_unknown=False,author_core_source_sha256=current['core_identity']['author_port']['author_sha256']))
  proposal=boundary.bind(current,reply);control=api.OriginPreview(current,proposal,source);preview=control.preview(current['origin']);assert abs(preview['raw_request'][0]-(.003*sum((i*10/99)**2 for i in range(6))/6))<1e-10 and abs(preview['raw_request'][1])<1e-10 and not preview['actual_execution_permitted']
  negatives=[]
  def reject(label,fn):
   try:fn()
   except (AssertionError,ValueError,KeyError):negatives.append(label)
   else:raise AssertionError('BAD_INPUT_ACCEPTED:'+label)
  reject('reused_preview',lambda:control.preview(current['origin']))
  foreign=copy.deepcopy(current['origin']);foreign['body'][0]+=.001
  reject('foreign_measured_packet',lambda:api.OriginPreview(current,proposal,source).preview(foreign))
  changed=copy.deepcopy(source);changed['experiments/v1485_priest_current_polynomial_seam/polynomial.py']='0'*64
  reject('changed_original_polynomial',lambda:api.OriginPreview(current,proposal,changed))
  altered=copy.deepcopy(receipt);altered['packet']['native_tick']=1
  reject('non_t0_receipt',lambda:builder.build(np,altered,full,selected,source,run_id='SOFTWARE'))
  reverse=copy.deepcopy(selected);reverse['gear']=-1
  reject('reverse_not_qualified',lambda:builder.build(np,receipt,full,reverse,source,run_id='SOFTWARE'))
  # Original actual client, quota boundary, charged regular stdin, actual readonly
  # bubblewrap CPU6 namespace. Only the explicit peer executable is substituted.
  client=load('software_actual_native_client',C/'native_client.py');original_read=client.read;original_load=client.load
  start=time.monotonic();now=time.time();window=dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),absolute_deadline_unix=now+5400,hard_stop_monotonic=start+5400,normal_end_unix=now+4200)
  def patched_read(p):
   if Path(p)==O/'PILOT_TASK.json':return dict(output=str(out))
   if Path(p)==O/'PILOT_WINDOW.json':return window
   return original_read(p)
  def patched_load(n,p):
   m=original_load(n,p)
   if Path(p)==C/'native_namespace.py':
    command=m.command
    m.command=lambda script,target:command(C/'software_peer.py',target)
   return m
  client.read=patched_read;client.load=patched_load
  io=load('software_original_OutputBoundary',R/'experiments/v1436_pathlib_control_rename/bounded_io.py');charged=[]
  def debit(p,n):
   assert Path(p).is_relative_to(out.resolve());charged.append(n);assert sum(charged)<=4*1024**2
  test=copy.deepcopy(frame);test['explicit_software_fixture']=True
  with io.OutputBoundary(out,debit):answer=client.solve(test,lambda n,v:put(out/n,v))
  assert answer['explicit_software_fixture']and answer['optimizer_queries']==answer['models']==0
  assert read(out/'PRIEST_NATIVE_PEER_IDENTITY.json')['CPU']==6
  assert read(out/'PRIEST_NATIVE_CLOSED.json')['returncode']==0
  assert not(C/'FORBIDDEN').exists()and not(SOURCE/'filter_output/FORBIDDEN').exists()
  for name in ['pilot_entry.py','run_phase.py']:
   p=subprocess.run(['taskset','-c','2','/usr/bin/python3','-B',str(C/name)],cwd=R,env=dict(os.environ,PHASE_REPO=str(R)),capture_output=True,timeout=10);assert p.returncode!=0 and b'NOT_ADMITTED'in p.stderr,(name,p.stderr[-2000:])
  for name,cpu,nsname,target,expected in [('native_worker.py',6,'native_namespace.py',out,b'PILOT_ADMISSION.json'),('filter_worker.py',4,'filter_namespace.py',SOURCE/'filter_output',b'FILTERS_ADMISSION.json')]:
   ns=load('software_denied_'+name,C/nsname);p=subprocess.run(['taskset','-c',str(cpu),*ns.command(C/name,target)],cwd=R,env=dict(os.environ,PHASE_REPO=str(R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'),capture_output=True,timeout=15);assert p.returncode!=0 and expected in p.stderr,(name,p.stderr[-2000:]);negatives.append(name+'_missing_admission_before_numerical_import')
  exact=[]
  original=R/'experiments/v2099_svg_direct_array_scope'
  for n in ['runtime_binding.py','history_binding.py','capture.py','resources.py','response.py','work.py','cpu_policy.py','resource_policy.py','base_quota.py','granted_quota.py','quota.py','error_stop.py','generic_audit.py','observation.py','compact_json.py','audit_budget.py','evidence_service.py','direct_bits.py']:
   assert (C/n).read_bytes()==(original/n).read_bytes(),n;exact.append(n)
  old=R/'experiments/v2064_five_algorithm_parallel_math'
  assert (C/'optimizer_call.py').read_text()==(old/'optimizer_call.py').read_text().replace('runs/v2064_five_algorithm_parallel_math/PRIEST_ADMISSION.json','runs/v2101_parallel_priest_vehicle/vehicle/actual/PRIEST_OPTIMIZER_ADMISSION.json')
  for n in ['work_budget.py','thread_observation.py']:assert (C/n).read_text()==(old/n).read_text().replace('{7}','{6}').replace('[7]','[6]'),n
  deps=read(R/'runs/v1491_priest_dependency_target/EXTRACTED_INDEX.json');assert all(source[x['path']]==x['sha256']==sha(R/x['path'])for x in deps['files'])
  from reserved_census import admission
  reserve=admission();pins={}
  for folder in [C,R/'experiments/v2102_parallel_priest_dispatch']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     pins[str(p.relative_to(R))]=sha(p)
  for p in [fixture/'cycle_0000_origin.json',fixture/'INITIAL_FULL_STATE.npz',fixture/'SVG_SELECTED_SEGMENT.json',O/'PILOT_TASK.json',O/'LIMITS_DRAFT.json',SOURCE/'BASELINE_DRAFT.json',SOURCE/'AUTHORIZATION.json',R/'runs/v2095_svg_common_full_route/rounds/common_02__SVGMPPI/POST_ROUND_STORAGE_BARRIER.json']:pins[str(p.relative_to(R))]=sha(p)
  result.update(passed=True,negative_cases=negatives,original_client_readonly_namespace_CPU6_actual=True,exact_charged_input_bytes=True,actual_model_free_software_peer=True,client_fixture_charged_bytes=sum(charged),new_current_input_rebuilt=True,fullstate_and_actor_truth_not_transmitted=True,original_preview_unclipped_request=preview['raw_request'],saved_fixture_never_installed_in_new_plant=True,original_numeric_and_safety_modules_byte_exact=exact,author_call_graph_exact_except_admission_path=True,dependency_members=len(deps['files']),reservation=reserve,source_pins=pins)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:result['closed']=True;put(SOURCE/'COMPONENT_INTERFACE_PROOF.json',result)
 print(json.dumps({k:result.get(k)for k in ['passed','first_error','models','client_fixture_charged_bytes']}));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
