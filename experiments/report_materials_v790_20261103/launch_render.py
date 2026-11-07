"""One bounded render of already recorded states; always restore review guard."""
import fcntl,hashlib,json,os,signal,subprocess,time
from pathlib import Path
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;guard=repo/'REVIEW_PENDING';log=repo/'runs/v790_render.console';record=repo/'runs/global_dynamic_overnight_20261103/RENDER_LAUNCH.json'
assert guard.exists()and not log.exists()and not record.exists();saved=guard.read_bytes()
with(repo/'runs/v648_static_unknown/execution.lock').open('a+')as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
freeze=json.loads((own/'RENDER_INPUT_FREEZE.json').read_text());assert all(hashlib.sha256((repo/p).read_bytes()).hexdigest()==h for p,h in freeze['files'].items())
started=time.time();deadline=min(started+605,1793750400.);assert deadline-started>=605;process=None;result=dict(status='RUNNING',started_unix=started,absolute_deadline_unix=deadline,role='SAVED_STATE_VISUALIZATION_ONLY',navigation_integrations=0,prediction_integrations=0,replay_integrations=0)
record.write_text(json.dumps(result,indent=2)+'\n')
try:
 guard.unlink()
 with log.open('x')as stream:
  process=subprocess.Popen([str(repo/'run_phase.sh'),str(own.relative_to(repo)/'render_saved_v790.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
  result['pid']=process.pid;record.write_text(json.dumps(result,indent=2)+'\n')
  try:result['exit_code']=process.wait(timeout=deadline-time.time())
  finally:
   if process.poll()is None:
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=2)
    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
 assert result['exit_code']==0,'SAVED_RENDER_FAILED'
 result['status']='SAVED_RENDER_COMPLETE'
finally:
 guard.write_bytes(saved);result.update(review_guard_restored=guard.read_bytes()==saved,elapsed_s=time.time()-started);record.write_text(json.dumps(result,indent=2)+'\n')
