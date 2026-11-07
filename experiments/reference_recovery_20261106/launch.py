"""One unique detached offline launch, never retries a model or old window."""
import fcntl,os,signal,subprocess,sys,time
from pathlib import Path
from evidence_rules import read,dump,sha
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;root=repo/'runs/reference_recovery_20261106'
assert (repo/'REVIEW_PENDING').exists()and(root/'PREPARED.json').exists()
claim=root/'LAUNCH_CLAIM.json'
fd=os.open(claim,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
os.write(fd,str(time.time()).encode());os.close(fd)
assert not(root/'ROUND_WINDOW.json').exists()
with(repo/'runs/v648_static_unknown/execution.lock').open('rb')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
deadline=read(repo/'RPCCR_REFERENCE_RECOVERY_AUTHORIZATION_20261106.json')['absolute_deadline_unix']
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
with(root/'campaign.console').open('x')as log:
 process=subprocess.Popen(['timeout','--signal=TERM','--kill-after=5',str(max(1,int(deadline-time.time()+2100))),sys.executable,'-B',str(common/'run_campaign.py')],cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,stdin=subprocess.DEVNULL)
dump(root/'LAUNCHED.json',dict(outer_pid=process.pid,started_unix=time.time(),absolute_deadline_unix=deadline,launch_attempts=1,offline=True,models_only_run_phase=True))
print('LAUNCHED_OFFLINE_BOUNDED_CAMPAIGN',process.pid)
