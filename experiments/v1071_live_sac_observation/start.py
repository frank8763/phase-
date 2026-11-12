"""One archived-sensor task; no navigation authority."""
import json,time,hashlib,subprocess,sys,os,fcntl
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1071_live_sac_observation';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert not(O/'ROUND_WINDOW.json').exists();assert json.loads((O/'SOFTWARE_QUALIFICATION.json').read_text())['passed'];assert all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items());assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN);guard=(R/'REVIEW_PENDING').read_bytes();(O/'GUARD.bin').write_bytes(guard);wall=time.time();mono=time.monotonic();w=dict(started_unix=wall,started_monotonic=mono,absolute_deadline_unix=wall+5400,hard_stop_monotonic=mono+5400,duration_s=5400,task_outer_deadline_unix=wall+125,max_model_initializations=1,navigation_authorized=False,training_authorized=False,scope='One archived sensor component, no navigation',user_request='下一步开始，抓紧将这个论文做完',old_windows_unchanged=True);(O/'ROUND_WINDOW.json').write_text(json.dumps(w,indent=2)+'\n');(O/'APPROVAL.json').write_text(json.dumps(dict(archived_sensor_model_authorized=True,navigation_authorized=False,training_authorized=False))+'\n');p=None
try:
 (R/'REVIEW_PENDING').unlink()
 with(O/'worker.console').open('x')as log:
  p=subprocess.Popen([str(R/'run_phase.sh'),str((C/'worker.py').relative_to(R))],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);(O/'ACTIVE.json').write_text(json.dumps(dict(pid=p.pid,pid_start=Path('/proc',str(p.pid),'stat').read_text().rsplit(')',1)[1].split()[19],task='archived_sensor_component'))+'\n');code=p.wait(timeout=125)
except BaseException as e:
 if p is not None and p.poll()is None:
  import signal
  try:os.killpg(p.pid,signal.SIGTERM);p.wait(3)
  except BaseException:
   try:os.killpg(p.pid,signal.SIGKILL);p.wait(3)
   except ProcessLookupError:pass
 (O/'PARENT_ERROR.json').write_text(json.dumps(dict(error=repr(e),no_model_retry=True))+'\n');code=1
finally:
 (R/'REVIEW_PENDING').write_bytes(guard);(O/'APPROVAL.json').write_text(json.dumps(dict(archived_sensor_model_authorized=False,closed=True,navigation_authorized=False,training_authorized=False))+'\n');(O/'ACTIVE.json').write_text(json.dumps(dict(closed=True))+'\n')
result=json.loads((O/'RESULT.json').read_text())if(O/'RESULT.json').exists()else dict(passed=False,model_initializations=None,navigation_native=0,error='MISSING_RESULT_UNKNOWN_MODEL_COUNT');result.update(parent_returncode=code,guard_original=sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66',closed=True);(O/'COMPLETION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
