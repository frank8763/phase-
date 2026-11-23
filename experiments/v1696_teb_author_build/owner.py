"""Recover exact small TEB build sources and configure once, never run TEB."""
import base64,fcntl,hashlib,json,os,selectors,signal,subprocess,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
I=R/'runs/v1650_comparison_completion/author_intake';P=R/'runs/v1694_shared_observation_closure'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,value):
 data=json.dumps(value,indent=2,allow_nan=False).encode()+b'\n';assert len(data)<=4*1024**2
 t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(data);t.replace(p)
def gitblob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 assert not(O/'ONCE_CLAIM.json').exists()and not(O/'RESULT.json').exists()and not(O/'OWNED_CHILD.json').exists()
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 parent=read(R/'CURRENT_EXPERIMENT.json');assert parent['active_round']is None and not parent['models_now_authorized']
 barrier=read(P/'POST_ROUND_STORAGE_BARRIER.json');assert barrier['passed']and all(sha(R/n)==h for n,h in barrier['proof_paths_SHA256'].items())
 assert read(P/'SOURCE_QUALIFICATION.json')['passed']and read(P/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used+(8+8+16+32+512)*1024**2<15*1024**3
 now=time.time();start=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 window=dict(started_unix=now,started_monotonic=start,absolute_deadline_unix=now+5400,hard_stop_monotonic=start+5400,boot_id=boot,source_intake_seconds=600,cmake_configure_seconds=90)
 def guard(seconds=5400):
  assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.time()<now+min(seconds,5400)and time.monotonic()<start+min(seconds,5400),'TEB_BUILD_DUAL_CLOCK'
 put(O/'ONCE_CLAIM.json',dict(unix=now,owner_pid=os.getpid(),models_authorized=False,source_owner_sha256=sha(C/'owner.py'),protocol_sha256=sha(C/'PROTOCOL.md'),allruns_bytes=used));put(O/'ROUND_WINDOW.json',window)
 result=dict(closed=False,passed=False,source_intake_passed=False,build_configure_passed=False,method_executed=False,method_outcome=None,models=0,optimizer_constructors=0,optimizer_calls=0,optimizer_DLL_loads=0,physical_native=0,replay_native=0,first_error=None)
 child=None;identity=None;console=bytearray();source={}
 try:
  tree=read(I/'TEB_TREE.json');commit=read(I/'TEB_COMMIT.json')
  assert commit['sha']=='9e55af4724310c34bcfa8cbb3b2783478c1a246a'and tree['sha']==commit['commit']['tree']['sha']=='ef454b69b5433be6356a648021137e202fc1ee7d'and tree['truncated']is False
  selected=[row for row in tree['tree']if row['type']=='blob'and(row['path'].startswith(('include/','src/','cfg/','cmake_modules/','msg/'))or row['path']in ['CMakeLists.txt','package.xml','LICENSE','README.md','teb_local_planner_plugin.xml'])]
  assert len(selected)==55 and sum(row['size']for row in selected)==730484 and sum(row['size']for row in selected)<=8*1024**2
  put(O/'SELECTED_BUILD_MATERIALS.json',dict(commit=commit['sha'],tree=tree['sha'],members=selected,commit_metadata_sha256=sha(I/'TEB_COMMIT.json'),tree_metadata_sha256=sha(I/'TEB_TREE.json'),no_source_substitution=True))
  folder=O/'source';folder.mkdir();members=[];source_bytes=0;api_calls=0
  for row in sorted(selected,key=lambda x:x['path']):
   guard(600);name=row['path'];assert not Path(name).is_absolute()and '..'not in Path(name).parts and row['mode']in ['100644','100755']
   previous=I/'upstream/TEB'/name
   if previous.is_file():data=previous.read_bytes();origin='EXISTING_EXACT_PINNED_MEMBER'
   else:
    api='repos/rst-tu-dortmund/teb_local_planner/git/blobs/'+row['sha']
    reply=subprocess.run([str(R/'tools/phase_storage_20261107/vendor/gh'),'api',api],cwd=R,capture_output=True,timeout=20)
    assert reply.returncode==0 and len(reply.stdout)<=2*1024**2,'PINNED_BLOB_API_REFUSED'
    blob=json.loads(reply.stdout);assert blob['sha']==row['sha']and blob['encoding']=='base64'and blob['size']==row['size']
    data=base64.b64decode(blob['content']);api_calls+=1;origin='EXACT_GIT_BLOB_API'
   assert len(data)==row['size']and gitblob(data)==row['sha'],'AUTHOR_SOURCE_BLOB_OR_SIZE_CHANGED'
   path=folder/name;path.parent.mkdir(parents=True,exist_ok=True)
   with path.open('xb')as f:f.write(data)
   path.chmod(0o755 if row['mode']=='100755'else 0o644)
   assert path.stat().st_size==row['size']and gitblob(path.read_bytes())==row['sha']
   source[str(path.relative_to(R))]=sha(path);source_bytes+=len(data)
   members.append(dict(path=str(path.relative_to(R)),upstream_path=name,git_blob_sha1=row['sha'],sha256=sha(path),bytes=len(data),git_mode=row['mode'],origin=origin))
   put(O/'INTAKE_PROGRESS.json',dict(members=len(members),source_bytes=source_bytes,api_calls=api_calls,models=0))
  put(O/'AUTHOR_SOURCE_FREEZE.json',dict(files=source,members=members,commit=commit['sha'],tree=tree['sha'],source_bytes=source_bytes,models_authorized=False))
  result.update(source_intake_passed=True,author_members=len(members),author_source_bytes=source_bytes,api_calls=api_calls,commit=commit['sha'],tree=tree['sha'])
  guard();env=os.environ.copy()
  for key in ['CMAKE_PREFIX_PATH','PYTHONPATH','ROS_PACKAGE_PATH','AMENT_PREFIX_PATH','COLCON_PREFIX_PATH','LD_LIBRARY_PATH']:env.pop(key,None)
  env.update(PATH='/usr/bin:/bin',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',CMAKE_BUILD_PARALLEL_LEVEL='1',PYTHONDONTWRITEBYTECODE='1')
  command=['taskset','-c','4','nice','-n','19','ionice','-c','3','/usr/bin/cmake','-S',str(folder),'-B',str(O/'build'),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_C_COMPILER=/usr/bin/cc','-DCMAKE_CXX_COMPILER=/usr/bin/c++','-DCMAKE_FIND_USE_PACKAGE_REGISTRY=FALSE','-DCMAKE_FIND_USE_SYSTEM_PACKAGE_REGISTRY=FALSE']
  put(O/'CMAKE_COMMAND.json',dict(argv=command,cpu=4,maximum_seconds=90,uncontrolled_ROS_paths_removed=True,optimizer_execution=False,source_owner_sha256=sha(C/'owner.py')))
  began=time.monotonic();wall=time.time();child=subprocess.Popen(command,cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
  stat=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split();identity=dict(pid=child.pid,pgid=os.getpgid(child.pid),start_ticks=stat[19],boot_id=boot,kind='NON_MODEL_CMAKE_CONFIGURE_CPU4');put(O/'OWNED_CHILD.json',identity)
  selector=selectors.DefaultSelector();selector.register(child.stdout,selectors.EVENT_READ)
  while selector.get_map():
   guard();assert time.monotonic()<began+90 and time.time()<wall+90,'CMAKE90_DUAL_CLOCK'
   for key,_ in selector.select(.2):
    block=os.read(key.fileobj.fileno(),16384)
    if not block:selector.unregister(key.fileobj);continue
    assert len(console)+len(block)<=256*1024,'CMAKE_CONSOLE_CAP';console.extend(block)
  child.wait(timeout=5);(O/'cmake.console').write_bytes(console)
  assert all(sha(R/n)==h for n,h in source.items()),'AUTHOR_SOURCE_MUTATED_DURING_CONFIGURE'
  result.update(build_returncode=child.returncode,build_configure_passed=child.returncode==0,passed=child.returncode==0,source_SHA_all_unchanged=True,configure_wall_s=time.monotonic()-began,console_sha256=sha(O/'cmake.console'),disposition='CONFIGURE_ONLY_NO_OPTIMIZER_AUTHORITY'if child.returncode==0 else'DEPENDENCY_OR_BUILD_INTERFACE_REFUSAL_BEFORE_OPTIMIZER')
  if child.returncode!=0:result['first_error']=dict(stage='CMAKE_CONFIGURE',returncode=child.returncode,console_sha256=sha(O/'cmake.console'))
 except BaseException as error:result.update(first_error=dict(error=repr(error),traceback=traceback.format_exc()),disposition='INTAKE_OR_BUILD_OPERATION_ERROR_NOT_METHOD_RESULT')
 finally:
  if child is not None and child.poll()is None:
   stat=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split();assert stat[19]==identity['start_ticks']and os.getpgid(child.pid)==identity['pgid']
   os.killpg(identity['pgid'],signal.SIGTERM)
   try:child.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(identity['pgid'],signal.SIGKILL);child.wait(timeout=5)
  if console and not(O/'cmake.console').exists():(O/'cmake.console').write_bytes(console)
  result.update(closed=True,wall_s=time.monotonic()-start,compiler_exited=child is None or child.poll()is not None,review_original=sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66',full_modelwork_not_applicable_no_model_execution=True)
  put(O/'RESULT.json',result)
 print(json.dumps(result),flush=True);return 0
if __name__=='__main__':raise SystemExit(main())
