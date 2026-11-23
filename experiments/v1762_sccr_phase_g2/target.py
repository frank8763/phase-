"""One separately named SCCR-PhaseG2 query; no vehicle or historical method retry."""
import ast,fcntl,importlib.abc,os,sys,time,traceback
from round_common import *
def main():
 mode='query'if '--query'in sys.argv else'source';start=time.monotonic()
 sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
 load('v1762_original_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'mujoco','torch','OpenGL','jax','rclpy','kernel','factory','vehicle','route_tools'}or(mode=='source'and name.split('.')[0]in {'numpy','ctypes','_ctypes'}):raise AssertionError('PHASE_G2_UNAUTHORIZED_IMPORT:'+name)
 sys.meta_path.insert(0,Ban())
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with(O/('QUERY_ONCE_CLAIM.json'if mode=='query'else'SOURCE_ONCE_CLAIM.json')).open('x')as f:f.write('{}\n')
  result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,full_original_SCCR_method_calls=0,adapted_query_attempts=0,adapted_query_returns=0,whole_navigation_passed=None,real_measured_receipt=False,method_identity='SCCR-PhaseG2-v1762')
  source=read(R/'runs/v1760_sccr_join_diagnosis/SOURCE_FREEZE.json')['files'].copy()
  try:
   barrier=read(R/'runs/v1760_sccr_join_diagnosis/POST_ROUND_STORAGE_BARRIER.json');assert barrier['passed']and all(sha(R/n)==h for n,h in barrier['proof_paths_SHA256'].items())
   for folder in [C,R/'experiments/v1763_sccr_query_source_recovery',R/'experiments/v1764_sccr_query_runtime_recovery']:
    for p in folder.iterdir():
     if p.is_file():
      if p.suffix=='.py':ast.parse(p.read_text())
      source[str(p.relative_to(R))]=sha(p)
   # Full inherited source/hash and historical anchors are checked by CPU5 owner;
   # the numerical target checks only immutable runtime/code and fixed-input files.
   assert all(sha(R/n)==h for n,h in source.items()if n.startswith(('experiments/','runtime/','current/'))),'RUNTIME_SOURCE_CHANGED'
   assert sha(C/'FIXED_FIXTURE.json')==sha(R/'experiments/v1751_sccr_original_query/FIXED_FIXTURE.json'),'FIXTURE_CHANGED'
   shape=load('v1762_phase_g2_shape',C/'shape_and_gate.py')
   if mode=='source':
    assert not(O/'CURRENT_QUERY_ADMISSION.json').exists();newproof=shape.qualify()
    tree=ast.parse((R/'runtime/mk-mini/navigation/phase22/continuous_corridor_planner.py').read_text());search=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='search_continuous_corridor');assert len([n for n in ast.walk(search)if isinstance(n,ast.Attribute)and n.attr=='feasible'])==1
    assert read(R/'runs/v1754_sccr_numpy_dependency/SOURCE_QUALIFICATION.json')['passed']
    put(O/'SOURCE_FREEZE.json',dict(files=source,models_authorized=False,new_method_identity='SCCR-PhaseG2-v1762'));result.update(passed=True,source_members=len(source),new_shape_software_proof=newproof,original_core_bytes_inherited=True,dependency_proof_reused_no_old_tests=True,adapted_numerical_query_not_yet_run=True)
   else:
    a=read(O/'CURRENT_QUERY_ADMISSION.json');assert a['query_authorized']and not a['physical_admission']and a['maximum_original_queries']==0 and a['maximum_adapted_search_calls']==1 and a['source_freeze_sha256']==sha(O/'SOURCE_FREEZE.json')
    assert a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and time.time()<a['deadline_unix']and time.monotonic()<a['deadline_monotonic']
    assert read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
    contract=load('v1762_original_causal_interface',R/'experiments/v1749_sccr_public_interface/contract.py');fixture=read(C/'FIXED_FIXTURE.json');config=read(R/'experiments/v1749_sccr_public_interface/PLANNER_CONFIG.json')['values'];payload=contract.causal_input(fixture['receipt'],fixture['known'],fixture['public_route'],config)
    put(O/'FIXED_QUERY_INPUT.json',dict(payload=payload,synthetic_software_fixture=True,real_measured_receipt=False,method_identity='SCCR-PhaseG2-v1762'))
    policy=load('v1762_reused_numpy_dependency_policy',R/'experiments/v1754_sccr_numpy_dependency/dependency_policy.py');bootstrap=policy.Bootstrap(read(R/'experiments/v1754_sccr_numpy_dependency/DEPENDENCY_PINS.json'));sys.addaudithook(bootstrap.audit)
    try:np=bootstrap.numpy_import()
    finally:put(O/'NUMPY_BOOTSTRAP.json',bootstrap.record())
    query=load('v1762_phase_g2_query',C/'adapted_query.py');result['adapted_query_attempts']=1
    answer,accounting=query.run(payload,source);result['adapted_query_returns']=1
    put(O/'ADAPTED_QUERY_RESPONSE.json',answer);put(O/'ADAPTED_SEARCH_ACCOUNTING.json',accounting);put(O/'NUMPY_BOOTSTRAP.json',bootstrap.record())
    baseline=read(R/'runs/v1754_sccr_numpy_dependency/ORIGINAL_QUERY_RESPONSE.json')
    result.update(passed=bool(answer.get('candidate_found')),candidate_found=answer.get('candidate_found'),candidate_evaluations=accounting['evaluations'],new_geometric_feasible=accounting['original_geometric_feasible'],new_phase_feasible=accounting['phase_feasible'],selected_phase_gate=answer.get('selected_phase_gate'),first_method_refusal=None if answer.get('candidate_found')else'NO_PHASE_ADMISSIBLE_CANDIDATE_IN_REGISTERED_FINITE_SEARCH',adapted_search_wall_s=answer['adapted_query_wall_s'],baseline_reused_not_rerun=dict(candidate_found=baseline['candidate_found'],candidate_count=baseline['candidate_count'],core_wall_s=baseline['wall_s'],path_phase_gate_refused=True),scope='SYNTHETIC_ONE_QUERY_ADAPTED_GEOMETRIC_COMPONENT_NOT_NAVIGATION',internal_numerical_work_unknown=True)
  except BaseException as error:
   result.update(first_error=repr(error),traceback=traceback.format_exc())
   if mode=='source':put(O/'FAILED_SOURCE_FREEZE.json',dict(files=source,models_authorized=False))
  finally:
   if(O/'NUMPY_BOOTSTRAP.json').exists():result['numpy_dependency_bootstrap']=read(O/'NUMPY_BOOTSTRAP.json')
   result.update(closed=True,wall_s=time.monotonic()-start);put(O/('QUERY_RESULT.json'if mode=='query'else'SOURCE_QUALIFICATION.json'),result)
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
