"""run_phase CPU2 entry to the private native loader namespace."""
import fcntl,json,os,subprocess,sys,time,traceback
from context import C,O,R,read,put,sha,load
def main():
 start=time.monotonic();assert os.sched_getaffinity(0)=={2};sys.path.insert(0,str(R/'experiments/v1067_causal_replan_brake_reserve'));import resource_policy;resource_policy.apply();load('v1732_outer_original_guard',R/'experiments/v1504_priest_namespace_worker/common.py').guard(O)
 with(O/'SOURCE_ONCE_CLAIM.json').open('x')as f:f.write('{}\n')
 window=read(O/'ROUND_WINDOW.json');assert time.time()<window['normal_end_unix']and time.monotonic()<window['normal_end_monotonic']
 source=read(R/'runs/v1694_shared_observation_closure/SOURCE_FREEZE.json')['files'].copy();binding=read(O/'INPUT_BINDING.json');source.update(binding['files_SHA256'])
 for p in C.iterdir():
  if p.is_file():source[str(p.relative_to(R))]=sha(p)
 build=read(O/'BUILD_RESULT.json');assert build['passed'];source[build['binary_path']]=build['binary_sha256'];source[str((O/'BUILD_RESULT.json').relative_to(R))]=sha(O/'BUILD_RESULT.json');assert all(sha(R/k)==v for k,v in source.items())
 n=load('v1732_private_native_namespace',C/'native_namespace.py');command=n.command([n.PYTHON,'-I','-B','-S',str(C/'native_loader.py'),'--source-only']);put(O/'SOURCE_NATIVE_COMMAND.json',dict(argv=command,cpu=2,models_authorized=False))
 result=dict(passed=False,closed=False,models=0,physical_native=0,replay_native=0,optimizer_calls=0,complete_vehicle_qualified=False)
 try:
  p=subprocess.run(command,cwd=R,capture_output=True,timeout=90);(O/'native_source.console').write_bytes(p.stdout+p.stderr);assert p.returncode==0,('PRIVATE_NATIVE_SOURCE_REFUSED',p.returncode)
  native=read(O/'build/SOURCE_NATIVE_RESULT.json');assert native['passed']and native['planner_constructors']==native['optimizer_calls']==0
  assert all(sha(R/k)==v for k,v in source.items());put(O/'SOURCE_FREEZE.json',dict(files=source,external_SHA256=binding['external_SHA256'],source_only=True,models_authorized=False));result.update(passed=True,source_members=len(source),explicit_DLL_loads=native['explicit_DLL_loads'],metadata_FFI_calls=native['metadata_FFI_calls'],upstream_static_registration_count=None,all_loaded_dependency_identities_exact=True,C_POD_layout_qualified=True,planner_or_vehicle_config_qualified=False)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(O/'FAILED_SOURCE_FREEZE.json',dict(files=source))
 finally:result.update(closed=True,wall_s=time.monotonic()-start);put(O/'SOURCE_QUALIFICATION.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
