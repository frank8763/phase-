"""One idempotent detached V826 launch; no model API in this launcher."""
import fcntl,hashlib,json,os,subprocess,sys,time
from pathlib import Path
repo=Path(__file__).resolve().parents[2];day=repo/'runs/goal_renewal_20261105';own=repo/'experiments/v826_goal_reference_renewal';root=repo/'runs/v826_goal_reference_renewal'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
with(day/'navigation_launch.lock').open('a+')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 claim=day/'V826_LAUNCH.json'
 if claim.exists()or(root/'ROUND_WINDOW.json').exists():print('ALREADY_CLAIMED_NO_SECOND_INSTANCE');raise SystemExit(0)
 qualified=read(repo/'runs/v825_goal_renewal_native_entry/FINALIZED.json');assert qualified['primary282_native_qualified']and qualified['source_and_decompressed_sha_verified']
 freeze=read(own/'CANDIDATE_FREEZE.json');assert all(sha(repo/p)==h for p,h in freeze['files'].items())
 auth=read(repo/'RPCCR_GOAL_RENEWAL_AUTHORIZATION_20261105.json');assert auth['absolute_deadline_unix']-time.time()>5000
 assert(repo/'REVIEW_PENDING').exists()
 with(repo/'runs/v648_static_unknown/execution.lock').open('rb')as check:fcntl.flock(check,fcntl.LOCK_EX|fcntl.LOCK_NB)
 data=dict(status='CLAIMED',claimed_at_unix=time.time(),absolute_deadline_unix=auth['absolute_deadline_unix'],source_freeze_sha256=sha(own/'CANDIDATE_FREEZE.json'),model_initializations_in_launcher=0)
 dump(claim,data)
 with(day/'v826_driver.console').open('x')as stream:
  cap=int(auth['absolute_deadline_unix']-time.time())+1810
  child=subprocess.Popen(['timeout','--signal=TERM','--kill-after=5s',str(cap)+'s',sys.executable,'-B',str(own/'execute_development.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
 data.update(status='DETACHED_DRIVER_STARTED',outer_pid=child.pid,outer_total_cap_s=cap);dump(claim,data);print(json.dumps(data))
