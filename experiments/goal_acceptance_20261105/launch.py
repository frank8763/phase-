"""One detached claim, never a navigation retry or a deadline reset."""
import fcntl,os,subprocess,sys,time
from pathlib import Path
from evidence_rules import dump,read,sha
repo=Path(__file__).resolve().parents[2];own=Path(__file__).parent;root=repo/'runs/goal_acceptance_20261105'
with(root/'launch.lock').open('a+')as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if(root/'LAUNCH.json').exists()or(root/'ROUND_WINDOW.json').exists():print('ALREADY_CLAIMED_NO_SECOND_INSTANCE');raise SystemExit(0)
 assert read(root/'PREPARED.json')['status']=='BOTH_STAGES_FROZEN_AND_ZERO_MODEL_QUALIFIED'
 for name in ['v827_goal_route_validation','v828_goal_dynamic_confirmation']:
  assert sha(repo/'experiments'/name/'CANDIDATE_FREEZE.json')==read(root/'PREPARED.json')['source_freezes'][name]
  freeze=read(repo/'experiments'/name/'CANDIDATE_FREEZE.json');assert all(sha(repo/p)==h for p,h in freeze['files'].items())
 auth=read(repo/'RPCCR_GOAL_ACCEPTANCE_AUTHORIZATION_20261105.json');assert time.time()+53000<auth['absolute_deadline_unix'];assert(repo/'REVIEW_PENDING').exists()
 with(repo/'runs/v648_static_unknown/execution.lock').open('rb')as check:fcntl.flock(check,fcntl.LOCK_EX|fcntl.LOCK_NB)
 data=dict(status='CLAIMED',claimed_at_unix=time.time(),absolute_deadline_unix=auth['absolute_deadline_unix'],new_models=0,new_integrations=0,launch_attempts=1);dump(root/'LAUNCH.json',data)
 with(root/'campaign.console').open('x')as stream:
  cap=int(auth['absolute_deadline_unix']-time.time())+1810
  child=subprocess.Popen(['timeout','--signal=TERM','--kill-after=10s',str(cap)+'s',sys.executable,'-B',str(own/'campaign.py')],cwd=repo,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
 data.update(status='DETACHED_CAMPAIGN_STARTED',outer_pid=child.pid,outer_total_cap_s=cap);dump(root/'LAUNCH.json',data);print(__import__('json').dumps(data))
