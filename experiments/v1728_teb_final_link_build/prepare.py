"""Reuse proven compile source; bind only original final-link material delta."""
import ast,hashlib,importlib.util,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;P=R/'runs/v1724_teb_focal_header_build'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 os.sched_setaffinity(0,{5});assert not(C/'CONFIG.json').exists();read=lambda p:json.loads(p.read_text());old=R/'experiments/v1724_teb_focal_header_build'
 assert(C/'namespace.py').read_bytes()==(old/'namespace.py').read_bytes()and(C/'owner.py').read_text()==(old/'owner.py').read_text().replace('v1725_teb_header_build_recovery','v1729_teb_final_build_recovery').replace('v1724_exact_namespace','v1728_exact_namespace')
 assert read(P/'LINK_BOUNDARY_DIAGNOSIS.json')['all9_author_objects_compiled'];inputs=read(P/'INPUT_BINDING.json');material=R/'runs/v1726_python_boost_link_material/rounds/06_python_boost_link_01';assert read(material/'RESULT.json')['passed']
 inputs['native_roots'].append(str((material/'sysroot').relative_to(R)));inputs['native_manifests'].append(str((material/'UNPACK_MANIFEST.json').relative_to(R)))
 for p in [P/'POST_ROUND_STORAGE_BARRIER.json',material/'POST_ROUND_STORAGE_BARRIER.json']:
  v=read(p);assert v['passed']and all(sha(R/k)==h for k,h in v['proof_paths_SHA256'].items());inputs['barriers'].append(str(p.relative_to(R)))
 for p in [P/'RESULT.json',P/'LINK_BOUNDARY_DIAGNOSIS.json',material/'RESULT.json',material/'UNPACK_MANIFEST.json',material/'POST_ROUND_STORAGE_BARRIER.json']:inputs['files_SHA256'][str(p.relative_to(R))]=sha(p)
 helper=R/'experiments/v1726_python_boost_link_material/link_inputs.py';assert sha(helper)==read(material/'ONCE_CLAIM.json')['source_files_SHA256'][str(helper.relative_to(R))];inputs['files_SHA256'][str(helper.relative_to(R))]=sha(helper)
 assert all(sha(R/k)==h for k,h in inputs['files_SHA256'].items());(O/'INPUT_BINDING.json').write_text(json.dumps(inputs,indent=2)+'\n')
 probe=O/'link_input_probe';(probe/'build/CMakeFiles/teb_local_planner.dir').mkdir(parents=True);(probe/'INPUT_BINDING.json').write_text(json.dumps(inputs,indent=2)+'\n')
 for name in ['link.txt','build.make']:(probe/'build/CMakeFiles/teb_local_planner.dir'/name).write_bytes((P/'build/CMakeFiles/teb_local_planner.dir'/name).read_bytes())
 spec=importlib.util.spec_from_file_location('v1728_exact_link_input_reader',helper);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);scope=m.inventory(R,probe);assert not scope['missing_explicit_files']and not scope['missing_search_l_names'];(O/'STATIC_FINAL_LINK_INPUT_SCOPE.json').write_text(json.dumps(scope,indent=2)+'\n')
 proof=dict(passed=True,scope='UNCHANGED_ORIGINAL_SOURCE_AND_ACTUAL_COMPILE_NAMESPACE_REUSE',namespace_sha256=sha(C/'namespace.py'),actual9object_proof_sha256=sha(P/'LINK_BOUNDARY_DIAGNOSIS.json'),new_link_material_manifest_sha256=sha(material/'UNPACK_MANIFEST.json'),new_software_cases=0,models=0,compiler_calls=0);(O/'NAMESPACE_SOFTWARE_REVIEW.json').write_text(json.dumps(proof,indent=2)+'\n')
 files=[p for p in C.iterdir()if p.is_file()and p.name!='CONFIG.json']
 for p in files:
  if p.suffix=='.py':ast.parse(p.read_text())
 (C/'CONFIG.json').write_text(json.dumps(dict(source_files_SHA256={str(p.relative_to(R)):sha(p)for p in files},input_binding_sha256=sha(O/'INPUT_BINDING.json')),indent=2)+'\n');used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used+(224+32+32+512)*1024**2<15*1024**3
 (O/'PRELAUNCH_CHECKPOINT.json').write_text(json.dumps(dict(passed=True,allruns_bytes=used,peak_bytes=used+(224+32+32+512)*1024**2,models=0,unix=time.time()),indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
