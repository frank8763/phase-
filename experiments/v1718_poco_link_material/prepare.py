"""Select one exact missing development link from already signed metadata."""
import ast,hashlib,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 os.sched_setaffinity(0,{5});assert not(C/'CONFIG.json').exists();read=lambda p:json.loads(p.read_text());old=R/'runs/v1716_catalog_directory_materials';plan=read(old/'BATCHES_LOCKED.json')
 assert (C/'materials.py').read_bytes()==(R/'experiments/v1716_catalog_directory_materials/materials.py').read_bytes();assert read(old/'SOFTWARE_REVIEW.json')['passed']
 prior=old/'rounds/03_runtime_base_01';v=read(prior/'POST_ROUND_STORAGE_BARRIER.json');assert v['passed']and all(sha(R/k)==h for k,h in v['proof_paths_SHA256'].items());assert read(prior/'RESULT.json')['passed']
 source=R/'runs/v1708_focal_dependency_resolution/FULL_DECLARED_DEPENDENCY_PLAN.json';pkg=next(x for x in read(source)['packages']if x['Package']=='libpoco-dev');assert pkg['SHA256']=='f6d63efab3b71e64467058f6eff225777ab35a1f85ab4c140070b1c05e615231'and int(pkg['Size'])==523992
 original=R/'runs/v1706_noetic_payload_intake/sysroot/opt/ros/noetic/share/class_loader/cmake/class_loaderConfig.cmake';assert '/usr/lib/x86_64-linux-gnu/libPocoFoundation.so;'in original.read_text()
 for p in [source,original,old/'SOFTWARE_REVIEW.json',prior/'POST_ROUND_STORAGE_BARRIER.json']:plan['source_inputs_SHA256'][str(p.relative_to(R))]=sha(p)
 plan.update(batches=[dict(id='04_poco_dev_01',packages=[pkg],download_bytes=int(pkg['Size']),declared_installed_bytes=int(pkg['Installed-Size'])*1024,predecessor=None)],total_packages=1,download_bytes=int(pkg['Size']),declared_installed_bytes=int(pkg['Installed-Size'])*1024)
 (O/'BATCHES_LOCKED.json').write_text(json.dumps(plan,indent=2)+'\n');(C/'CONFIG.json').write_text(json.dumps(dict(plan_sha256=sha(O/'BATCHES_LOCKED.json'),batch_ids=['04_poco_dev_01'],task_cap_bytes=224*1024**2,metadata_root_cap_bytes=8*1024**2),indent=2)+'\n')
 proof=dict(passed=True,scope='UNCHANGED_READER_PROOF_REUSE_AND_EXACT_ADDITIONAL_DEV_LINK',reader_sha256=sha(C/'materials.py'),prior_software_review_sha256=sha(old/'SOFTWARE_REVIEW.json'),original_class_loader_config_sha256=sha(original),new_software_cases=0,models=0);(O/'SOFTWARE_REVIEW.json').write_text(json.dumps(proof,indent=2)+'\n')
 files=[p for folder in [C,R/'experiments/v1719_poco_material_recovery']for p in folder.iterdir()if p.is_file()]
 for p in files:
  if p.suffix=='.py':ast.parse(p.read_text())
 used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);peak=used+(224+32+32+512)*1024**2;assert peak<15*1024**3
 (O/'PRELAUNCH_CHECKPOINT.json').write_text(json.dumps(dict(source_files_SHA256={str(p.relative_to(R)):sha(p)for p in files},software_review_sha256=sha(O/'SOFTWARE_REVIEW.json'),packages=1,allruns_bytes=used,peak_bytes=peak,models=0,unix=time.time()),indent=2)+'\n');print(json.dumps(dict(packages=1,models=0,peak_bytes=peak)))
if __name__=='__main__':main()
