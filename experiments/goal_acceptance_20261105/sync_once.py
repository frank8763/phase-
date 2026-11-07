"""The sole bounded repository sync for the closed GOAL_ACCEPTANCE round."""
import json,os,re,signal,subprocess,time
from pathlib import Path
repo=Path(__file__).resolve().parents[2];root=repo/'runs/goal_acceptance_20261105'
assert(root/'ZERO_MODEL_CLOSURE.json').exists()and(repo/'REVIEW_PENDING').exists()
result_path=root/'GIT_SYNC_RESULT.json';claim=root/'GIT_SYNC_CLAIM.json'
assert not result_path.exists()and not claim.exists(),'SYNC_ALREADY_CLAIMED_NO_RETRY'
started=time.time();claim.write_text(json.dumps(dict(status='ONLY_FINAL_SYNC_CLAIMED',started_unix=started,max_push_s=30,max_read_only_head_s=5),indent=2)+'\n')
target=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
remote=subprocess.check_output(['git','remote','get-url','origin'],cwd=repo,text=True).strip()
assert remote=='https://github.com/frank8763/phase-.git','UNEXPECTED_CANONICAL_REMOTE'
env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GIT_TRACE='0',GIT_TRACE_CURL='0',GIT_CURL_VERBOSE='0',GIT_TRACE_PACKET='0',GIT_TRACE2='0')
def bounded(args,name,seconds):
    start=time.monotonic()
    with(root/name).open('xb')as stream:
        p=subprocess.Popen(args,cwd=repo,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        timed_out=False
        try:code=p.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            timed_out=True;os.killpg(p.pid,signal.SIGKILL);p.wait();code=124
    return dict(returncode=code,timed_out=timed_out,wall_s=time.monotonic()-start,cap_s=seconds)
push=bounded(['git','push','origin','main'],'git_push.console',30)
verify=bounded(['git','ls-remote','origin','refs/heads/main'],'git_remote_head.console',5)
raw=(root/'git_remote_head.console').read_text(errors='replace');match=re.search(r'(?m)^([0-9a-f]{40})\s+refs/heads/main\s*$',raw);head=match.group(1)if match else None
out=dict(status='SCIENTIFIC_COMMIT_REMOTE_VERIFIED'if head==target else'REMOTE_SCIENTIFIC_COMMIT_NOT_VERIFIED',started_unix=started,finished_unix=time.time(),target_scientific_commit=target,push=push,read_only_verification=verify,remote_head=head,remote_scientific_commit_verified=head==target,remote_state='AT_TARGET'if head==target else'KNOWN_DIFFERENT_HEAD'if head else'UNKNOWN',network_retries=0,old_round_sync_retried=False,raw_evidence_deleted=False)
result_path.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)
