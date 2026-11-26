"""New supervisor/source binding qualification, zero numerical calls."""
import ast,fcntl,json,os,subprocess,time,traceback
from pathlib import Path
import evidence as e
R=e.R;C=e.C;S=e.ROOT;P=R/'runs/v2101_parallel_priest_vehicle';SCI=R/'runs/v2099_svg_direct_array_scope';CASE=R/'runs/v2095_svg_common_full_route/rounds/common_03__SVGMPPI'
def main():
 assert os.sched_getaffinity(0)=={2};locks=[]
 for n in ['runs/v648_static_unknown/execution.lock','runs/v1643_formal_parent_metadata/OWNER.lock']:
  f=(R/n).open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
 assert e.sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 assert not(S/'SOURCE_ONCE.json').exists();e.put(S/'SOURCE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),models=0))
 result=dict(passed=False,closed=False,models=0,DLLs=0,constructors=0,optimizer_calls=0,physics=0,replay=0,formal_tasks_registered=0)
 try:
  supervisor=e.load('source_bound_next_supervisor',C/'supervisor.py');supervisor.predecessor();scientific=supervisor.original_source()
  prior=e.read(P/'SOURCE_FREEZE.json')['files'];assert all(e.sha(R/n)==h for n,h in prior.items());files=dict(prior)
  assert e.read(P/'POST_COMPONENT_STORAGE_BARRIER.json')['passed']and e.read(P/'FINAL_CHECKPOINT.json')['closed']
  for n,h in scientific.items():assert prior[n]==h
  task=e.read(CASE/'PILOT_TASK.json');registry=e.read(R/'runs/v1805_common_algorithm_registry/TASKS_METHODS_LOCKED.json');original=next(x['task']for x in registry['tasks']if x['task']['task_id']=='common_03')
  for k,v in original.items():
   if k not in {'task_id','output','run_id','run_root','method'}:assert task[k]==v,k
  assert task['formal_common_task']and not task['component_not_navigation']and task['maximum_control_native']==57600 and task['stop_native']==2200
  events=R/'runs/v1805_common_algorithm_registry/PARALLEL_METHOD_EVENTS'
  assert not(events/'common_03__SVGMPPI.REGISTERED.json').exists()and e.read(R/'runs/v2095_svg_common_full_route/RETENTION_STATE.json')['last']=='common_02__SVGMPPI'
  assert e.sha(CASE/'PILOT_TASK.json')==scientific[str((CASE/'PILOT_TASK.json').relative_to(R))]
  # Production entry rejects this new task before any DLL/model numerical import.
  for n in ['pilot_entry.py','run_phase.py']:
   p=subprocess.run(['taskset','-c','2','/usr/bin/python3','-B',str(R/'experiments/v2099_svg_direct_array_scope'/n)],cwd=R,env=dict(os.environ,PHASE_COMMON_ASSIGNMENT='common_03__SVGMPPI',PHASE_REPO=str(R)),capture_output=True,timeout=10)
   assert p.returncode!=0 and b'NOT_ADMITTED'in p.stderr,(n,p.stderr[-2000:])
  # Isolated CPU4 diagnostic refuses before SciPy when admission is absent.
  ns=e.load('source_bound_diagnostic_namespace',C/'namespace.py');cmd=ns.command(C/'math_worker.py',S/'math')
  env=dict(os.environ,PHASE_REPO=str(R),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1')
  p=subprocess.run(['taskset','-c','4',*cmd],cwd=R,env=env,capture_output=True,timeout=20);assert p.returncode!=0 and b'MATH_ADMISSION.json'in p.stderr,p.stderr.decode()
  idx=next(i for i,x in enumerate(cmd)if x.endswith('/envs/mk_mujoco/bin/python'))
  payload="from pathlib import Path;import os;assert os.sched_getaffinity(0)=={4};Path("+repr(str(S/'math/SOURCE_NAMESPACE_WRITE'))+").write_text('software')\nfor name in "+repr([str(C/'FORBIDDEN'),str(CASE/'FORBIDDEN'),str(P/'FORBIDDEN')])+":\n try:Path(name).write_text('forbidden')\n except OSError:pass\n else:raise AssertionError('DIAGNOSTIC_CROSS_LANE_WRITABLE')"
  p=subprocess.run(['taskset','-c','4',*cmd[:idx],cmd[idx],'-I','-B','-S','-c',payload],cwd=R,env=env,capture_output=True,timeout=20);assert p.returncode==0,p.stderr.decode()
  # Reuse all old software/numerical acceptance by SHA; never re-run old scope.
  assert (C/'namespace.py').read_text()==(R/'experiments/v2101_parallel_priest_vehicle/filter_namespace.py').read_text().replace('from context import R,C,SOURCE as S,load','from evidence import R,C,ROOT as S,load')
  original_nlp=R/'experiments/v2101_parallel_priest_vehicle/nonlinear_filter.py';assert prior[str(original_nlp.relative_to(R))]==e.sha(original_nlp)
  tree=ast.parse((C/'math_worker.py').read_text());calls=[x for x in ast.walk(tree)if isinstance(x,ast.Call)and isinstance(x.func,ast.Name)and x.func.id=='minimize'];assert len(calls)==1
  assert "result['NLP_attempts']==0"in(C/'math_worker.py').read_text()
  for folder in [C,S]:
   for p in folder.iterdir():
    if p.is_file()and p.name not in {'SOURCE_ONCE.json','owner.lock'}:
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=e.sha(p)
  for p in [R/'runs/v2103_svg03_pcbf_diagnosis/SOURCE_QUALIFICATION.json',R/'runs/v2103_svg03_pcbf_diagnosis/SOURCE_OUTER_CLOSED.json',R/'runs/v2103_svg03_pcbf_diagnosis/FAILED_SOURCE_FREEZE.json',P/'FINAL_CHECKPOINT.json',P/'POST_COMPONENT_STORAGE_BARRIER.json',P/'filter_output/RESULT.json',P/'filter_output/NONLINEAR_SOLVER_CASES.json',R/'runs/v2095_svg_common_full_route/rounds/common_02__SVGMPPI/POST_ROUND_STORAGE_BARRIER.json']:
   files[str(p.relative_to(R))]=e.sha(p)
  b=e.read(S/'BASELINE_DRAFT.json');reserve=e.load('new_next_case_reservation',C/'reserved_census.py').admission();old=e.read(SCI/'BASELINE_DRAFT.json')
  old_floor=old['quiescent_allruns_bytes']+sum(old[k]for k in ['preparation_bytes','retained_future_closed_bytes','metadata_bytes'])
  assert b['quiescent_allruns_bytes']+b['preparation_bytes']+b['parallel_math_bytes']<=old_floor,'ORIGINAL_SCIENTIFIC_STORAGE_GUARD_MUST_REMAIN_CONSERVATIVE'
  assert all(e.sha(R/n)==h for n,h in files.items())and all(n not in prior or prior[n]==h for n,h in files.items())
  e.put(S/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=e.sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False))
  e.put(S/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=e.sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=e.sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]))
  result.update(passed=True,source_members=len(files),source_delta_members=len(files)-len(prior),scientific_source_unchanged=True,scientific_source_members=len(scientific),original_case_common03_template_byte_exact=True,original_common120_ledger_unchanged=True,only_one_exposed_PCBF_auxiliary_NLP_allowed=True,negative_checks=['original_vehicle_entry_missing_admission','original_runtime_entry_missing_admission','diagnostic_missing_admission_before_SciPy','diagnostic_crosslane_readonly'],reservation=reserve,original_storage_guard_also_conservative=True)
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc());e.put(S/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 finally:
  result['closed']=True;e.put(S/'SOURCE_QUALIFICATION.json',result);e.put(S/'SOURCE_OUTER_CLOSED.json',dict(passed=result['passed'],closed=True,models=0,optimizer_calls=0,physics=0))
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
