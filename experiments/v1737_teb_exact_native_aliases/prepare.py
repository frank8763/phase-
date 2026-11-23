"""Freeze source and exact existing build/runtime inputs, no DLL or model load."""
import ast,fcntl,json,os,subprocess,time
from context import C,O,R,read,put,sha,load
def main():
 os.sched_setaffinity(0,{5});assert not(O/'INPUT_BINDING.json').exists()
 prior=R/'runs/v1728_teb_final_link_build';result=read(prior/'RESULT.json');assert result['passed']and result['source_SHA_unchanged']
 barrier=read(prior/'POST_ROUND_STORAGE_BARRIER.json');assert barrier['passed']and all(sha(R/n)==h for n,h in barrier['proof_paths_SHA256'].items())
 previous=R/'runs/v1735_teb_dependency_map_diagnosis/POST_ROUND_STORAGE_BARRIER.json';b=read(previous);assert b['passed']and all(sha(R/n)==h for n,h in b['proof_paths_SHA256'].items())
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 cur=read(R/'CURRENT_EXPERIMENT.json');assert cur['active_round']is None and not cur['models_now_authorized']
 graph=read(prior/'TRANSITIVE_LIBRARY_CANDIDATE.json');assert graph['all_needed_files_located']and len(graph['nodes'])==50
 paths=[prior/n for n in ['RESULT.json','AUTHOR_SOURCE_FREEZE.json','BUILT_LIBRARY_ELF_METADATA.json','TRANSITIVE_LIBRARY_CANDIDATE.json','POST_ROUND_STORAGE_BARRIER.json','INPUT_BINDING.json','NAMESPACE_MAPPING.json']]
 paths +=[R/'experiments/v1728_teb_final_link_build/namespace.py',R/'experiments/v1504_priest_namespace_worker/common.py',R/'experiments/v1447_full_module_guard_identity/guard_binding.py',R/'runtime/mk-mini/experiments/phase_rpccr_p0b3_v1/pilot.py']
 paths +=[R/'runs/v1732_teb_runtime_ref_binding/RUNTIME_CLOSED_REVIEW.json',R/'runs/v1732_teb_runtime_ref_binding/FAILED_SOURCE_FREEZE.json',R/'runs/v1732_teb_runtime_ref_binding/build/libphase_teb_bridge.so',R/'runs/v1732_teb_runtime_ref_binding/BUILD_RESULT.json',previous,R/'runs/v1730_teb_runtime_binding/PREENTRY_COMPLETION.json',R/'runs/v1731_teb_runtime_recovery/SOURCE_SYNC_RESULT.json',R/'runs/v1731_teb_runtime_recovery/PREENTRY_REMOTE_REF_PROOF.json'];sources={str(p.relative_to(R)):sha(p)for p in paths};external={}
 for row in graph['nodes']:
  p=__import__('pathlib').Path(row['path'])if row['path'].startswith('/')else R/row['path'];assert sha(p)==row['sha256']
  (external if p.is_absolute()and not p.is_relative_to(R)else sources)[str(p)if not p.is_relative_to(R)else str(p.relative_to(R))]=row['sha256']
 python=__import__('pathlib').Path('/home/linghu/miniconda3/envs/mk_mujoco/bin/python');external[str(python)]=sha(python)
 # Native view link text is immutable; no broad filesystem or numerical suite.
 for row in read(prior/'NAMESPACE_MAPPING.json')['records']:
  p=prior/'view'/row['path'].lstrip('/');expected=row.get('target')if row['kind']=='EXACT_NATIVE_SYMLINK'else'/tmp/phase-host/'+row['source'].lstrip('/')if row['kind']=='HOST_READONLY_PROXY'else str(R/row['source']);assert p.is_symlink()and os.readlink(p)==expected
 for name in ['homotopy_class_planner.cpp','teb_local_planner_ros.cpp']:
  p=prior/'source/src'/name;sources[str(p.relative_to(R))]=sha(p)
 header=prior/'source/include/teb_local_planner/teb_config.h';text=header.read_text();assert 'hcp.enable_homotopy_class_planning = true;'in text and 'hcp.enable_multithreading = true;'in text
 identity=dict(author_commit='9e55af4724310c34bcfa8cbb3b2783478c1a246a',proposal_class='teb_local_planner::HomotopyClassPlanner',full_ROS_plugin=False,original_homotopy_default=True,resource_adaptation='enable_multithreading=false; all other unoverridden author defaults retained',original_rng_initialization='std::random_device; no seed/reset API',numerical_or_vehicle_config_admitted=False,vehicle_config_and_causal_obstacle_mapping_pending=True)
 put(O/'ALGORITHM_IDENTITY.json',identity);sources[str(header.relative_to(R))]=sha(header)
 diagnosis_path=R/'runs/v1735_teb_dependency_map_diagnosis/build/DEPENDENCY_MAP_DIAGNOSIS.json';diagnosis=read(diagnosis_path);sources[str(diagnosis_path.relative_to(R))]=sha(diagnosis_path)
 missing=diagnosis['missing_expected'];assert len(missing)==3
 aliases=[]
 names={'libuuid.so.1.3.0':'libuuid.so.1.3.0','libexpat.so.1.6.11':'libexpat.so.1.12.1','libz.so.1.2.11':'libz.so.1.3.2'}
 for row in missing:
  target='/home/linghu/miniconda3/envs/mk_mujoco/lib/'+names[__import__('pathlib').Path(row['path']).name]
  actual=next(x for x in diagnosis['new_mappings']if x['mapped_path']==target)
  assert actual['path_stat_matches_mapping']and sha(__import__('pathlib').Path(target))==actual['sha256']and sha(R/row['path'])==row['sha256']
  assert not any(x['mapped_path']==target for x in diagnosis['baseline'])
  aliases.append(dict(source=row['path'],sha256=row['sha256'],target=target,original_target_sha256=actual['sha256']))
 put(O/'EXACT_NATIVE_ALIASES.json',dict(aliases=aliases,readonly_private_mounts_only=True,source_diagnosis_sha256=sha(diagnosis_path),underlying_conda_files_unchanged=True));sources[str((O/'EXACT_NATIVE_ALIASES.json').relative_to(R))]=sha(O/'EXACT_NATIVE_ALIASES.json')
 sources[str((O/'RPATH_DIAGNOSIS.json').relative_to(R))]=sha(O/'RPATH_DIAGNOSIS.json')
 namespace=load('v1737_alias_argv_review',C/'native_namespace.py');argv=namespace.command(['/usr/bin/true']);mounts=[argv[i+1:i+3]for i,x in enumerate(argv)if x=='--ro-bind']
 assert all([str(R/row['source']),row['target']]in mounts for row in aliases)
 assert sum(1 for pair in mounts if pair[1]in {row['target']for row in aliases})==3
 assert argv[-1]=='/usr/bin/true'and all(argv.index(row['target'])<argv.index('--remount-ro')for row in aliases)
 put(O/'ALIAS_COMMAND_REVIEW.json',dict(passed=True,only_3_observed_readonly_aliases=True,argv_generated_not_executed=True,compiler_or_DLL_or_model_calls=0));sources[str((O/'ALIAS_COMMAND_REVIEW.json').relative_to(R))]=sha(O/'ALIAS_COMMAND_REVIEW.json')
 for p in C.iterdir():
  if p.is_file():
   if p.suffix=='.py':ast.parse(p.read_text())
   sources[str(p.relative_to(R))]=sha(p)
 build=read(R/'runs/v1732_teb_runtime_ref_binding/BUILD_RESULT.json');assert build['passed']and sha(R/build['binary_path'])==build['binary_sha256'];build.update(reused_exact_prior_binary=True,compiler_calls_this_round=0);put(O/'BINARY_BINDING.json',build)
 put(O/'INPUT_BINDING.json',dict(files_SHA256=sources,external_SHA256=external,prior_build_root=str(prior.relative_to(R)),all50_library_files_SHA_bound=True,models_authorized=False))
 for name in ['build','tmp','build/empty_cwd','build/home']:(O/name).mkdir(parents=True,exist_ok=True)
 used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used+(224+32+32+512)*1024**2<15*1024**3
 put(O/'PREPARATION_CHECKPOINT02.json',dict(prepared=True,source_imported_only_pure_helpers=True,compiled=False,SOURCE_qualified=False,models_authorized=False,allruns_bytes=used,peak_bytes=used+(224+32+32+512)*1024**2,input_binding_sha256=sha(O/'INPUT_BINDING.json'),unix=time.time()))
 print(json.dumps(dict(prepared=True,dependencies=50,models=0)))
if __name__=='__main__':main()
