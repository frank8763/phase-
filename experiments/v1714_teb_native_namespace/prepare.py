"""One software namespace check and actual closed-material binding."""
import ast,importlib.util,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
def main():
 os.sched_setaffinity(0,{5});assert not(C/'CONFIG.json').exists()and not(O/'INPUT_BINDING.json').exists()
 s=importlib.util.spec_from_file_location('v1714_namespace_software',C/'namespace.py');n=importlib.util.module_from_spec(s);s.loader.exec_module(n);sha=n.sha;read=lambda p:json.loads(p.read_text())
 proof=read(O/'NAMESPACE_SOFTWARE_REVIEW.json');assert proof['passed']and proof['namespace_source_sha256']==sha(C/'namespace.py')
 base=R/'runs/v1712_root_member_materials';plan=read(base/'BATCHES_LOCKED.json');barriers=[];manifests=[];roots=[];files={}
 material_sources=[(base,task)for task in plan['batches'][:-1]]+[(R/'runs/v1716_catalog_directory_materials',plan['batches'][-1]),(R/'runs/v1718_poco_link_material',{'id':'04_poco_dev_01'})]
 for source_root,task in material_sources:
  p=source_root/'rounds'/task['id'];assert read(p/'RESULT.json')['passed'];v=read(p/'POST_ROUND_STORAGE_BARRIER.json');assert v['passed']and all(sha(R/k)==digest for k,digest in v['proof_paths_SHA256'].items());barriers.append(str((p/'POST_ROUND_STORAGE_BARRIER.json').relative_to(R)));manifests.append(str((p/'UNPACK_MANIFEST.json').relative_to(R)));roots.append(str((p/'sysroot').relative_to(R)))
  for name in ['RESULT.json','UNPACK_MANIFEST.json','POST_ROUND_STORAGE_BARRIER.json']:files[str((p/name).relative_to(R))]=sha(p/name)
 for name,digest in plan['host_tools_SHA256'].items():assert sha(Path(name))==digest
 prior=['runs/v1706_noetic_payload_intake/POST_ROUND_STORAGE_BARRIER.json','runs/v1698_local_cmake_toolchain/POST_ROUND_STORAGE_BARRIER.json']
 for name in prior:
  v=read(R/name);assert v['passed']and all(sha(R/k)==digest for k,digest in v['proof_paths_SHA256'].items());barriers.append(name)
 other=['runs/v1696_teb_author_build/AUTHOR_SOURCE_FREEZE.json','runs/v1706_noetic_payload_intake/UNPACK_MANIFEST.json','runs/v1698_local_cmake_toolchain/UNPACK_MANIFEST.json','runs/v1698_local_cmake_toolchain/RESULT.json']
 for name in other:files[name]=sha(R/name)
 tool=read(R/other[-1]);assert sha(R/tool['binary_path'])==tool['binary_sha256']
 binding=dict(files_SHA256=files,barriers=barriers,native_manifests=manifests,native_roots=roots,ros_manifest=other[1],cmake_manifest=other[2],ros_root='runs/v1706_noetic_payload_intake/sysroot/opt/ros/noetic',author_manifest=other[0],cmake_binary=tool['binary_path'],host_tools_SHA256=plan['host_tools_SHA256'],models=False)
 (O/'INPUT_BINDING.json').write_text(json.dumps(binding,indent=2)+'\n')
 source=[p for p in C.iterdir()if p.is_file()and p.name!='CONFIG.json'];config=dict(source_files_SHA256={str(p.relative_to(R)):sha(p)for p in source},input_binding_sha256=sha(O/'INPUT_BINDING.json'))
 for p in source:
  if p.suffix=='.py':ast.parse(p.read_text())
 (C/'CONFIG.json').write_text(json.dumps(config,indent=2)+'\n');used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used+(224+32+32+512)*1024**2<15*1024**3
 proof=dict(passed=True,scope='NEW_NAMESPACE_MAPPING_SOFTWARE_ONLY',native_same_byte_merge=True,exact_symbolic_link_literal=True,host_fallback_readonly=True,conflict_negative=True,all_required_material_barriers=True,allruns_bytes=used,peak_bytes=used+(224+32+32+512)*1024**2,models=0,compiler_calls=0,unix=time.time());(O/'PRELAUNCH_CHECKPOINT.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
