"""One source push, bounded to30s, then one5s remote HEAD read; no retry loop."""
import json,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];REC=R/'records/nav2_v861_20261107';O=R/'runs/v861_startup_gate/cloud'
def run(args,timeout):return subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=timeout)
def main():
 assert json.loads((REC/'FULL_REMOTE_VERIFIED.json').read_text())['passed'];assert(R/'REVIEW_PENDING').exists()
 with(REC/'SOURCE_SYNC_CLAIM.json').open('x')as f:json.dump(dict(started_unix=time.time(),push_budget_s=30,read_budget_s=5),f)
 check=run(['git','diff','--cached','--check'],10);assert check.returncode==0
 commit=run(['git','commit','-m','Record V861 readiness gates and fixed curve qualification'],30);assert commit.returncode==0,commit.stderr
 head=run(['git','rev-parse','HEAD'],5).stdout.strip();result=dict(source_commit=head,attempted_once=True,push_succeeded=False,remote_head_verified=False)
 try:
  push=run(['git','push','origin','main'],30);result.update(push_returncode=push.returncode,push_succeeded=push.returncode==0)
  (O/'source_push.console').write_text(push.stdout+push.stderr)
 except subprocess.TimeoutExpired:result['push_error']='PUSH_30S_TIMEOUT_NO_RETRY'
 try:
  verify=run(['git','ls-remote','origin','refs/heads/main'],5);remote=verify.stdout.split()[0]if verify.returncode==0 and verify.stdout.strip()else None;result.update(remote_head=remote,remote_head_verified=remote==head)
 except subprocess.TimeoutExpired:result['remote_read_error']='READ_5S_TIMEOUT_NO_RETRY'
 result['completed_unix']=time.time()
 for p in [O/'SOURCE_SYNC_RESULT.json',REC/'SOURCE_SYNC_RESULT.json']:p.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result),flush=True)
if __name__=='__main__':main()
