"""Select exact final-link records after static original-link declaration review."""
import ast,hashlib,importlib.util,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 os.sched_setaffinity(0,{5});assert not(C/'CONFIG.json').exists();read=lambda p:json.loads(p.read_text());prior=R/'runs/v1724_teb_focal_header_build';v=read(prior/'POST_ROUND_STORAGE_BARRIER.json');assert v['passed']and all(sha(R/k)==h for k,h in v['proof_paths_SHA256'].items())
 assert(C/'materials.py').read_bytes()==(R/'experiments/v1718_poco_link_material/materials.py').read_bytes()
 s=importlib.util.spec_from_file_location('v1726_link_inputs',C/'link_inputs.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);report=m.inventory(R,prior);assert set(report['missing_search_l_names'])=={'python3.8','boost_program_options'},report['missing_search_l_names'];assert set(report['missing_explicit_files'])=={'/usr/lib/x86_64-linux-gnu/libpython3.8.so','/usr/lib/x86_64-linux-gnu/libboost_program_options.so.1.71.0'}
 (O/'LINK_INPUT_SCOPE.json').write_text(json.dumps(report,indent=2)+'\n')
 source=R/'runs/v1708_focal_dependency_resolution/FULL_DECLARED_DEPENDENCY_PLAN.json';records=read(source)['packages'];names=['libpython3.8','libpython3.8-dev','libboost-program-options1.71.0','libboost-program-options1.71-dev'];packages=[next(x for x in records if x['Package']==name)for name in names]
 expected=['d47a54492e5ec7199d150c74d67b6fcec03bfbe2449bae340a107568df3ab861','a50ecdf8970df35f940f0417ce14d117d49165ef6bbcc0534c0ae5f195ee26d9','389095c7167251ee73667031a4c0f45083a31347cc95faddbdf5b7d22ac4c774','3151044dec2507392b0496f3c9886b0ed69b7fc0ba3cd55c355e9e5145999119'];assert[x['SHA256']for x in packages]==expected
 plan=read(R/'runs/v1718_poco_link_material/BATCHES_LOCKED.json');size=sum(int(x['Size'])for x in packages);installed=sum(int(x['Installed-Size'])*1024 for x in packages);plan.update(batches=[dict(id='06_python_boost_link_01',packages=packages,download_bytes=size,declared_installed_bytes=installed,predecessor=None)],total_packages=4,download_bytes=size,declared_installed_bytes=installed)
 for p in [source,C/'link_inputs.py',prior/'compile.console',prior/'build/CMakeFiles/teb_local_planner.dir/link.txt',prior/'build/CMakeFiles/teb_local_planner.dir/build.make',prior/'POST_ROUND_STORAGE_BARRIER.json']:plan['source_inputs_SHA256'][str(p.relative_to(R))]=sha(p)
 (O/'BATCHES_LOCKED.json').write_text(json.dumps(plan,indent=2)+'\n');(C/'CONFIG.json').write_text(json.dumps(dict(plan_sha256=sha(O/'BATCHES_LOCKED.json'),batch_ids=['06_python_boost_link_01'],task_cap_bytes=224*1024**2,metadata_root_cap_bytes=8*1024**2),indent=2)+'\n')
 proof=dict(passed=True,scope='UNCHANGED_SELECTED_MATERIAL_READER_AND_EXACT_ORIGINAL_LINK_INPUTS',reader_sha256=sha(C/'materials.py'),previous_software_review_sha256=sha(R/'runs/v1718_poco_link_material/SOFTWARE_REVIEW.json'),link_scope_sha256=sha(O/'LINK_INPUT_SCOPE.json'),new_software_cases=0,models=0);(O/'SOFTWARE_REVIEW.json').write_text(json.dumps(proof,indent=2)+'\n')
 files=[p for folder in [C,R/'experiments/v1727_python_boost_recovery']for p in folder.iterdir()if p.is_file()]
 for p in files:
  if p.suffix=='.py':ast.parse(p.read_text())
 used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used+(224+32+32+512)*1024**2<15*1024**3
 (O/'PRELAUNCH_CHECKPOINT.json').write_text(json.dumps(dict(source_files_SHA256={str(p.relative_to(R)):sha(p)for p in files},software_review_sha256=sha(O/'SOFTWARE_REVIEW.json'),packages=4,allruns_bytes=used,peak_bytes=used+(224+32+32+512)*1024**2,models=0,unix=time.time()),indent=2)+'\n');print(json.dumps(dict(packages=4,download_bytes=size,missing_search_l_names=report['missing_search_l_names'],models=0)))
if __name__=='__main__':main()
