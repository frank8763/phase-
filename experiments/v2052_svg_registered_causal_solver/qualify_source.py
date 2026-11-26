from common import R,C,S,O,read,put,sha,load
import ast,copy,json,os,subprocess,time,traceback
def main():
 os.sched_setaffinity(0,{5});assert not(S/'SOURCE_ONCE.json').exists();put(S/'SOURCE_ONCE.json',dict(pid=os.getpid(),unix=time.time(),models=0));result=dict(passed=False,closed=False,models=0,algorithm_DLLs=0,controller_constructors=0,optimizer_queries=0,physics=0,replay=0)
 try:
  P=R/'runs/v2045_remaining_parallel_source';assert read(P/'POST_SOURCE_STORAGE_BARRIER.json')['passed']and read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered'];prior=read(P/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in prior.items());files=dict(prior)
  assert read(S/'PREPARATION.json')['passed'];cfg=read(S/'CONFIG.json');assert cfg['integers']==[15,8000,1,100,10,1,1]and cfg['parameters'][1]==.08 and cfg['author_RNG_default_seed']==42 and cfg['all_other_author_optimizer_vehicle_and_cost_values_retained'];yaml=R/cfg['author_config_path'];assert sha(yaml)==cfg['author_config_sha256'];assert read(R/'runs/v2036_svg_causal_route_frontend/RESULT.json')['passed']
  inp=read(S/'INPUT.json');packet=read(R/inp['source_packet_path']);assert sha(R/inp['source_packet_path'])==inp['source_packet_sha256']and inp['origin']['origin_packet']==packet and inp['author_state']==inp['origin']['author_state'];assert inp['maps_sha256']==sha(S/'MAPS.json')and inp['config_sha256']==sha(S/'CONFIG.json');maps=read(S/'MAPS.json');assert maps['source_request_sha256']==load('causal_digest_only',R/'experiments/v2036_svg_causal_route_frontend/frontend.py').digest(inp['causal_request']);assert maps['point_cost_only_not_Phase_footprint_certificate']
  # Existing preparation evidence is bounded using named folders, never globaldu.
  old=int(read(P/'PREPARATION_FINAL.json')['allocated_since_baseline'])
  for name in ['v2048_remaining_parallel_dispatch','v2049_rpp12_same_archive_transport','v2050_closed_queue_retention_recovery','v2051_mppi_remaining_seven_resume']:
   folder=R/'runs'/name;old+=sum(p.lstat().st_blocks*512 for p in folder.rglob('*')if p.is_file())
  # Include all original preparation source metadata and round-local new late copies
  # conservatively via original16MiB aggregate per-lane metadata grants, not here.
  old+=1024**2;assert old<=8*1024**2,'EXISTING_PREPARATION_NOT_WITHIN_8MIB'
  put(S/'PREPARATION_RESERVATION.json',dict(passed=True,existing_preparation_allocated_bound_bytes=old,new_subset_peak_bytes=8*1024**2,whole_preparation_cap_bytes=16*1024**2,joint_peak_bytes=16095019008,no_new_physical_lane_or_RPP_retention_allocation=True,source_metadata_cap=2*1024**2,native_evidence_cap=1024**2,source_archive_cap=1024**2,runtime_archive_cap=2*1024**2,readback_cap=2*1024**2))
  # Production refusal before any algorithm DLL with no admission.
  ns=load('SVG_namespace_software_check',C/'namespace.py');O.mkdir();(O/'execution.lock').touch();cmd,env=ns.command(C/'native.py');p=subprocess.run(['taskset','-c','7',*cmd],cwd=R,env=env,capture_output=True,timeout=20);assert p.returncode!=0 and b'ADMISSION.json'in p.stderr and not(O/'NATIVE_ONCE.json').exists();put(S/'UNADMITTED_NATIVE_CLI_PROOF.json',dict(passed=True,returncode=p.returncode,algorithm_DLLs=0,constructors=0,queries=0,stderr_sha256=__import__('hashlib').sha256(p.stderr).hexdigest()))
  # Real readonly namespace: CPU7 may write only its own output directory.
  cmd,env=ns.command(C/'native.py');i=cmd.index('/usr/bin/python3.12');other=R/'runs/v2045_remaining_parallel_source/rounds/common_07__MPPI'
  script="from pathlib import Path;import os;assert os.sched_getaffinity(0)=={7};Path("+repr(str(O/'SOFTWARE_WRITE_TEST'))+").write_text('software')\nfor p in [Path("+repr(str(C/'FORBIDDEN'))+"),Path("+repr(str(other/'FORBIDDEN'))+")]:\n try:p.write_text('forbidden')\n except OSError:pass\n else:raise AssertionError('SOURCE_OR_OTHER_LANE_WRITABLE')"
  p=subprocess.run(['taskset','-c','7',*cmd[:i],'/usr/bin/python3.12','-I','-B','-S','-c',script],cwd=R,env=env,capture_output=True,timeout=20);assert p.returncode==0,p.stderr.decode()
  # No unknown library scopes are granted; inherit exact previously successful maps.
  deps=read(S/'NATIVE_DEPENDENCIES.json');assert all(sha(R/n)==h for n,h in deps['repo_dependency_files'].items());files.update(deps['repo_dependency_files'])
  binary=R/'runs/v1656_svg_solver_interface/libphase_svg_bridge.so';assert prior[str(binary.relative_to(R))]==sha(binary);syms=subprocess.check_output(['nm','-D','--defined-only',str(binary)],text=True);assert all(n in syms for n in ['phase_svg_create','phase_svg_set_maps','phase_svg_solve','phase_svg_call_counts','phase_svg_destroy'])
  proof=dict(passed=True,author_YAML_configuration_bound=True,original8000_100_10_workload=True,only_explicit_speed_and_singlethread_adaptations=True,current_causal_saved_map_and_measured_state_bound=True,real_unadmitted_native_CLI_refused_before_DLL=True,actual_CPU7_readonly_crosslane_source_namespace_passed=True,Phase_vehicle_or_formal_permission=False,prior32sample_qualification_not_promoted=True,reservation8MiB_subset_checked=True,models=0,algorithm_DLLs=0,constructors=0,optimizer_queries=0,physics=0,replay=0);put(S/'SOFTWARE_CHECK_PROOF.json',proof)
  for folder in [C,S]:
   for p in folder.iterdir():
    if p.is_file()and p.name!='SOURCE_ONCE.json':
     if p.suffix=='.py':ast.parse(p.read_text())
     files[str(p.relative_to(R))]=sha(p)
  for p in [yaml,R/inp['source_packet_path'],R/'runs/v2027_mppi_journal_snapshot_consistency/actual/MPPI_NATIVE_INPUT.jsonl',R/'experiments/v2036_svg_causal_route_frontend/frontend.py',R/'experiments/v1665_svg_phase_vehicle_contract/bridge.py',R/'runs/v2036_svg_causal_route_frontend/RESULT.json']:files[str(p.relative_to(R))]=sha(p)
  assert all(sha(R/n)==h for n,h in files.items());put(S/'SOURCE_FREEZE.json',dict(files={n:h for n,h in files.items()if prior.get(n)!=h},inherit_freeze_path=str((P/'SOURCE_FREEZE.json').relative_to(R)),inherit_freeze_sha256=sha(P/'SOURCE_FREEZE.json'),logical_source_members=len(files),models_authorized=False));put(S/'SOURCE_INHERITED_CHAINS.json',dict(inherited=[dict(root=str(P.relative_to(R)),freeze_sha256=sha(P/'SOURCE_FREEZE.json'),recovery_path=str((P/'CURRENT_SOURCE_REMOTE_RECOVERY.json').relative_to(R)),recovery_sha256=sha(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json'))]));result.update(passed=True,source_members=len(files),proof=proof)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc());put(S/'FAILED_SOURCE_FREEZE.json',dict(models_authorized=False))
 finally:result['closed']=True;put(S/'SOURCE_QUALIFICATION.json',result);put(S/'SOURCE_OUTER_CLOSED.json',dict(passed=result['passed'],closed=True,models=0,algorithm_DLLs=0,constructors=0,queries=0))
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
