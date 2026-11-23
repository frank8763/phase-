"""Recover exact ROS payload bytes without installing or executing a package."""
import fcntl,hashlib,io,json,os,posixpath,re,signal,subprocess,tarfile,time,traceback,urllib.request
from pathlib import Path,PurePosixPath
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
P=R/'runs/v1704_signed_noetic_metadata';D=R/'runs/v1707_noetic_payload_recovery';CAP=224*1024**2;CLOSE=8*1024**2
read=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1024**2),b''):h.update(b)
 return h.hexdigest()
def allocation():return O.lstat().st_blocks*512+sum(p.lstat().st_blocks*512 for p in O.rglob('*'))
def capacity(size,closing=False):assert allocation()+((size+4095)//4096)*4096+8192+(0 if closing else CLOSE)<=CAP,'PAYLOAD_TASK_224MIB_CAP'
def put(p,v,closing=False):
 data=json.dumps(v,indent=2,allow_nan=False).encode()+b'\n';capacity(len(data),closing);t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(data);t.replace(p)
def ar_data(blob):
 assert blob.startswith(b'!<arch>\n');at=8;members={}
 while at<len(blob):
  header=blob[at:at+60];assert len(header)==60 and header[-2:]==b'`\n';name=header[:16].decode().strip().rstrip('/');size=int(header[48:58]);at+=60
  assert name not in members and 0<=size<=32*1024**2 and at+size<=len(blob);members[name]=blob[at:at+size];at+=size+size%2
 assert at==len(blob)and members.pop('debian-binary')==b'2.0\n'
 payloads=[n for n in members if n in ['data.tar.xz','data.tar.gz','data.tar']];controls=[n for n in members if n in ['control.tar.xz','control.tar.gz','control.tar']]
 assert len(payloads)==1 and len(controls)==1 and len(members)==2,'EXACT_DEBIAN_AR_STRUCTURE'
 return payloads[0],members[payloads[0]]
def member_path(name):
 while name.startswith('./'):name=name[2:]
 name=name.rstrip('/')
 if name in ['','.']:return None
 p=PurePosixPath(name);assert not p.is_absolute()and '..'not in p.parts and '\\'not in name
 assert name==str(p).rstrip('/'),('NONCANONICAL_TAR_PATH',name)
 assert name in ['opt','opt/ros','opt/ros/noetic','usr','usr/share','usr/share/doc']or name.startswith(('opt/ros/noetic/','usr/share/doc/')),'PAYLOAD_NAMESPACE'
 return str(p)
def symlink_target(name,target):
 assert target and '\\'not in target and '\0'not in target
 logical=posixpath.normpath(target if target.startswith('/')else '/'+posixpath.dirname(name)+'/'+target)
 assert logical in ['/opt/ros/noetic','/usr/share/doc','/usr/share/common-licenses']or logical.startswith(('/opt/ros/noetic/','/usr/share/doc/','/usr/share/common-licenses/')),'SYMLINK_LOGICAL_NAMESPACE'
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 for n in ['ONCE_CLAIM.json','RESULT.json','OWNED_CHILD.json']:assert not(O/n).exists()
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 current=read(R/'CURRENT_EXPERIMENT.json');assert current['active_round']is None and not current['models_now_authorized']
 prior=read(P/'RESULT.json');plan=read(P/'DEPENDENCY_PLAN.json');barrier=read(P/'POST_ROUND_STORAGE_BARRIER.json')
 assert prior['passed']and prior['signature_authenticated']and plan['release_signature_authenticated']and not plan['missing_ROS_packages']
 assert barrier['passed']and all(sha(R/n)==h for n,h in barrier['proof_paths_SHA256'].items())
 assert barrier['closed_runtime_review_sha256']==sha(P/'RUNTIME_CLOSED_REVIEW.json')and read(P/'RUNTIME_CLOSED_REVIEW.json')['release_SHA_bound_index_verified']
 assert sha(P/'DEPENDENCY_PLAN.json')==read(P/'RUNTIME_CLOSED_REVIEW.json')['source_paths_SHA256'][str((P/'DEPENDENCY_PLAN.json').relative_to(R))]
 assert sha(R/plan['metadata']['index_path'])==plan['metadata']['index_sha256']and sha(P/'KEY_BINDING.json')==plan['metadata']['key_binding_sha256']
 assert read(P/'COMMAND_signature1.json')['returncode']==0 and sha(P/'COMMAND_signature1.json')==plan['metadata']['signature_record_sha256']
 for p in [P/'ONCE_CLAIM.json',*P.glob('OWNED_CHILD_*.json')]:
  identity=read(p);assert not Path('/proc',str(identity.get('pid',identity.get('owner_pid')))).exists()
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 source=read(D/'SYNC_RESULT.json');assert source['remote_verified']and source['push_executed']
 for path in [C/'owner.py',C/'PROTOCOL.md']:assert subprocess.check_output(['git','show',source['head']+':'+str(path.relative_to(R))],cwd=R)==path.read_bytes()
 used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used+(224+32+32+512)*1024**2<15*1024**3
 assert len(plan['packages'])==74 and sum(int(x['Size'])for x in plan['packages'])==6915624
 now=time.time();start=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 def guard(closing=False):
  limit=5400 if closing else 4200;assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.time()<now+limit and time.monotonic()<start+limit,'PAYLOAD_BOOT_DUAL_CLOCK'
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('PAYLOAD5400_HARD_STOP')));signal.setitimer(signal.ITIMER_REAL,5400)
 put(O/'ONCE_CLAIM.json',dict(owner_pid=os.getpid(),unix=now,monotonic=start,boot_id=boot,owner_sha256=sha(C/'owner.py'),protocol_sha256=sha(C/'PROTOCOL.md'),source_commit=source['head'],plan_sha256=sha(P/'DEPENDENCY_PLAN.json'),prior_barrier_sha256=sha(P/'POST_ROUND_STORAGE_BARRIER.json'),allruns_bytes=used,full_peak_bytes=used+(224+32+32+512)*1024**2,models_authorized=False))
 put(O/'ROUND_WINDOW.json',dict(started_unix=now,started_monotonic=start,normal_end_unix=now+4200,normal_end_monotonic=start+4200,root_end_unix=now+5400,root_end_monotonic=start+5400,boot_id=boot))
 result=dict(closed=False,passed=False,package_downloads=0,package_payload_SHA_verified=0,package_executions=0,maintainer_scripts_executed=0,compiler_calls=0,optimizer_calls=0,optimizer_constructors=0,models=0,physical_native=0,replay_native=0,method_executed=False,method_outcome=None,first_error=None)
 records=[];entries={};deferred=[];content=0;prefix=O/'sysroot';downloads=O/'packages';prefix.mkdir();downloads.mkdir();requests=[]
 def target(name):
  p=prefix/name
  for ancestor in p.parents:
   if ancestor==prefix:break
   assert not ancestor.is_symlink(),'SYMLINK_ANCESTOR_WRITE_REFUSED'
  return p
 def remember(name,row,package):
  if name in entries:
   existing=entries[name];assert all(existing[k]==row[k]for k in ['type','mode'])and {k:v for k,v in existing.items()if k not in ['owners','uid','gid']}=={k:v for k,v in row.items()if k not in ['owners','uid','gid']},('PAYLOAD_PATH_COLLISION',name)
   if package not in existing['owners']:existing['owners'].append(package)
   return False
  row['owners']=[package];entries[name]=row;return True
 try:
  base=plan['metadata']['base'];assert base=='https://mirrors.tuna.tsinghua.edu.cn/ros/ubuntu'
  for ordinal,package in enumerate(plan['packages'],1):
   guard();name=package['Package'];filename=package['Filename'];size=int(package['Size']);assert 0<size<=32*1024**2 and re.fullmatch('[A-Za-z0-9_./+~:-]+',filename)and '..'not in PurePosixPath(filename).parts
   capacity(size+2*32*1024**2);path=downloads/Path(filename).name;assert not path.exists();partial=path.with_suffix(path.suffix+'.partial');assert not partial.exists()
   url=base+'/'+filename;request_record=dict(package=name,url=url,passed=False)
   try:
    digest=hashlib.sha256();count=0
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Phase-exact-signed-ROS-payload','Accept-Encoding':'identity'}),timeout=30)as response,partial.open('xb')as stream:
     assert response.geturl().startswith(base+'/')
     while True:
      guard();block=response.read(128*1024)
      if not block:break
      assert count+len(block)<=size;capacity(len(block));stream.write(block);digest.update(block);count+=len(block)
    assert count==size and digest.hexdigest()==package['SHA256'],'SIGNED_INDEX_PAYLOAD_SHA_SIZE';partial.replace(path)
    result['package_downloads']+=1;result['package_payload_SHA_verified']+=1;request_record.update(passed=True,bytes=count,sha256=digest.hexdigest())
   except BaseException as error:request_record['error']=repr(error);raise
   finally:requests.append(request_record);put(O/'REQUESTS.json',requests)
   archive_name,data=ar_data(path.read_bytes());package_files=0;expanded=0
   with tarfile.open(fileobj=io.BytesIO(data),mode='r:*')as archive:
    members=archive.getmembers();assert len(members)<=20000 and sum(m.size for m in members if m.isfile())<=64*1024**2
    for member in members:
     guard();relative=member_path(member.name)
     if relative is None:continue
     assert not(member.mode&0o7000),'SPECIAL_PERMISSION_REFUSED';p=target(relative);mode=member.mode&0o777
     row=dict(path=str(p.relative_to(R)),mode=mode,uid=member.uid,gid=member.gid)
     if member.isdir():
      row['type']='directory'
      if remember(relative,row,name):capacity(4096);p.mkdir(parents=True,exist_ok=True);p.chmod(mode)
     elif member.isfile():
      row.update(type='regular',bytes=member.size);capacity(member.size)
      h=hashlib.sha256();stream=archive.extractfile(member);payload=stream.read(member.size+1);assert len(payload)==member.size;row['sha256']=hashlib.sha256(payload).hexdigest()
      if remember(relative,row,name):
       assert not p.exists()and not p.is_symlink();p.parent.mkdir(parents=True,exist_ok=True)
       with p.open('xb')as f:f.write(payload)
       p.chmod(mode)
      package_files+=1;expanded+=member.size;content+=member.size;assert content<=160*1024**2,'TOTAL_PAYLOAD_CONTENT_CAP'
     elif member.issym():
      symlink_target(relative,member.linkname);row.update(type='symlink',target=member.linkname)
      if remember(relative,row,name):capacity(4096);assert not p.exists()and not p.is_symlink();p.parent.mkdir(parents=True,exist_ok=True);p.symlink_to(member.linkname)
      package_files+=1
     elif member.islnk():
      link=member_path(member.linkname);assert link is not None;row.update(type='hardlink',target=str((prefix/link).relative_to(R)));deferred.append((relative,row,name));package_files+=1
     else:raise AssertionError(('SPECIAL_TAR_MEMBER',member.name,member.type))
   records.append(dict(package=name,version=package['Version'],deb_path=str(path.relative_to(R)),deb_sha256=package['SHA256'],deb_bytes=size,data_member=archive_name,payload_files=package_files,regular_expanded_bytes=expanded))
   put(O/'INTAKE_PROGRESS.json',dict(completed_packages=ordinal,total_packages=74,last_package=name,task_allocated_bytes=allocation(),expanded_content_bytes=content,models=0,package_execution=False))
  for relative,row,name in deferred:
   p=target(relative);q=R/row['target'];assert q.is_file()and not q.is_symlink();target(str(q.relative_to(prefix)));row.update(bytes=q.stat().st_size,sha256=sha(q))
   if remember(relative,row,name):capacity(4096);assert not p.exists()and not p.is_symlink();p.parent.mkdir(parents=True,exist_ok=True);os.link(q,p)
  guard(closing=True)
  for relative,row in entries.items():
   p=target(relative);assert not p.is_symlink()or row['type']=='symlink'
   if row['type']in ['regular','hardlink']:assert p.stat().st_size==row['bytes']and sha(p)==row['sha256']and(p.lstat().st_mode&0o777)==row['mode']
   elif row['type']=='symlink':assert p.is_symlink()and os.readlink(p)==row['target']
   else:assert p.is_dir()and(p.lstat().st_mode&0o777)==row['mode']
  put(O/'PACKAGE_MANIFEST.json',dict(packages=records,original_deb_bytes=sum(x['deb_bytes']for x in records),original_debs_retained=True,signature_bound_plan_sha256=sha(P/'DEPENDENCY_PLAN.json'),models=0),closing=True)
  put(O/'UNPACK_MANIFEST.json',dict(prefix=str(prefix.relative_to(R)),entries=entries,total_entries=len(entries),expanded_regular_content_bytes=content,host_uid_gid_replication_not_claimed=True,all_member_SHA_size_mode_link_verified=True,package_execution=False,models=0),closing=True)
  used_after=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used_after+(32+32+512)*1024**2<15*1024**3 and allocation()<CAP
  result.update(passed=True,recovered_packages=len(records),unpack_entries=len(entries),expanded_regular_content_bytes=content,all_member_SHA_size_mode_link_verified=True,original_debs_retained=True,nonROS_dependencies_still_unresolved=86,ABI_or_build_qualified=False,task_allocated_bytes_before_terminal=allocation(),allruns_after_bytes=used_after,disposition='EXACT_ROS_PAYLOAD_DATA_RECOVERY_ONLY_NOT_TEB_BUILD_OR_METHOD_PASS')
 except BaseException as error:result.update(first_error=dict(error=repr(error),traceback=traceback.format_exc()),disposition='PAYLOAD_RESOURCE_OR_INTERFACE_ERROR_NOT_METHOD_RESULT')
 finally:
  signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,wall_s=time.monotonic()-start,review_original=sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66',partial_package_records=records,task_allocated_bytes=allocation());put(O/'RESULT.json',result,closing=True)
 print(json.dumps({k:v for k,v in result.items()if k!='partial_package_records'}),flush=True);return 0
if __name__=='__main__':raise SystemExit(main())
