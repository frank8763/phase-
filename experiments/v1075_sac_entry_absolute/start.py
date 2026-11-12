"""One bounded native component. No route/training/retry dispatch."""
import subprocess,fcntl,signal
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'experiments/v1074_sac_native_control'))
from common import *
paths();from resource_policy import apply
apply();assert not(R/'runs/v1075_sac_entry_absolute/CLAIM.json').exists();dump(R/'runs/v1075_sac_entry_absolute/CLAIM.json',dict(single_entry_continuation=True));assert json.loads((O/'QUALIFICATION.json').read_text())['passed'];assert all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items());guard=(R/'REVIEW_PENDING').read_bytes();assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN);tasks=json.loads((C/'TASKS.json').read_text());task=tasks[0];dump(O/'TASK.json',task);(O/'GUARD.bin').write_bytes(guard);window=json.loads((O/'ROUND_WINDOW.json').read_text());wall=window['started_unix'];assert time.time()<window['absolute_deadline_unix']and time.monotonic()<window['hard_stop_monotonic'];dump(O/'APPROVAL.json',dict(models_authorized=True,absolute_deadline_unix=window['absolute_deadline_unix'],allowed_task_ids=[task['task_id']],single_entry_exception=True));p=None;code=None
try:
 (R/'REVIEW_PENDING').unlink()
 with(R/'runs/v1075_sac_entry_absolute/worker.console').open('x')as log:
  p=subprocess.Popen([str(R/'run_phase.sh'),'experiments/v1075_sac_entry_absolute/entry.py'],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);dump(O/'ACTIVE.json',dict(pid=p.pid,task_id=task['task_id']));code=p.wait(timeout=305)
except BaseException as e:
 dump(O/'PARENT_ERROR.json',dict(error=repr(e),no_retry=True))
 if p is not None and p.poll()is None:
  try:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=3)
  except BaseException:
   try:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=3)
   except ProcessLookupError:pass
finally:
 (R/'REVIEW_PENDING').write_bytes(guard);dump(O/'APPROVAL.json',dict(models_authorized=False,closed=True));dump(O/'ACTIVE.json',dict(closed=True))
out=Path(task['output']);result_path=out/'RESULT.json';fallback=out/'physics/paired/ENTRY_FAILURE_RESULT.json';path=result_path if result_path.exists()else fallback;result=json.loads(path.read_text())if path.exists()else dict(passed=False,vehicle_initializations=None,navigation_native=None,own_replay_native=None,missing_result=True);result.update(parent_returncode=code,guard_original=(R/'REVIEW_PENDING').read_bytes()==guard,closed=True,source_unchanged=all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items()));dump(R/'runs/v1075_sac_entry_absolute/COMPLETION.json',result);print(json.dumps(result),flush=True)
