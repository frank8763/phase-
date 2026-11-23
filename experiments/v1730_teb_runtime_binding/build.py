"""Compile only the thin C interface on CPU4; never run its planner methods."""
import fcntl,os,resource,selectors,signal,subprocess,time,traceback
from context import C,O,R,read,put,sha,load
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 lock=(O/'OWNER.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert not(O/'BUILD_ONCE_CLAIM.json').exists()and not(O/'BUILD_RESULT.json').exists()
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 binding=read(O/'INPUT_BINDING.json');assert all(sha(R/k)==h for k,h in binding['files_SHA256'].items())and all(sha(k)==h for k,h in binding['external_SHA256'].items())
 sync=read(R/'runs/v1731_teb_runtime_recovery/SOURCE_SYNC_RESULT.json');assert sync['remote_verified']
 for p in C.iterdir():
  if p.is_file():assert subprocess.check_output(['git','show',sync['head']+':'+str(p.relative_to(R))],cwd=R)==p.read_bytes()
 now=time.time();mono=time.monotonic();boot=__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip();put(O/'ROUND_WINDOW.json',dict(started_unix=now,started_monotonic=mono,normal_end_unix=now+4200,normal_end_monotonic=mono+4200,root_end_unix=now+5400,root_end_monotonic=mono+5400,boot_id=boot));put(O/'BUILD_ONCE_CLAIM.json',dict(owner_pid=os.getpid(),source_commit=sync['head'],input_binding_sha256=sha(O/'INPUT_BINDING.json'),models_authorized=False))
 n=load('v1730_compile_namespace',C/'native_namespace.py');prior=R/'runs/v1728_teb_final_link_build';binary=O/'build/libphase_teb_bridge.so'
 argv=['/usr/bin/c++','-O2','-DNDEBUG','-fPIC','-shared','-DROSCONSOLE_BACKEND_LOG4CXX','-DROS_BUILD_SHARED_LIBS=1','-DROS_PACKAGE_NAME="teb_local_planner"','-I'+str(prior/'build/devel/include'),'-I'+str(prior/'source/include'),'-I/opt/ros/noetic/include','-I/opt/ros/noetic/include/g2o','-I/usr/include/eigen3','-I/usr/include/suitesparse',str(C/'bridge.cpp'),'-L'+str(prior/'build/devel/lib'),'-lteb_local_planner','-Wl,-rpath,'+str(prior/'build/devel/lib'),'-o',str(binary)]
 command=['taskset','-c','4','nice','-n','19',*n.command(argv)];put(O/'BUILD_COMMAND.json',dict(argv=command,cpu=4,maximum_s=180,optimizer_execution=False));child=None;data=bytearray();result=dict(closed=False,passed=False,models=0,optimizer_calls=0,first_error=None)
 try:
  def limits():resource.setrlimit(resource.RLIMIT_FSIZE,(32*1024**2,32*1024**2))
  child=subprocess.Popen(command,cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True,preexec_fn=limits);s=__import__('pathlib').Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split();identity=dict(pid=child.pid,pgid=os.getpgid(child.pid),start_ticks=s[19],boot_id=boot);put(O/'BUILD_OWNED_CHILD.json',identity);sel=selectors.DefaultSelector();sel.register(child.stdout,selectors.EVENT_READ)
  while sel.get_map():
   assert time.time()<now+180 and time.monotonic()<mono+180 and __import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot
   assert int(subprocess.check_output(['du','-sx','-B1',str(O)]).split()[0])<144*1024**2
   for key,_ in sel.select(.2):
    block=os.read(key.fileobj.fileno(),16384)
    if not block:sel.unregister(key.fileobj);continue
    assert len(data)+len(block)<4*1024**2;data.extend(block)
  child.wait(timeout=5);assert child.returncode==0,('BRIDGE_COMPILE_REFUSED',child.returncode);result.update(passed=True,binary_path=str(binary.relative_to(R)),binary_sha256=sha(binary))
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  if child is not None and child.poll()is None:
   s=__import__('pathlib').Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split();assert s[19]==identity['start_ticks'];os.killpg(identity['pgid'],signal.SIGTERM)
   try:child.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(identity['pgid'],signal.SIGKILL);child.wait(timeout=5)
  (O/'build.console').write_bytes(data);result.update(closed=True,returncode=child.returncode if child else None,wall_s=time.monotonic()-mono,source_unchanged=all(sha(R/k)==h for k,h in binding['files_SHA256'].items()));put(O/'BUILD_RESULT.json',result)
 print(__import__('json').dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
