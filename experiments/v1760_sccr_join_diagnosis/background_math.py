"""One detached CPU4 saved-data diagnosis; no experiment successor."""
import ast,fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):
 t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');t.replace(p)
def main():
 os.sched_setaffinity(0,{5});wall=time.time();mono=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 current=read(R/'CURRENT_EXPERIMENT.json');assert current['active_round']is None and current.get('active_source_round')is None and not current['models_now_authorized']
 assert not(O/'MATH_OWNER_ONCE.json').exists()
 prior=read(R/'runs/v1757_sccr_path_vehicle_gate/POST_ROUND_STORAGE_BARRIER.json');assert prior['passed']and all(sha(R/n)==h for n,h in prior['proof_paths_SHA256'].items())
 for n in ['DETACHED_LAUNCH','SOURCE_OWNED_CHILD','QUERY_OWNED_CHILD','runtime_delivery_OWNED_CHILD']:
  x=read(R/'runs/v1757_sccr_path_vehicle_gate'/(n+'.json'));p=Path('/proc',str(x['pid']),'stat');assert not p.exists()or p.read_text().split()[21]!=x['start_ticks']
 with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 original=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 source=read(R/'runs/v1757_sccr_path_vehicle_gate/SOURCE_FREEZE.json')['files'].copy();source.update(read(C/'INPUTS.json')['files_SHA256'])
 for folder in [C,R/'experiments/v1761_sccr_diagnosis_recovery']:
  for p in folder.iterdir():
   if p.is_file():
    if p.suffix=='.py':ast.parse(p.read_text())
    source[str(p.relative_to(R))]=sha(p)
 assert all(sha(R/n)==h for n,h in source.items())
 seen=set();used=0
 for root,ds,fs in os.walk(R/'runs',followlinks=False):
  for p in [Path(root)]+[Path(root)/n for n in fs]:
   st=p.lstat();key=st.st_dev,st.st_ino
   if key not in seen:seen.add(key);used+=st.st_blocks*512
 assert used+(8+32+32+512)*1024**2<15*1024**3
 put(O/'MATH_OWNER_ONCE.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],boot_id=boot,started_unix=wall,started_monotonic=mono,maximum_target_s=300,root_deadline_unix=wall+5400,root_deadline_monotonic=mono+5400,models=0,allruns_before_bytes=used,peak_reserved_bytes=used+(8+32+32+512)*1024**2,next_round_requires_user_review=True))
 put(O/'SOURCE_FREEZE.json',dict(files=source,models_authorized=False,saved_math_only=True))
 current.update(status='BACKGROUND_SAVED_SCCR_JOIN_DIAGNOSIS',active_math=C.name,models_now_authorized=False,automatic_next_round=False,tonight_overnight_authorized=False);put(R/'CURRENT_EXPERIMENT.json',current)
 result=dict(passed=False,closed=False,models=0,physical_native=0,replay_native=0,original_planner_calls=0,whole_navigation_passed=None);process=None
 try:
  (R/'REVIEW_PENDING').unlink();(O/'mpl_cache').mkdir()
  env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MPLCONFIGDIR=str(O/'mpl_cache'))
  with(O/'math.console').open('xb')as f:
   process=subprocess.Popen(['taskset','-c','4','nice','-n','19','./run_phase.sh',str((C/'analyse.py').relative_to(R))],cwd=R,env=env,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True)
   identity=dict(pid=process.pid,pgid=os.getpgid(process.pid),start_ticks=Path('/proc',str(process.pid),'stat').read_text().split()[21],boot_id=boot);put(O/'MATH_OWNED_CHILD.json',identity)
   while process.poll()is None:
    assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot and time.time()<wall+300 and time.monotonic()<mono+300
    assert (O/'math.console').stat().st_size<=512*1024
    put(O/'RUNNING_CHECKPOINT.json',dict(stage='saved_math',unix=time.time(),models=0,physical_native=0,original_planner_calls=0,remaining_target_s=max(0,min(wall+300-time.time(),mono+300-time.monotonic()))));time.sleep(.5)
  result['returncode']=process.returncode;assert process.returncode==0 and read(O/'DIAGNOSIS.json')['passed'];assert all(sha(R/n)==h for n,h in source.items());result.update(passed=True,all_source_SHA_verified_after_child_exit=True)
  (R/'docs/SCCR_JOIN_DIAGNOSIS_V1760_REPORT.md').write_text((O/'REPORT.md').read_text())
 except BaseException as error:result.update(first_error=repr(error),traceback=traceback.format_exc())
 finally:
  if process is not None and process.poll()is None:
   os.killpg(process.pid,signal.SIGTERM)
   try:process.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
  with(R/'runs/v648_static_unknown/execution.lock').open()as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  (R/'REVIEW_PENDING').write_bytes(original);result.update(closed=True,review_restored=True,wall_s=time.monotonic()-mono,remote_recovery_pending=True,automatic_next_round=False,tonight_overnight_not_authorized=True);put(O/'MATH_OUTER_CLOSED.json',result)
  current=read(R/'CURRENT_EXPERIMENT.json');current.update(status='SCCR_DIAGNOSIS_CLOSED_RECOVERY_PENDING',active_math=None,models_now_authorized=False,automatic_next_round=False,latest_background_result=str((O/'MATH_OUTER_CLOSED.json').relative_to(R)));put(R/'CURRENT_EXPERIMENT.json',current)
 print(json.dumps(result));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
