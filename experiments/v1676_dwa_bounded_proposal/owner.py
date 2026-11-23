"""One bounded CPU2 worker; owner only manages evidence and process identity."""
import fcntl,json,os,selectors,signal,subprocess,time,traceback
from pathlib import Path
from context import C,O,R,REVIEW_SHA,put,read,sha,usage

def main():
 os.sched_setaffinity(0,{5});os.nice(max(0,19-os.getpriority(os.PRIO_PROCESS,0)))
 assert not(O/'NUMERIC_ONCE_CLAIM.json').exists()and not(O/'COMPLETION.json').exists()
 original=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')==REVIEW_SHA
 assert read(R/'runs/v1672_svg_direct_live_component/POST_ROUND_STORAGE_BARRIER.json')['passed']
 parent=read(R/'runs/v1382_weekend_campaign/LEDGER.json')
 assert parent['active_round']is None and parent.get('active_math_round')is None and not parent['models_now_authorized']
 assert read(O/'SOURCE_QUALIFICATION.json')['passed']and read(O/'SOURCE_OUTER_CLOSED.json')['passed']
 frozen=read(O/'SOURCE_FREEZE.json')['files'];assert all(sha(R/n)==h for n,h in frozen.items())
 recovery=read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')
 assert recovery['passed']and recovery['all_frozen_members_remote_chain_covered']and recovery['source_freeze_sha256']==sha(O/'SOURCE_FREEZE.json')
 assert read(R/recovery['full_remote_proof_path'])['passed']and sha(R/recovery['full_remote_proof_path'])==recovery['full_remote_proof_sha256']
 # No launch while another qualified process owns execution, even before our claim.
 with(R/'runs/v648_static_unknown/execution.lock').open()as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 before=usage();assert before+(4+16+32+512)*1024**2<15*1024**3,'NUMERIC_FULL_STORAGE_PEAK'
 wall=time.time();mono=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 a=dict(scope='DWA_REFERENCE_ORIGINAL_RESPONSE_STATIC_SAVED_INPUT',numerical_authorized=True,physical_authorized=False,benchmark_authorized=False,boot_id=boot,source_freeze_sha256=sha(O/'SOURCE_FREEZE.json'),input_sha256=sha(O/'INPUT.json'),constructor_limit=1,solve_limit=1,step_limit=2205,start_wall=wall,start_mono=mono,normal_stop_wall=wall+180,normal_stop_mono=mono+180,root_stop_wall=wall+300,root_stop_mono=mono+300)
 with(O/'NUMERIC_ONCE_CLAIM.json').open('x')as f:json.dump(dict(admission=a,allruns_before_bytes=before,full_peak_bytes=before+(4+16+32+512)*1024**2),f)
 put(O/'ROUND_WINDOW.json',a);put(O/'NUMERIC_ADMISSION.json',a)
 result=dict(passed=False,closed=False,outer_first_error=None,outer_secondary_errors=[],constructor_attempts=None,constructor_returns=None,solve_attempts=None,solve_returns=None,internal_kinematic_rollout_steps=None,physical_native=0,replay_native=0,whole_navigation_passed=False)
 process=None;console=bytearray()
 try:
  (R/'REVIEW_PENDING').unlink()
  env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
  process=subprocess.Popen(['taskset','-c','2','nice','-n','19','ionice','-c','3','./run_phase.sh',str((C/'entry.py').relative_to(R))],cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
  stat=Path('/proc/'+str(process.pid)+'/stat').read_text().split(') ',1)[1].split()
  put(O/'OWNED_CHILD.json',dict(pid=process.pid,pgid=os.getpgid(process.pid),start_ticks=int(stat[19]),boot_id=boot,command='run_phase.sh '+str((C/'entry.py').relative_to(R))))
  selector=selectors.DefaultSelector();selector.register(process.stdout,selectors.EVENT_READ)
  while selector.get_map():
   assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot,'BOOT_CHANGED'
   assert time.time()<wall+180 and time.monotonic()<mono+180,'NUMERIC_180S_LIMIT'
   for key,_ in selector.select(.2):
    data=os.read(key.fileobj.fileno(),16384)
    if not data:selector.unregister(key.fileobj);continue
    assert len(console)+len(data)<=256*1024,'CONSOLE_CAP'
    console.extend(data)
  process.wait(timeout=5)
  if(O/'numeric/RESULT.json').exists():
   inner=read(O/'numeric/RESULT.json');result['machine_result']=inner
   for key in ['constructor_attempts','constructor_returns','response_step_attempts','response_step_returns','response_step_inflight']:result[key]=inner.get(key)
   result['passed']=process.returncode==0 and inner['passed']and inner['closed']
  else:result['machine_result_missing']=True
 except BaseException as e:result.update(outer_first_error=repr(e),traceback=traceback.format_exc())
 finally:
  if process is not None and process.poll()is None:
   try:
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
   except BaseException as e:result['outer_secondary_errors'].append(dict(stage='CHILD_CLOSE',error=repr(e)))
  if process is not None:result['child_returncode']=process.returncode
  for stage,action in [
   ('CONSOLE_SAVE',lambda:(O/'numeric.console').write_bytes(console)),
   ('SOURCE_AFTER_EXIT',lambda:all(sha(R/n)==h for n,h in frozen.items())),
   ('REVIEW_RESTORE',lambda:(R/'REVIEW_PENDING').write_bytes(original))]:
   try:
    value=action()
    if stage=='SOURCE_AFTER_EXIT':
     result['all_source_SHA_after_child_exit']=value
     if not value:result['passed']=False
   except BaseException as e:result['outer_secondary_errors'].append(dict(stage=stage,error=repr(e)));result['passed']=False
  result.update(closed=True,wall_s=time.monotonic()-mono,review_restored=sha(R/'REVIEW_PENDING')==REVIEW_SHA,allruns_after_bytes=usage())
  if result['outer_secondary_errors']or not result['review_restored']:result['passed']=False
  put(O/'COMPLETION.json',result)
 print(json.dumps(result,allow_nan=False));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
