"""One new source freeze; no JAX/SciPy/controller/model numerical calls."""
import ast,fcntl,json,os,subprocess,time,traceback
from pathlib import Path
from context import R,C,SOURCE,O,read,put,sha,load,predecessors_closed
P=R/'runs/v2099_svg_direct_array_scope'
def main():
 assert os.sched_getaffinity(0)=={2};locks=[]
 for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 assert not(SOURCE/'SOURCE_ONCE.json').exists();put(SOURCE/'SOURCE_ONCE.json',dict(unix=time.time(),models=0,pid=os.getpid()))
 result=dict(passed=False,closed=False,models=0,algorithm_DLLs=0,constructors=0,queries=0,physics=0,replay=0)
 try:
  predecessors_closed();prior=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in prior.items());files=dict(prior)
  proof=read(SOURCE/'COMPONENT_INTERFACE_PROOF.json');assert proof['passed']and proof['models']==proof['DLLs']==proof['physics']==proof['optimizer_queries']==0
  assert all(sha(R/n)==h for n,h in proof['source_pins'].items()),'SOFTWARE_CHECK_SOURCE_CHANGED'
  for n in proof['original_numeric_and_safety_modules_byte_exact']:assert (C/n).read_bytes()==(R/'experiments/v2099_svg_direct_array_scope'/n).read_bytes(),n
  old=R/'experiments/v2064_five_algorithm_parallel_math'
  assert(C/'optimizer_call.py').read_text()==(old/'optimizer_call.py').read_text().replace('runs/v2064_five_algorithm_parallel_math/PRIEST_ADMISSION.json','runs/v2101_parallel_priest_vehicle/vehicle/actual/PRIEST_OPTIMIZER_ADMISSION.json')
  for n in ['work_budget.py','thread_observation.py']:assert (C/n).read_text()==(old/n).read_text().replace('{7}','{6}').replace('[7]','[6]'),n
  # Real filter mount output writes are separate from the vehicle output.
  ns=load('source_filter_output_namespace',C/'filter_namespace.py');target=SOURCE/'filter_output';cmd=ns.command(C/'filter_worker.py',target);i=next(i for i,x in enumerate(cmd)if x.endswith('/envs/mk_mujoco/bin/python'))
  payload="from pathlib import Path;import os;assert os.sched_getaffinity(0)=={4};Path("+repr(str(target/'SOURCE_NAMESPACE_WRITE'))+").write_text('software')\nfor name in "+repr([str(C/'FORBIDDEN'),str(O/'FORBIDDEN'),str(R/'runs/v2099_svg_direct_array_scope/FORBIDDEN')])+":\n try:Path(name).write_text('forbidden')\n except OSError:pass\n else:raise AssertionError('FILTER_CROSS_LANE_WRITABLE')"
  p=subprocess.run(['taskset','-c','4',*cmd[:i],cmd[i],'-I','-B','-S','-c',payload],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,timeout=20);assert p.returncode==0,p.stderr.decode()
  for folder in [C,R/'experiments/v2102_parallel_priest_dispatch']:
   for p in folder.iterdir():
    if p.is_file():
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for n in proof['source_pins']:files[n]=sha(R/n)
  for p in SOURCE.iterdir():
   if p.is_file()and p.name not in {'SOURCE_ONCE.json'}:files[str(p.relative_to(R))]=sha(p)
  for p in (SOURCE/'software_fixture_04').iterdir():
   if p.is_file():files[str(p.relative_to(R))]=sha(p)
  for n in ['PILOT_TASK.json','LIMITS_DRAFT.json']:files[str((O/n).relative_to(R))]=sha(O/n)
  for n in ['COMPLETION.json','RUNTIME_CLOSED_REVIEW.json','POST_ROUND_STORAGE_BARRIER.json']:
   p=R/'runs/v2095_svg_common_full_route/rounds/common_02__SVGMPPI'/n;files[str(p.relative_to(R))]=sha(p)
  for p in [R/'experiments/v2062_bounded_dual_route_transport/net.py',R/'runs/v2062_bounded_dual_route_transport/SOFTWARE_RESULT.json']:files[str(p.relative_to(R))]=sha(p)
  assert not(O/'PILOT_ONCE_CLAIM.json').exists()and not(O/'COMPLETION.json').exists()and not(O/'actual').exists()and not(SOURCE/'PARALLEL_ONCE.json').exists()and not(SOURCE/'FILTERS_ADMISSION.json').exists()
  assert all((O/n).is_file()and(O/n).stat().st_size==0 for n in ['owner.lock','execution.lock'])
  registry=read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');task=read(O/'PILOT_TASK.json');original=next(x['task']for x in registry['tasks']if x['task']['task_id']=='common_01')
  for k,v in original.items():
   if k not in {'task_id','output','run_id','run_root','method','maximum_control_native','maximum_current_native_queries','maximum_plans'}:assert task[k]==v,k
  assert task['component_not_navigation']and not task['formal_common_task']and task['maximum_control_native']==5 and task['maximum_current_native_queries']==1 and task['stop_native']==2200
  limits=read(O/'LIMITS_DRAFT.json');assert limits['maximum_task_evidence_bytes']==224*1024**2 and limits['maximum_actual_native']==limits['maximum_replay_native']==60000 and limits['python_native_cap']==25000000 and limits['cpp_native_cap']==150000000
  reserve=load('component_source_reservation',C/'reserved_census.py').admission()
  assert read(R/'runs/v1942_sccr_applicability_decision/RESULT.json')['disposition']=='APPLICABILITY_BLOCKED_ORIGINAL_FULL_SCCR_SENSOR_CONTRACT'
  # No numerical fixture/control has been called by SOURCE. Original separate
  # formal registration remains untouched and the nonlinear fixture is explicit.
  assert 'nonlinear_unicycle_fixture_not_Phase=True'in(C/'filter_worker.py').read_text()
  assert all(sha(R/n)==h for n,h in files.items())and all(n not in prior or prior[n]==h for n,h in files.items())
  put(SOURCE/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  put(SOURCE/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
  result.update(passed=True,source_members=len(files),software_proof_sha256=sha(SOURCE/'COMPONENT_INTERFACE_PROOF.json'),source_members_added=len(files)-len(prior),formal_common_registered=0,PRIEST_scope='one fresh measured current original vehicle component',PSF_PCBF_scope='non-Phase nonlinear solver fixture only',original_author_call_byte_exact_except_admission_path=True,original_safety_and_vehicle_modules_byte_exact=True,reservation=reserve,Stage_reserved_cores_untouched=True)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(SOURCE/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 finally:
  result['closed']=True;put(SOURCE/'SOURCE_QUALIFICATION.json',result);put(SOURCE/'SOURCE_OUTER_CLOSED.json',dict(passed=result['passed'],closed=True,models=0,algorithm_DLLs=0,constructors=0,queries=0))
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
