"""Pin original signed C headers after a real compiler incompatibility."""
import ast,hashlib,importlib.util,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 os.sched_setaffinity(0,{5});assert not(C/'CONFIG.json').exists();read=lambda p:json.loads(p.read_text());old=R/'experiments/v1718_poco_link_material/materials.py';s=old.read_text();a=s.index('def selected(name):');b=s.index('def safe_link',a);expected=(s[:a]+"def selected(name):\n return name in ['usr','usr/include']or name.startswith('usr/include/')\n"+s[b:]).replace('STATIC_ARCHIVE_OR_DOCUMENTATION_NOT_SHARED_TEB_BUILD_INPUT','HEADER_ONLY_BUILD_INTERFACE_SELECTION');assert expected==(C/'materials.py').read_text()
 spec=importlib.util.spec_from_file_location('v1722_header_selector',C/'materials.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 positives=['usr','usr/include','usr/include/pthread.h','usr/include/x86_64-linux-gnu/bits/pthread_stack_min.h'];negatives=['usr/lib/x86_64-linux-gnu/crt1.o','usr/lib/x86_64-linux-gnu/libc_nonshared.a','usr/lib/x86_64-linux-gnu/libc.so','usr/bin/gencat','lib/x86_64-linux-gnu/libc.so.6','etc/ld.so.conf']
 assert all(m.selected(x)for x in positives)and not any(m.selected(x)for x in negatives)
 prior=R/'runs/v1720_teb_writable_mountpoints';v=read(prior/'POST_ROUND_STORAGE_BARRIER.json');assert v['passed']and all(sha(R/k)==h for k,h in v['proof_paths_SHA256'].items());assert read(prior/'RESULT.json')['configure_passed']and 'PTHREAD_STACK_MIN'in(prior/'compile.console').read_text()
 plan=read(R/'runs/v1718_poco_link_material/BATCHES_LOCKED.json');source=R/'runs/v1708_focal_dependency_resolution/FULL_DECLARED_DEPENDENCY_PLAN.json';records=read(source)['packages'];packages=[next(x for x in records if x['Package']==name)for name in ['libc6-dev','linux-libc-dev']]
 assert [x['SHA256']for x in packages]==['adb78f38fb00c76af4384be7a4c5f41da242e05bea6b0483e03b7e0c86738477','a7d59420134a8307eb11ef79b68e2b35cadc794a60f82c87f4583e37c763fd01']
 for p in [source,old,prior/'POST_ROUND_STORAGE_BARRIER.json',prior/'compile.console',R/'runs/v1716_catalog_directory_materials/SOFTWARE_REVIEW.json']:plan['source_inputs_SHA256'][str(p.relative_to(R))]=sha(p)
 size=sum(int(x['Size'])for x in packages);installed=sum(int(x['Installed-Size'])*1024 for x in packages);plan.update(batches=[dict(id='05_focal_headers_01',packages=packages,download_bytes=size,declared_installed_bytes=installed,predecessor=None)],total_packages=2,download_bytes=size,declared_installed_bytes=installed,selected_file_policy='ONLY usr/include/** and containing dirs. Raw debs retained; no CRT, linker script, runtime .so, .a or executable selected. Original host compiler/core runtime SHA unchanged; no complete Focal ABI proof.')
 (O/'BATCHES_LOCKED.json').write_text(json.dumps(plan,indent=2)+'\n');(C/'CONFIG.json').write_text(json.dumps(dict(plan_sha256=sha(O/'BATCHES_LOCKED.json'),batch_ids=['05_focal_headers_01'],task_cap_bytes=224*1024**2,metadata_root_cap_bytes=8*1024**2),indent=2)+'\n')
 proof=dict(passed=True,scope='EXACT_HEADER_SELECTOR_ONLY',positive_cases=positives,negative_cases=negatives,parser_meter_link_gates_unchanged=True,previous_software_proof_sha256=sha(R/'runs/v1716_catalog_directory_materials/SOFTWARE_REVIEW.json'),models=0);(O/'SOFTWARE_REVIEW.json').write_text(json.dumps(proof,indent=2)+'\n')
 files=[p for folder in [C,R/'experiments/v1723_focal_header_recovery']for p in folder.iterdir()if p.is_file()]
 for p in files:
  if p.suffix=='.py':ast.parse(p.read_text())
 used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used+(224+32+32+512)*1024**2<15*1024**3
 (O/'PRELAUNCH_CHECKPOINT.json').write_text(json.dumps(dict(source_files_SHA256={str(p.relative_to(R)):sha(p)for p in files},software_review_sha256=sha(O/'SOFTWARE_REVIEW.json'),packages=2,allruns_bytes=used,peak_bytes=used+(224+32+32+512)*1024**2,models=0,unix=time.time()),indent=2)+'\n');print(json.dumps(dict(packages=2,download_bytes=size,models=0)))
if __name__=='__main__':main()
