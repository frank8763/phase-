"""Conditional saved continuation, exact parent deadline; no root reset."""
import subprocess,fcntl,signal
from common import *
paths();from resource_policy import apply
RESOURCE=apply();own=(O/'driver.lock').open('a+');fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB);assert not(O/'ROUND_WINDOW.json').exists();assert json.loads((O/'QUALIFICATION.json').read_text())['passed']and json.loads((O/'ENTRY_QUALIFICATION.json').read_text())['passed'];assert json.loads((R/'runs/v1077_speed125_response/COMPLETION.json').read_text())['response_5_passed'];assert all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items());guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';w=json.loads((R/'runs/v1077_speed125_response/ROUND_WINDOW.json').read_text());assert time.time()<w['absolute_deadline_unix']-950 and time.monotonic()<w['hard_stop_monotonic']-950;dump(O/'ROUND_WINDOW.json',w);task=json.loads((O/'TASK.json').read_text());dump(O/'APPROVAL.json',dict(models_authorized=True,absolute_deadline_unix=w['absolute_deadline_unix'],allowed_task_ids=[task['task_id']]));(O/'GUARD.bin').write_bytes(guard);child=None;code=None
try:
 (R/'REVIEW_PENDING').unlink()
 with(O/'worker.console').open('x')as log:
  child=subprocess.Popen([str(R/'run_phase.sh'),str((C/'worker.py').relative_to(R)),str(O/'TASK.json')],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);dump(O/'ACTIVE.json',dict(pid=child.pid,task_id=task['task_id']));code=child.wait(timeout=905)
except BaseException as e:dump(O/'PARENT_ERROR.json',dict(error=repr(e),no_model_retry=True))
finally:
 if child is not None and child.poll()is None:
  try:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=3)
  except BaseException:
   try:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=3)
   except ProcessLookupError:pass
 (R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'ACTIVE.json',dict(closed=True))
out=Path(task['output']);p=out/'RESULT.json';fallback=out/'physics/paired/ENTRY_FAILURE_RESULT.json';p=p if p.exists()else fallback;result=json.loads(p.read_text())if p.exists()else dict(passed=False,vehicle_initializations=None,historical_replay_native=None,recovery_native=None,own_replay_native=None,missing_result=True);result.update(parent_returncode=code,guard_original=(R/'REVIEW_PENDING').read_bytes()==guard,source_unchanged=all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items()),same_absolute_and_monotonic_root=w==json.loads((R/'runs/v1077_speed125_response/ROUND_WINDOW.json').read_text()));dump(O/'COMPLETION.json',result)
if result['passed']and code==0:
 p=subprocess.run([sys.executable,'-B',str(C/'audit_saved.py')],cwd=R,capture_output=True,text=True,timeout=90);(O/'audit.console').write_text(p.stdout+p.stderr);result['independent_audit_passed']=p.returncode==0;result['passed']=result['passed']and p.returncode==0;dump(O/'COMPLETION.json',result)
print(json.dumps(result),flush=True)
