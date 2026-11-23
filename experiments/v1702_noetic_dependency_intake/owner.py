"""Bounded data-only Noetic package inventory; never install or run a package."""
import fcntl,gzip,hashlib,io,json,os,re,signal,subprocess,time,traceback,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
P=R/'runs/v1699_teb_local_cmake_configure';D=R/'runs/v1703_noetic_dependency_recovery'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def allocation():return sum(p.lstat().st_blocks*512 for p in O.rglob('*'))+O.lstat().st_blocks*512
def put(p,v):
 data=json.dumps(v,indent=2,allow_nan=False).encode()+b'\n';assert len(data)<=16*1024**2
 assert allocation()+((len(data)+4095)//4096)*4096+8192<=32*1024**2,'METADATA_TOTAL_32MIB_CAP'
 temp=p.with_suffix(p.suffix+'.tmp');temp.write_bytes(data);temp.replace(p)
def fields(text):
 out={};key=None
 for line in text.splitlines():
  if line.startswith((' ','\t')):
   assert key is not None;out[key]+='\n'+line[1:]
  else:
   key,sep,value=line.partition(':');assert sep;assert key not in out;out[key]=value.strip()
 return out
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 for n in ['ONCE_CLAIM.json','RESULT.json','OWNED_CHILD.json']:assert not(O/n).exists()
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 parent=read(R/'CURRENT_EXPERIMENT.json');assert parent['active_round']is None and not parent['models_now_authorized']
 barrier=read(P/'POST_ROUND_STORAGE_BARRIER.json');assert barrier['passed']and all(sha(R/n)==h for n,h in barrier['proof_paths_SHA256'].items())
 for n in ['ONCE_CLAIM.json','OWNED_CHILD.json']:
  old=read(P/n);assert not Path('/proc',str(old.get('pid',old.get('owner_pid')))).exists()
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert all(sha(R/n)==h for n,h in read(P/'AUTHOR_SOURCE_FREEZE.json')['files'].items())
 sync=read(D/'SYNC_RESULT.json');assert sync['remote_verified']and sync['push_executed']
 for path in [C/'owner.py',C/'PROTOCOL.md']:
  raw=subprocess.check_output(['git','show',sync['head']+':'+str(path.relative_to(R))],cwd=R);assert raw==path.read_bytes()
 used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used+(32+32+32+512)*1024**2<15*1024**3
 now=time.time();start=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 def guard():assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.time()<now+600 and time.monotonic()<start+600,'METADATA_DUAL_CLOCK'
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('METADATA600_HARD_STOP')));signal.setitimer(signal.ITIMER_REAL,600)
 put(O/'ONCE_CLAIM.json',dict(unix=now,monotonic=start,boot_id=boot,owner_pid=os.getpid(),owner_sha256=sha(C/'owner.py'),protocol_sha256=sha(C/'PROTOCOL.md'),source_commit=sync['head'],allruns_bytes=used,models_authorized=False))
 put(O/'ROUND_WINDOW.json',dict(started_unix=now,started_monotonic=start,metadata_end_unix=now+600,metadata_end_monotonic=start+600,root_end_unix=now+5400,root_end_monotonic=start+5400,boot_id=boot))
 result=dict(closed=False,passed=False,models=0,compiler_calls=0,optimizer_calls=0,optimizer_constructors=0,physical_native=0,replay_native=0,method_executed=False,method_outcome=None,package_downloads=0,package_executions=0,first_error=None)
 attempts=[];requests=[]
 def fetch(url,path):
  guard();assert url.startswith(('https://snapshots.ros.org/','https://packages.ros.org/'))
  record=dict(url=url,path=str(path.relative_to(R)),passed=False)
  try:
   request=urllib.request.Request(url,headers={'User-Agent':'Phase-bounded-TEB-dependency-metadata','Accept-Encoding':'identity'})
   with urllib.request.urlopen(request,timeout=30)as response:
    assert response.geturl().startswith(('https://snapshots.ros.org/','https://packages.ros.org/'))
    body=bytearray()
    while True:
     guard();block=response.read(128*1024)
     if not block:break
     assert len(body)+len(block)<=16*1024**2,'METADATA_OBJECT_16MIB_CAP';body.extend(block)
   assert allocation()+((len(body)+4095)//4096)*4096+1024**2<=32*1024**2,'METADATA_TOTAL_WITH_CLOSE_RESERVE'
   with path.open('xb')as f:f.write(body)
   record.update(passed=True,bytes=len(body),sha256=sha(path));return bytes(body)
  except BaseException as error:
   record['error']=repr(error);raise
  finally:requests.append(record);put(O/'REQUESTS.json',requests)
 try:
  cmake=P/'source/CMakeLists.txt';package=P/'source/package.xml';ET.parse(package)
  components=re.search(r'find_package\(catkin REQUIRED COMPONENTS(.*?)\)',cmake.read_text(),re.S).group(1).split();assert len(components)==20
  roots=sorted({'ros-noetic-'+x.replace('_','-')for x in components+['catkin','message_runtime','libg2o']})
  put(O/'ROOTS.json',dict(packages=roots,author_source_paths_SHA256={str(p.relative_to(R)):sha(p)for p in [cmake,package]},components=components))
  selected=None
  for ordinal,base in enumerate(['https://snapshots.ros.org/noetic/final/ubuntu','https://packages.ros.org/ros/ubuntu'],1):
   guard();folder=O/f'endpoint{ordinal:02d}';folder.mkdir();attempt=dict(base=base,passed=False)
   try:
    release=fetch(base+'/dists/focal/Release',folder/'Release');doc=fields(release.decode());hashes={}
    for line in doc['SHA256'].splitlines():
     parts=line.split()
     if parts:assert len(parts)==3;hashes[parts[2]]=(parts[0],int(parts[1]))
    name=next(x for x in ['main/binary-amd64/Packages.gz','main/binary-amd64/Packages']if x in hashes)
    digest,size=hashes[name];assert 0<size<=16*1024**2 and re.fullmatch('[0-9a-f]{64}',digest)
    compressed=fetch(base+'/dists/focal/'+name,folder/Path(name).name);assert len(compressed)==size and hashlib.sha256(compressed).hexdigest()==digest,'RELEASE_INDEX_SHA_SIZE'
    if name.endswith('.gz'):
     with gzip.GzipFile(fileobj=io.BytesIO(compressed))as f:raw=f.read(16*1024**2+1)
    else:raw=compressed
    assert len(raw)<=16*1024**2
    assert allocation()+((len(raw)+4095)//4096)*4096+1024**2<=32*1024**2,'DECOMPRESSED_INDEX_TOTAL_CAP'
    (folder/'Packages.exact').write_bytes(raw)
    selected=dict(base=base,official_frozen_snapshot=ordinal==1,release_path=str((folder/'Release').relative_to(R)),release_sha256=sha(folder/'Release'),index_path=str((folder/'Packages.exact').relative_to(R)),index_sha256=sha(folder/'Packages.exact'),release_bound_index_sha256=digest,release_bound_index_bytes=size,release_signature_authenticated=False,payload_authority=False)
    attempt.update(passed=True,selected=selected);attempts.append(attempt);put(O/'ENDPOINT_ATTEMPTS.json',attempts);break
   except Exception as error:attempt.update(error=repr(error));attempts.append(attempt);put(O/'ENDPOINT_ATTEMPTS.json',attempts)
  assert selected is not None,'BOTH_OFFICIAL_METADATA_ENDPOINTS_UNAVAILABLE'
  records=[fields(x)for x in (R/selected['index_path']).read_text().strip().split('\n\n')];lookup={}
  for row in records:
   if row.get('Architecture')in ['amd64','all']:
    assert row['Package']not in lookup,'DUPLICATE_PACKAGE_VERSION_INDEX';lookup[row['Package']]=row
  queue=list(roots);chosen={};external={};missing=[];edges=[]
  while queue:
   guard();name=queue.pop(0)
   if name in chosen or name in missing:continue
   if name not in lookup:missing.append(name);continue
   row=lookup[name];filename=row['Filename'];assert not filename.startswith('/')and '..'not in Path(filename).parts and filename.endswith('.deb')
   assert re.fullmatch('[0-9a-f]{64}',row['SHA256']);size=int(row['Size']);assert 0<size<=32*1024**2,'PROSPECTIVE_PACKAGE_32MIB_CAP'
   chosen[name]={k:row[k]for k in ['Package','Version','Architecture','Filename','Size','SHA256']};chosen[name]['Installed-Size']=int(row.get('Installed-Size','0'));chosen[name]['Depends']=row.get('Depends','');chosen[name]['Pre-Depends']=row.get('Pre-Depends','')
   for key in ['Pre-Depends','Depends']:
    for group in filter(None,(x.strip()for x in row.get(key,'').split(','))):
     alternatives=[x.strip()for x in group.split('|')];parsed=[]
     for item in alternatives:
      match=re.fullmatch(r'([a-zA-Z0-9+.-]+)(?::[a-zA-Z0-9-]+)?(?:\s*\((>=|<=|=|>>|<<)\s*([^()]+)\))?',item);assert match,('DEPENDENCY_SYNTAX',item)
      dep,op,version=match.groups();parsed.append((dep,op,version))
     ros=[x for x in parsed if x[0].startswith('ros-noetic-')and x[0]in lookup]
     if ros:
      dep,op,version=ros[0]
      if op:assert subprocess.run(['dpkg','--compare-versions',lookup[dep]['Version'],op,version],capture_output=True,timeout=5).returncode==0,('ROS_DEP_VERSION',dep,op,version)
      queue.append(dep);edges.append(dict(parent=name,kind=key,original_group=group,selected=dep))
     elif any(x[0].startswith('ros-noetic-')for x in parsed):missing.extend(x[0]for x in parsed if x[0].startswith('ros-noetic-'))
     else:external.setdefault(group,[]).append(name)
  packages=sorted(chosen.values(),key=lambda x:x['Package']);download=sum(int(x['Size'])for x in packages);installed=sum(x['Installed-Size']*1024 for x in packages)
  plan=dict(metadata=selected,roots=roots,packages=packages,ROS_dependency_edges=edges,missing_ROS_packages=sorted(set(missing)),external_dependency_groups=external,ROS_package_count=len(packages),ROS_download_bytes=download,ROS_declared_installed_bytes=installed,declared_size_not_exact_allocated_or_complete_peak=True,nonROS_transitive_closure_unresolved=True,package_payload_SHA_verified=False,release_signature_authenticated=False,package_execution_authority=False,all_ROS_roots_and_dependencies_indexed=not missing,prospective_two_block_reserve_bytes=2*32*1024**2,models=0,method_executed=False)
  put(O/'DEPENDENCY_PLAN.json',plan)
  result.update(passed=not missing,disposition='ROS_METADATA_SELECTION_ONLY_NOT_RECOVERED_OR_ABI_QUALIFIED',ROS_package_count=len(packages),ROS_download_bytes=download,ROS_declared_installed_bytes=installed,external_groups=len(external),missing_ROS_packages=sorted(set(missing)),selected_metadata=selected,signature_authenticated=False,payload_authority=False)
 except BaseException as error:result.update(first_error=dict(error=repr(error),traceback=traceback.format_exc()),disposition='METADATA_OPERATION_REFUSAL_NOT_METHOD_RESULT')
 finally:
  signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,wall_s=time.monotonic()-start,review_original=sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66');put(O/'RESULT.json',result)
 print(json.dumps(result),flush=True);return 0
if __name__=='__main__':raise SystemExit(main())
