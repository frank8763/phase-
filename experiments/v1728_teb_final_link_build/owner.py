"""One original-author configure/build; no optimizer or model execution."""
import fcntl,hashlib,importlib.util,json,os,resource,selectors,signal,subprocess,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));n=load('v1728_exact_namespace',C/'namespace.py');sha=n.sha
 def put(p,v):
  raw=json.dumps(v,indent=2,allow_nan=False).encode()+b'\n';assert len(raw)<8*1024**2;p.write_bytes(raw)
 assert not any((O/x).exists()for x in ['ONCE_CLAIM.json','RESULT.json','OWNED_CHILD.json'])
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 cur=read(R/'CURRENT_EXPERIMENT.json');assert cur['active_round']is None and not cur['models_now_authorized']
 lock=(R/'runs/v648_static_unknown/execution.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 config=read(C/'CONFIG.json');sync=read(R/'runs/v1729_teb_final_build_recovery/SOURCE_SYNC_RESULT.json');assert sync['remote_verified']
 assert subprocess.check_output(['git','show',sync['head']+':'+str((C/'CONFIG.json').relative_to(R))],cwd=R)==(C/'CONFIG.json').read_bytes()
 for name,digest in config['source_files_SHA256'].items():
  assert sha(R/name)==digest and subprocess.check_output(['git','show',sync['head']+':'+name],cwd=R)==(R/name).read_bytes()
 assert sha(O/'INPUT_BINDING.json')==config['input_binding_sha256'];inputs=read(O/'INPUT_BINDING.json')
 for name,digest in inputs['files_SHA256'].items():assert sha(R/name)==digest
 for name,digest in inputs['host_tools_SHA256'].items():assert sha(Path(name))==digest
 for row in read(R/inputs['ros_manifest'])['entries'].values():
  p=R/row['path']
  if row['type']in ['regular','hardlink']:assert sha(p)==row['sha256']and p.stat().st_size==row['bytes']
  elif row['type']=='symlink':assert p.is_symlink()and os.readlink(p)==row['target']
  else:assert p.is_dir()and not p.is_symlink()
 for row in read(R/inputs['cmake_manifest'])['files']:assert sha(R/row['path'])==row['sha256']and(R/row['path']).stat().st_size==row['bytes']
 for b in inputs['barriers']:
  v=read(R/b);assert v['passed']and all(sha(R/k)==h for k,h in v['proof_paths_SHA256'].items())
 for manifest in inputs['native_manifests']:
  m=read(R/manifest);prefix=R/m['prefix']
  for row in m['entries'].values():
   p=prefix/row['path']
   if row['type']in ['regular','hardlink']:assert not p.is_symlink()and p.stat().st_size==row['bytes']and sha(p)==row['sha256']and p.stat().st_mode&0o777==row['mode']
   elif row['type']=='symlink':assert p.is_symlink()and os.readlink(p)==row['target']
   else:assert p.is_dir()and not p.is_symlink()
 used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used+(224+32+32+512)*1024**2<15*1024**3
 now=time.time();mono=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();child=None;identity=None;source={}
 def guard():assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.time()<now+4200 and time.monotonic()<mono+4200,'BUILD_DUAL_CLOCK'
 put(O/'ONCE_CLAIM.json',dict(owner_pid=os.getpid(),unix=now,monotonic=mono,boot_id=boot,source_commit=sync['head'],source_files_SHA256=config['source_files_SHA256'],input_binding_sha256=sha(O/'INPUT_BINDING.json'),models_authorized=False))
 put(O/'ROUND_WINDOW.json',dict(started_unix=now,started_monotonic=mono,normal_end_unix=now+4200,normal_end_monotonic=mono+4200,root_end_unix=now+5400,root_end_monotonic=mono+5400,boot_id=boot))
 result=dict(closed=False,passed=False,configure_calls=0,compile_calls=0,optimizer_constructors=0,optimizer_calls=0,optimizer_DLL_loads=0,models=0,physical_native=0,replay_native=0,method_outcome=None,first_error=None,secondary_errors=[])
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in()).throw(TimeoutError('BUILD5400_HARD_STOP')));signal.setitimer(signal.ITIMER_REAL,5400)
 def stop():
  if child is not None and child.poll()is None:
   s=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split();assert s[19]==identity['start_ticks']and os.getpgid(child.pid)==identity['pgid'];os.killpg(identity['pgid'],signal.SIGTERM)
   try:child.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(identity['pgid'],signal.SIGKILL);child.wait(timeout=5)
 def run(stage,argv,limit,view):
  nonlocal child,identity
  guard();command=['/usr/bin/taskset','-c','4','/usr/bin/nice','-n','19','/usr/bin/ionice','-c','3',*n.command(O,view,R/inputs['ros_root'],argv)]
  put(O/(stage+'_COMMAND.json'),dict(argv=command,cpu=4,maximum_s=limit,network_unshared=True,readonly_inputs=True,models=False))
  def limits():resource.setrlimit(resource.RLIMIT_FSIZE,(32*1024**2,32*1024**2))
  env={k:v for k,v in os.environ.items()if k not in ['CMAKE_PREFIX_PATH','LD_LIBRARY_PATH','PYTHONPATH','ROS_PACKAGE_PATH','AMENT_PREFIX_PATH','COLCON_PREFIX_PATH']};env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
  child=subprocess.Popen(command,env=env,cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True,preexec_fn=limits)
  s=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split();identity=dict(pid=child.pid,pgid=os.getpgid(child.pid),start_ticks=s[19],boot_id=boot,kind='ORIGINAL_TEB_NON_MODEL_BUILD_CPU4',stage=stage);put(O/'OWNED_CHILD.json',identity)
  sel=selectors.DefaultSelector();sel.register(child.stdout,selectors.EVENT_READ);console=bytearray();began=time.monotonic();wall=time.time();error=None;last_check=0;last_checkpoint=0
  try:
   while sel.get_map():
    guard();assert time.monotonic()<began+limit and time.time()<wall+limit,stage+'_BOUNDED_TIMEOUT'
    if time.monotonic()-last_check>=.5:
     allocated=int(subprocess.check_output(['du','-sx','-B1',str(O)]).split()[0]);assert allocated<144*1024**2,'BUILD_PREEMPTIVE144MIB_THRESHOLD';last_check=time.monotonic()
     if time.monotonic()-last_checkpoint>=30:
      put(O/'RUNNING_CHECKPOINT.json',dict(stage=stage,child_identity=identity,allocated_bytes=allocated,console_bytes=len(console),unix=time.time(),models=0,optimizer_calls=0,partial_build_only=True));last_checkpoint=time.monotonic()
    for key,_ in sel.select(.1):
     block=os.read(key.fileobj.fileno(),16384)
     if not block:sel.unregister(key.fileobj);continue
     assert len(console)+len(block)<=4*1024**2,'BUILD_CONSOLE4MIB_CAP';console.extend(block)
   child.wait(timeout=5)
  except BaseException as e:error=e;stop()
  finally:
   (O/(stage+'.console')).write_bytes(console);put(O/(stage+'_RETURN.json'),dict(returncode=child.poll(),wall_s=time.monotonic()-began,console_sha256=sha(O/(stage+'.console')),error=repr(error)if error else None,child_exited=child.poll()is not None))
  if error:raise error
  assert child.returncode==0,(stage+'_DEPENDENCY_OR_COMPILER_REFUSAL',child.returncode)
 try:
  for name in ['build','tmp']:(O/name).mkdir()
  author=read(R/inputs['author_manifest']);folder=O/'source';folder.mkdir()
  for row in author['members']:
   original=R/row['path'];assert sha(original)==row['sha256'];p=folder/row['upstream_path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(original.read_bytes());p.chmod(0o755 if row['git_mode']=='100755'else 0o644);source[str(p.relative_to(R))]=sha(p)
  put(O/'AUTHOR_SOURCE_FREEZE.json',dict(commit=author['commit'],files=source,unchanged_original_author=True))
  view,records=n.prepare_view(O,[R/p for p in inputs['native_roots']]);put(O/'NAMESPACE_MAPPING.json',dict(records=records,package_literals_preserved=True,host_fallback_readonly=True,source_rewrites=False,missing_library_aliases_fabricated=False))
  binary=str(R/inputs['cmake_binary']);result['configure_calls']=1
  argv=[binary,'-S',str(folder),'-B',str(O/'build'),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_C_COMPILER=/usr/bin/cc','-DCMAKE_CXX_COMPILER=/usr/bin/c++','-DPYTHON_EXECUTABLE=/usr/bin/python3.8','-DCATKIN_ENABLE_TESTING=OFF','-DCMAKE_FIND_USE_PACKAGE_REGISTRY=FALSE','-DCMAKE_FIND_USE_SYSTEM_PACKAGE_REGISTRY=FALSE']
  run('configure',argv,180,view);result['configure_passed']=True;result['compile_calls']=1
  run('compile',[binary,'--build',str(O/'build'),'--target','teb_local_planner','--parallel','1'],1800,view)
  libraries=list((O/'build').rglob('libteb_local_planner.so'));assert len(libraries)==1;result.update(passed=True,original_library_compiled=True,library_path=str(libraries[0].relative_to(R)),library_sha256=sha(libraries[0]),optimizer_executed=False)
 except BaseException as e:result['first_error']=dict(error=repr(e),traceback=traceback.format_exc())
 finally:
  try:stop()
  except BaseException as e:result['secondary_errors'].append(dict(stage='owned_child_cleanup',error=repr(e)))
  signal.setitimer(signal.ITIMER_REAL,0);result.update(closed=True,wall_s=time.monotonic()-mono,source_SHA_unchanged=all(sha(R/k)==h for k,h in source.items()),compiler_exited=child is None or child.poll()is not None,review_original=sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66',task_allocated_bytes=int(subprocess.check_output(['du','-sx','-B1',str(O)]).split()[0]))
  assert result['task_allocated_bytes']<224*1024**2;put(O/'RESULT.json',result)
 print(json.dumps(result));return 0
if __name__=='__main__':raise SystemExit(main())
