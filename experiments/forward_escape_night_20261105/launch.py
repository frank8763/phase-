"""One detached local claim, independent of network/interactive shell."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from evidence_rules import dump,read,sha
repo=Path(__file__).resolve().parents[2];common=Path(__file__).parent;root=repo/'runs/forward_escape_night_20261105';own=repo/'experiments/v832_forward_escape_development'
with(root/'launch.lock').open('a+')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not(root/'LAUNCH.json').exists()and not(root/'ROUND_WINDOW.json').exists(),'ALREADY_CLAIMED_NO_SECOND_INSTANCE'
 prepared=read(root/'PREPARED.json');assert prepared['status']=='ONE_CANDIDATE_FROZEN_AND_ZERO_MODEL_QUALIFIED'
 freeze=read(own/'CANDIDATE_FREEZE.json');assert sha(own/'CANDIDATE_FREEZE.json')==prepared['source_freezes'][own.name]and all(sha(repo/n)==h for n,h in freeze['files'].items())
 deadline=read(repo/'RPCCR_FORWARD_ESCAPE_NIGHT_AUTHORIZATION_20261105.json')['absolute_deadline_unix'];assert time.time()+24003<deadline
 assert(repo/'REVIEW_PENDING').exists()
 with(repo/'runs/v648_static_unknown/execution.lock').open('rb')as probe:fcntl.flock(probe,fcntl.LOCK_EX|fcntl.LOCK_NB)
 data=dict(status='CLAIMED',claimed_unix=time.time(),absolute_deadline_unix=deadline,launch_attempts=1,models=0,integrations=0);dump(root/'LAUNCH.json',data)
 with(root/'campaign.console').open('x')as stream:
  cap=int(deadline-time.time())+1910
  child=subprocess.Popen(['timeout','--signal=TERM','--kill-after=10s',str(cap)+'s',sys.executable,'-B',str(common/'campaign.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
 data.update(status='DETACHED_OFFLINE_CAMPAIGN_STARTED',outer_pid=child.pid,outer_cap_s=cap);dump(root/'LAUNCH.json',data);print(__import__('json').dumps(data))
