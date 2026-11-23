"""Freeze bounded shared-library build materials from existing signed metadata."""
import hashlib,importlib.util,json,os,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name;P=R/'runs/v1708_focal_dependency_resolution'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 assert not(O/'BATCHES_LOCKED.json').exists()and not(C/'CONFIG.json').exists()
 read=lambda p:json.loads(p.read_text());barrier=read(P/'POST_ROUND_STORAGE_BARRIER.json');assert barrier['passed']and all(sha(R/n)==h for n,h in barrier['proof_paths_SHA256'].items())
 m=load('v1710_materials',C/'materials.py');deb=load('v1708_exact_debian',R/'experiments/v1708_focal_dependency_resolution/debian.py')
 query=subprocess.run(['/usr/bin/dpkg-query','-W','-f=${binary:Package}\t${Version}\t${Status}\n',*m.HOST_PACKAGES],capture_output=True,text=True,timeout=10);assert query.returncode==0
 host={line.split('\t')[0].split(':')[0]:line.split('\t')[1]for line in query.stdout.splitlines()if line.endswith('install ok installed')};assert set(host)==set(m.HOST_PACKAGES);host['libstdc++-dev']=host['libstdc++-13-dev']
 records=read(P/'FULL_DECLARED_DEPENDENCY_PLAN.json')['packages'];base=read(P/'BUILD_CANDIDATE_PLAN.json');ros=read(R/'runs/v1704_signed_noetic_metadata/DEPENDENCY_PLAN.json')['packages'];already={x['Package']:x['Version']for x in ros}
 plan=deb.closure(base['roots']+['libpocofoundation62'],records,{**already,**host});assert not plan['unresolved']
 omitted=[x for x in plan['packages']if x['Package']=='libgraphblas3'];packages=[x for x in plan['packages']if x['Package']!='libgraphblas3']
 for edge in plan['edges']:
  locked=edge.pop('already_locked_ROS');edge['satisfied_by']='HOST_BUILD_TOOLCHAIN'if locked and edge['selected']in host else'LOCKED_ROS'if locked else'EXACT_NATIVE_PACKAGE'
 batches=[]
 for category in m.BATCHES:
  current=[];download=0;installed=0;ordinal=1
  for row in sorted((x for x in packages if m.batch(x['Package'])==category),key=lambda x:x['Package']):
   size=int(row['Size']);nominal=int(row.get('Installed-Size',0))*1024;assert size<=24*1024**2 and nominal<=144*1024**2
   if current and(download+size>24*1024**2 or installed+nominal>144*1024**2):
    batches.append(dict(id=category+'_'+str(ordinal).zfill(2),packages=current,download_bytes=download,declared_installed_bytes=installed));ordinal+=1;current=[];download=installed=0
   current.append(row);download+=size;installed+=nominal
  if current:batches.append(dict(id=category+'_'+str(ordinal).zfill(2),packages=current,download_bytes=download,declared_installed_bytes=installed))
 assert 1<=len(batches)<=12 and sum(len(x['packages'])for x in batches)==len(packages)
 for i,row in enumerate(batches):row['predecessor']=batches[i-1]['id']if i else None
 toolpaths=['/usr/bin/cc','/usr/bin/c++','/usr/bin/ld','/usr/bin/make','/usr/bin/pkg-config','/usr/bin/bwrap','/usr/lib/x86_64-linux-gnu/libc.so.6','/usr/lib/x86_64-linux-gnu/libstdc++.so.6','/usr/lib/x86_64-linux-gnu/libgcc_s.so.1']
 sourceinputs=[P/'FULL_DECLARED_DEPENDENCY_PLAN.json',P/'BUILD_CANDIDATE_PLAN.json',P/'ELF_DEPENDENCIES.json',P/'POST_ROUND_STORAGE_BARRIER.json',R/'runs/v1696_teb_author_build/source/cmake_modules/FindSUITESPARSE.cmake',R/'runs/v1696_teb_author_build/source/CMakeLists.txt',R/'experiments/v1708_focal_dependency_resolution/debian.py']
 locked=dict(batches=batches,total_packages=len(packages),download_bytes=sum(int(x['Size'])for x in packages),declared_installed_bytes=sum(int(x.get('Installed-Size',0))*1024 for x in packages),host_packages=host,host_query=query.stdout,host_tools_SHA256={p:sha(Path(p))for p in toolpaths},source_inputs_SHA256={str(p.relative_to(R)):sha(p)for p in sourceinputs},dependency_edges=plan['edges'],omitted_graphblas_package=omitted,omission_reason='Original FindSUITESPARSE shared-library list and all92ROS ELF dependencies have no GraphBLAS requirement; packaging installation is not claimed.',deferred_image_and_other_optional_ROS_dependencies='33externalSONAME inventory remains a superset; defer image/GL/Pythonextension-specific payloads until actual unchanged author target link evidence requires them.',selected_file_policy='Preserve headers/shared objects/CMake/pkgconfig/Python/tools, omit static.a and documentation/locale/debug only; complete original debs retained.',full_APT_or_ABI_or_build_qualification=False,models=0)
 raw=json.dumps(locked,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<4*1024**2;(O/'BATCHES_LOCKED.json').write_bytes(raw)
 (C/'CONFIG.json').write_text(json.dumps(dict(plan_sha256=sha(O/'BATCHES_LOCKED.json'),batch_ids=[x['id']for x in batches],task_cap_bytes=224*1024**2,metadata_root_cap_bytes=8*1024**2),indent=2)+'\n')
 print(json.dumps(dict(packages=len(packages),batches=[{k:v for k,v in x.items()if k!='packages'}for x in batches],download_bytes=locked['download_bytes'],declared_installed_bytes=locked['declared_installed_bytes'],models=0)))
if __name__=='__main__':main()
