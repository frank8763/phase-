"""One new sampled SCCR path-to-Phase mapping experiment; zero numerical propagation."""
import ast,fcntl,importlib.abc,os,sys,time,traceback
from round_common import *
def main():
 mode='query'if '--query'in sys.argv else 'source';start=time.monotonic()
 sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply()
 load('v1757_immutable_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 class Ban(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'numpy','ctypes','_ctypes','mujoco','torch','OpenGL','jax','rclpy','kernel','factory','vehicle','route_tools'}:raise AssertionError('PATH_GATE_NUMERICAL_DEPENDENCY_FORBIDDEN:'+name)
 sys.meta_path.insert(0,Ban())
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with(O/('QUERY_ONCE_CLAIM.json'if mode=='query'else'SOURCE_ONCE_CLAIM.json')).open('x')as f:f.write('{}\n')
  result=dict(passed=False,closed=False,models=0,analytical_native=0,physical_native=0,replay_native=0,original_SCCR_query_attempts=0,original_SCCR_query_returns=0,path_gate_attempts=0,path_gate_returns=0,whole_navigation_passed=None,real_measured_receipt=False,scope='SAMPLED_SYNTHETIC_PATH_REQUEST_GATE'if mode=='query'else'SOURCE_ONLY_PATH_REQUEST_INTERFACE')
  source=read(R/'runs/v1754_sccr_numpy_dependency/SOURCE_FREEZE.json')['files'].copy()
  try:
   prior=read(R/'runs/v1754_sccr_numpy_dependency/POST_ROUND_STORAGE_BARRIER.json');assert prior['passed']and all(sha(R/n)==h for n,h in prior['proof_paths_SHA256'].items())
   source.update(read(C/'PINNED_INPUTS.json')['files_SHA256'])
   for folder in [C,R/'experiments/v1758_sccr_query_source_recovery',R/'experiments/v1759_sccr_query_runtime_recovery']:
    for p in folder.iterdir():
     if p.is_file():
      if p.suffix=='.py':ast.parse(p.read_text())
      source[str(p.relative_to(R))]=sha(p)
   assert all(sha(R/n)==h for n,h in source.items()),'SOURCE_CHANGED'
   fixture=read(C/'PATH_FIXTURE.json');assert sha(R/fixture['original_query_response_path'])==fixture['original_query_response_sha256']and fixture['selected_path']==read(R/fixture['original_query_response_path'])['selected_path']
   gate=load('v1757_new_path_mapping',C/'path_gate.py')
   if mode=='source':
    assert not(O/'CURRENT_QUERY_ADMISSION.json').exists();negatives=gate.qualify()
    old_proof=read(R/'runs/v1665_svg_phase_vehicle_contract/SOURCE_QUALIFICATION.json');old_freeze=read(R/'runs/v1665_svg_phase_vehicle_contract/SOURCE_FREEZE.json')['files'];assert old_proof['passed'] and old_freeze['experiments/v1665_svg_phase_vehicle_contract/bridge.py']==sha(R/'experiments/v1665_svg_phase_vehicle_contract/bridge.py')
    put(O/'SOURCE_FREEZE.json',dict(files=source,source_only=True,models_authorized=False));result.update(passed=True,source_members=len(source),new_path_negative_cases=negatives,original_bridge_proof_reused_without_requalifying=True,candidate_response_SHA_verified=True,geometry_mapping_not_yet_run=True)
   else:
    a=read(O/'CURRENT_QUERY_ADMISSION.json');assert a['query_authorized']and not a['physical_admission']and a['source_freeze_sha256']==sha(O/'SOURCE_FREEZE.json')and a['maximum_original_queries']==0 and a['maximum_path_gate_runs']==1
    assert a['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip()and time.time()<a['deadline_unix']and time.monotonic()<a['deadline_monotonic']
    assert read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
    bridge=load('v1757_original_vehicle_request_bridge',R/'experiments/v1665_svg_phase_vehicle_contract/bridge.py')
    result['path_gate_attempts']=1;mark=time.monotonic();answer=gate.run(fixture,bridge);elapsed=time.monotonic()-mark
    put(O/'PATH_REQUEST_GATE.json',answer);result.update(passed=answer['passed'],path_gate_returns=1,path_mapping_wall_s=elapsed,geometry_samples=answer['geometry_samples'],mapped_samples_before_first_refusal=answer['mapped_samples_before_first_refusal'],sampled_max_abs_center_steering_rad=answer['sampled_max_abs_center_steering_rad'],original_center_cap_rad=answer['original_center_cap_rad'],first_refusal=answer['first_refusal'],original_bridge_used=True,physical_admission=False,continuous_path_feasibility_unknown=True,no_tracking_controller_defined=True)
  except BaseException as error:
   result.update(first_error=repr(error),traceback=traceback.format_exc())
   if mode=='source':put(O/'FAILED_SOURCE_FREEZE.json',dict(files=source,models_authorized=False))
  finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/('QUERY_RESULT.json'if mode=='query'else'SOURCE_QUALIFICATION.json'),result)
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
