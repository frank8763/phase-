"""Static ELF and signed Ubuntu Focal metadata; no package or model execution."""
import fcntl,hashlib,importlib.util,json,lzma,os,re,signal,subprocess,time,traceback,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
P=R/'runs/v1706_noetic_payload_intake';S=R/'runs/v1704_signed_noetic_metadata';D=R/'runs/v1709_focal_metadata_recovery'
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def allocation():return O.lstat().st_blocks*512+sum(p.lstat().st_blocks*512 for p in O.rglob('*'))
def put(p,v):
 raw=json.dumps(v,indent=2,allow_nan=False).encode()+b'\n';assert allocation()+((len(raw)+4095)//4096)*4096+1024**2<32*1024**2,'METADATA32_CAP'
 t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(raw);t.replace(p)
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 for n in ['ONCE_CLAIM.json','RESULT.json','OWNED_CHILD.json']:assert not(O/n).exists()
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 cur=read(R/'CURRENT_EXPERIMENT.json');assert cur['active_round']is None and not cur['models_now_authorized']
 barrier=read(P/'POST_ROUND_STORAGE_BARRIER.json');assert barrier['passed']and all(sha(R/n)==h for n,h in barrier['proof_paths_SHA256'].items())
 assert not Path('/proc',str(read(P/'ONCE_CLAIM.json')['owner_pid'])).exists()
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 source=read(D/'SYNC_RESULT.json');assert source['remote_verified']and source['push_executed']
 sources=[C/n for n in ['owner.py','elf.py','debian.py','PROTOCOL.md']]
 for p in sources:assert subprocess.check_output(['git','show',source['head']+':'+str(p.relative_to(R))],cwd=R)==p.read_bytes()
 used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used+608*1024**2<15*1024**3
 now=time.time();start=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 def guard():assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.time()<now+1200 and time.monotonic()<start+1200,'FOCAL_METADATA_DUAL_CLOCK'
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('FOCAL_METADATA1200_HARD_STOP')));signal.setitimer(signal.ITIMER_REAL,1200)
 put(O/'ONCE_CLAIM.json',dict(owner_pid=os.getpid(),unix=now,monotonic=start,boot_id=boot,source_files_SHA256={str(p.relative_to(R)):sha(p)for p in sources},source_commit=source['head'],allruns_bytes=used,prior_barrier_sha256=sha(P/'POST_ROUND_STORAGE_BARRIER.json'),models_authorized=False))
 put(O/'ROUND_WINDOW.json',dict(started_unix=now,started_monotonic=start,metadata_end_unix=now+1200,metadata_end_monotonic=start+1200,root_end_unix=now+5400,root_end_monotonic=start+5400,boot_id=boot))
 result=dict(closed=False,passed=False,models=0,compiler_calls=0,optimizer_calls=0,physical_native=0,replay_native=0,package_downloads=0,package_executions=0,method_executed=False,method_outcome=None,first_error=None)
 requests=[];attempts=[]
 def fetch(url,path,size=None,digest=None):
  guard();assert url.startswith(('https://mirrors.tuna.tsinghua.edu.cn/ubuntu/','https://archive.ubuntu.com/ubuntu/'));row=dict(url=url,path=str(path.relative_to(R)),passed=False)
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Phase-bounded-Focal-build-metadata','Accept-Encoding':'identity'}),timeout=30)as response:
    assert response.geturl().startswith(('https://mirrors.tuna.tsinghua.edu.cn/ubuntu/','https://archive.ubuntu.com/ubuntu/'));data=bytearray()
    while True:
     guard();block=response.read(128*1024)
     if not block:break
     assert len(data)+len(block)<=min(16*1024**2,size or 16*1024**2);data.extend(block)
   assert(size is None or len(data)==size)and(digest is None or hashlib.sha256(data).hexdigest()==digest),'RELEASE_INDEX_SHA_SIZE'
   assert allocation()+((len(data)+4095)//4096)*4096+2*1024**2<32*1024**2
   with path.open('xb')as f:f.write(data)
   row.update(passed=True,bytes=len(data),sha256=sha(path));return bytes(data)
  except BaseException as error:row['error']=repr(error);raise
  finally:requests.append(row);put(O/'REQUESTS.json',requests)
 try:
  elf=load('v1708_static_ELF_only',C/'elf.py');deb=load('v1708_debian_metadata_only',C/'debian.py');manifest=read(P/'UNPACK_MANIFEST.json');inventory=[]
  for row in manifest['entries'].values():
   guard()
   if row['type']not in ['regular','hardlink']:continue
   p=R/row['path'];assert sha(p)==row['sha256']and p.stat().st_size==row['bytes']
   with p.open('rb')as f:magic=f.read(4)
   if magic==b'\x7fELF':
    item=elf.dynamic_metadata(p);assert item['sha256']==row['sha256'];item['path']=str(p.relative_to(R));item['owners']=row['owners'];inventory.append(item)
  provided={x['soname']for x in inventory if x['soname']};needed=sorted({v for x in inventory for v in x['needed']}-provided)
  put(O/'ELF_DEPENDENCIES.json',dict(files=inventory,ROS_provided_SONAMEs=sorted(provided),external_SONAMEs=needed,source_manifest_sha256=sha(P/'UNPACK_MANIFEST.json'),all_ELFs_read_as_data=True,no_ldd_dlopen_or_library_execution=True,models=0))
  key=Path('/usr/share/keyrings/ubuntu-archive-keyring.gpg');assert sha(key)=='80a36b0a6de2f69f49d2df75ef473ccde121e9e190b9ea01d20a4f63778d5c31'
  home=O/'gpg-home';home.mkdir(mode=0o700);selected=None;database=[]
  for ordinal,base in enumerate(['https://mirrors.tuna.tsinghua.edu.cn/ubuntu','https://archive.ubuntu.com/ubuntu'],1):
   folder=O/f'endpoint{ordinal:02d}';folder.mkdir();attempt=dict(base=base,passed=False)
   try:
    release=fetch(base+'/dists/focal/Release',folder/'Release');fetch(base+'/dists/focal/Release.gpg',folder/'Release.gpg')
    command=['/usr/bin/gpgv','--homedir',str(home),'--keyring',str(key),'--status-fd','1',str(folder/'Release.gpg'),str(folder/'Release')]
    child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True);identity=dict(pid=child.pid,pgid=os.getpgid(child.pid),start_ticks=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split()[19],boot_id=boot,nonmodel_signature_tool=True)
    put(O/f'OWNED_CHILD_SIGNATURE{ordinal}.json',identity)
    try:stdout,stderr=child.communicate(timeout=15)
    except BaseException:
     assert Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split()[19]==identity['start_ticks'];os.killpg(identity['pgid'],signal.SIGKILL);child.wait(timeout=3);raise
    assert len(stdout)+len(stderr)<=128*1024;proof=dict(argv=command,returncode=child.returncode,stdout=stdout.decode(),stderr=stderr.decode(),identity=identity,child_exited=True,keyring_sha256=sha(key),gpgv_sha256=sha(Path('/usr/bin/gpgv')));put(folder/'SIGNATURE.json',proof)
    signers=[line.split()[2]for line in proof['stdout'].splitlines()if line.startswith('[GNUPG:] VALIDSIG ')];assert child.returncode==0 and signers and all(v in ['F6ECB3762474EDA9D21B7022871920D1991BC93C','790BC7277767219C42C86F933B4FE6ACC0B21F32']for v in signers),'UBUNTU_SIGNATURE_REFUSED'
    doc=deb.fields(release.decode());assert doc['Codename']=='focal'and doc['Origin']=='Ubuntu';hashes={}
    for line in doc['SHA256'].splitlines():
     values=line.split()
     if values:hashes[values[2]]=(values[0],int(values[1]))
    records=[];indices=[]
    for component in ['main','universe']:
     name=f'{component}/binary-amd64/Packages.xz';digest,size=hashes[name];path=folder/(component+'-Packages.xz');fetch(base+'/dists/focal/'+name,path,size,digest)
     expanded=0;count=0;pending=b'';rawhash=hashlib.sha256()
     with lzma.open(path,'rb')as stream:
      while True:
       guard();block=stream.read(128*1024)
       if not block:break
       expanded+=len(block);assert expanded<=96*1024**2;rawhash.update(block);pending+=block
       while b'\n\n'in pending:
        raw,pending=pending.split(b'\n\n',1)
        if raw:
         row=deb.fields(raw.decode());count+=1
         if row.get('Architecture')in ['amd64','all']:records.append({**{k:row[k]for k in deb.FIELDS if k in row},'source':'FOCAL_'+component.upper(),'base_url':base})
       assert len(pending)<=2*1024**2
     if pending.strip():
      row=deb.fields(pending.decode());count+=1
      if row.get('Architecture')in ['amd64','all']:records.append({**{k:row[k]for k in deb.FIELDS if k in row},'source':'FOCAL_'+component.upper(),'base_url':base})
     rawdigest,rawsize=hashes[f'{component}/binary-amd64/Packages'];assert expanded==rawsize and rawhash.hexdigest()==rawdigest
     indices.append(dict(component=component,path=str(path.relative_to(R)),compressed_sha256=sha(path),compressed_bytes=size,expanded_sha256=rawdigest,expanded_bytes=expanded,records=count,expanded_index_not_saved=True))
    database=records;selected=dict(base=base,release_path=str((folder/'Release').relative_to(R)),release_sha256=sha(folder/'Release'),signature_path=str((folder/'SIGNATURE.json').relative_to(R)),signature_sha256=sha(folder/'SIGNATURE.json'),signers=signers,release_date=doc['Date'],indices=indices,signature_authenticated=True)
    attempt.update(passed=True,selected=selected);attempts.append(attempt);put(O/'ENDPOINT_ATTEMPTS.json',attempts);break
   except Exception as error:attempt.update(error=repr(error));attempts.append(attempt);put(O/'ENDPOINT_ATTEMPTS.json',attempts)
  assert selected,'SIGNED_FOCAL_METADATA_UNAVAILABLE'
  ros=read(S/'DEPENDENCY_PLAN.json');index_path=R/ros['metadata']['index_path'];assert sha(index_path)==ros['metadata']['index_sha256']
  for block in index_path.read_text().strip().split('\n\n'):
   row=deb.fields(block)
   if row.get('Architecture')in ['amd64','all']:database.append({**{k:row[k]for k in deb.FIELDS if k in row},'source':'ROS_SIGNED','base_url':ros['metadata']['base']})
  already={x['Package']:x['Version']for x in ros['packages']};full=deb.closure(sorted(ros['external_dependency_groups']),database,already)
  build_roots=['libeigen3-dev','libsuitesparse-dev','libboost-system-dev','libboost-thread-dev','libboost-graph-dev','libboost-filesystem-dev','libboost-regex-dev','libboost-chrono-dev','libconsole-bridge-dev','libtinyxml2-dev','liborocos-kdl-dev','liblog4cxx-dev','libapr1-dev','libaprutil1-dev','python3-catkin-pkg-modules','python3-rospkg-modules','python3-empy','python3-docutils','python3-yaml']
  build=deb.closure(build_roots,database,already)
  common=dict(signed_metadata=selected,ROS_plan_sha256=sha(S/'DEPENDENCY_PLAN.json'),ELF_inventory_sha256=sha(O/'ELF_DEPENDENCIES.json'),original_external_constraint_groups=86,no_new_package_payload_downloads=True,no_system_install=True,ABI_or_build_authority=False,models=0)
  put(O/'FULL_DECLARED_DEPENDENCY_PLAN.json',dict(full,**common,scope='FULL_PACKAGING_CONSTRAINTS_NOT_MINIMAL_BUILD'))
  put(O/'BUILD_CANDIDATE_PLAN.json',dict(build,**common,roots=build_roots,scope='INITIAL_AUTHOR_CMAKE_AND_BUILD_TOOL_ROOTS_NOT_COMPLETE_LINK_RUNTIME_CLOSURE',all_actual_ELF_external_SONAMEs=needed,missing_SONAME_providers_not_yet_resolved=True,existing_CMake_and_Python_build_tools_available_but_not_treated_as_Focal_ABI_proof=True))
  result.update(passed=not full['unresolved'],scope='SIGNED_FOCAL_METADATA_AND_STATIC_ELF_ONLY',ELF_files=len(inventory),external_SONAMEs=len(needed),signature_authenticated=True,full_declared_packages=len(full['packages']),full_declared_download_bytes=full['download_bytes'],full_declared_installed_bytes=full['declared_installed_bytes'],full_unresolved=full['unresolved'],build_candidate_packages=len(build['packages']),build_candidate_download_bytes=build['download_bytes'],build_candidate_installed_bytes=build['declared_installed_bytes'],build_candidate_unresolved=build['unresolved'],ABI_or_build_qualified=False)
 except BaseException as error:result.update(first_error=dict(error=repr(error),traceback=traceback.format_exc()),scope='METADATA_INTERFACE_OR_RESOURCE_REFUSAL_NOT_METHOD_RESULT')
 finally:
  signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,wall_s=time.monotonic()-start,review_original=sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66');put(O/'RESULT.json',result)
 print(json.dumps(result),flush=True);return 0
if __name__=='__main__':raise SystemExit(main())
