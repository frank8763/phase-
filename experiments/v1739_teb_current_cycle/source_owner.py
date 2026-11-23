"""One source owner, exact child identity and original REVIEW restoration."""
import fcntl,json,os,selectors,signal,subprocess,time,traceback
from pathlib import Path
from context import C,O,R,read,put,sha
def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)));lock=(O/'OWNER.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not any((O/n).exists()for n in ['SOURCE_OUTER_ONCE_CLAIM.json','SOURCE_QUALIFICATION.json','SOURCE_OUTER_CLOSED.json'])
 assert read(O/'BINARY_BINDING.json')['passed']
 assert all(sha(row['target'])==row['original_target_sha256']for row in read(O/'EXACT_NATIVE_ALIASES.json')['aliases'])
 sync=read(R/'runs/v1740_teb_current_cycle_source_recovery/SOURCE_SYNC_RESULT.json');assert sync['remote_verified']
 for p in C.iterdir():
  if p.is_file():assert subprocess.check_output(['git','show',sync['head']+':'+str(p.relative_to(R))],cwd=R)==p.read_bytes()
 assert not(O/'ROUND_WINDOW.json').exists();now=time.time();mono=time.monotonic();put(O/'ROUND_WINDOW.json',dict(started_unix=now,started_monotonic=mono,normal_end_unix=now+4200,normal_end_monotonic=mono+4200,root_end_unix=now+5400,root_end_monotonic=mono+5400,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()))
 window=read(O/'ROUND_WINDOW.json');boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert boot==window['boot_id']and time.time()+150<window['normal_end_unix']and time.monotonic()+150<window['normal_end_monotonic']
 review=R/'REVIEW_PENDING';original=review.read_bytes();assert sha(review)=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 parent=read(R/'CURRENT_EXPERIMENT.json');assert parent['active_round']is None and not parent['models_now_authorized']
 used=int(subprocess.check_output(['du','-sx','-B1',str(R/'runs')]).split()[0]);assert used+(224+32+32+512)*1024**2<15*1024**3
 now=time.time();mono=time.monotonic();put(O/'SOURCE_OUTER_ONCE_CLAIM.json',dict(owner_pid=os.getpid(),maximum_s=150,unix=now,monotonic=mono,boot_id=boot,models_authorized=False));child=None;data=bytearray();result=dict(passed=False,closed=False,models=0,optimizer_calls=0,physical_native=0,replay_native=0)
 try:
  review.unlink();env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MUJOCO_GL='osmesa')
  child=subprocess.Popen(['taskset','-c','2','nice','-n','19','ionice','-c','3','./run_phase.sh',str((C/'source_target.py').relative_to(R))],cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True);s=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split();identity=dict(pid=child.pid,pgid=os.getpgid(child.pid),start_ticks=s[19],boot_id=boot);put(O/'SOURCE_OWNED_CHILD.json',identity);sel=selectors.DefaultSelector();sel.register(child.stdout,selectors.EVENT_READ)
  while sel.get_map():
   assert time.time()<now+150 and time.monotonic()<mono+150 and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot
   for key,_ in sel.select(.2):
    block=os.read(key.fileobj.fileno(),16384)
    if not block:sel.unregister(key.fileobj);continue
    assert len(data)+len(block)<=512*1024;data.extend(block)
  child.wait(timeout=5);inner=read(O/'SOURCE_QUALIFICATION.json');assert child.returncode==0 and inner['passed'];frozen=read(O/'SOURCE_FREEZE.json');assert all(sha(R/k)==h for k,h in frozen['files'].items())and all(sha(k)==h for k,h in frozen['external_SHA256'].items());result.update(passed=True,all_source_SHA_verified_after_child_exit=True,explicit_DLL_loads=inner['explicit_DLL_loads'],metadata_FFI_calls=inner['metadata_FFI_calls'],complete_runtime_qualified=False)
 except BaseException as e:result.update(first_error=repr(e),traceback=traceback.format_exc())
 finally:
  if child is not None and child.poll()is None:
   s=Path('/proc',str(child.pid),'stat').read_text().split(') ',1)[1].split();assert s[19]==identity['start_ticks'];os.killpg(identity['pgid'],signal.SIGTERM)
   try:child.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(identity['pgid'],signal.SIGKILL);child.wait(timeout=5)
  (O/'source.console').write_bytes(data);review.write_bytes(original);assert all(sha(row['target'])==row['original_target_sha256']for row in read(O/'EXACT_NATIVE_ALIASES.json')['aliases']);result.update(closed=True,returncode=child.returncode if child else None,wall_s=time.monotonic()-mono,review_restored=sha(review)=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66');put(O/'SOURCE_OUTER_CLOSED.json',result)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
