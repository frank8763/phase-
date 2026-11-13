"""One30s source push and one5s remote HEAD read; never retry."""
import sys,json,time,os,subprocess,signal,re
from pathlib import Path
R=Path(__file__).resolve().parents[2];D=R/'records/nav2_v1113_20261113'
def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def main():
    assert not(D/'GIT_SYNC_CLAIM.json').exists()and not(D/'GIT_SYNC_RESULT.json').exists()
    assert subprocess.check_output(['git','remote','get-url','origin'],cwd=R,text=True).strip()=='https://github.com/frank8763/phase-.git'
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
    dump(D/'GIT_SYNC_CLAIM.json',dict(at=time.time(),head=head,push_limit_s=30,readonly_verify_limit_s=5,no_retries=True))
    env=dict(os.environ,GIT_TERMINAL_PROMPT='0')
    for name in ['GIT_TRACE','GIT_TRACE_CURL','GIT_CURL_VERBOSE','GIT_TRACE_PACKET','GIT_TRACE2_EVENT','GIT_TRACE2_PERF','GIT_TRACE_PERFORMANCE']:
        env.pop(name,None)
    def run(args,limit):
        p=subprocess.Popen(args,cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True)
        try:output=p.communicate(timeout=limit)[0];return dict(returncode=p.returncode,output=output[-1200:])
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL);p.communicate();return dict(returncode=None,timed_out=True)
    pushed=run(['git','push','origin','HEAD:main'],30)
    verified=run(['git','ls-remote','--heads','origin','main'],5)
    matches=re.findall(r'^([0-9a-f]{40})\s+refs/heads/main$',verified.get('output',''),re.M)
    remote=matches[0]if verified.get('returncode')==0 and len(matches)==1 else None
    result=dict(head=head,push=pushed,readonly_verification=verified,remote_head=remote,remote_verified=remote==head,push_attempts=1,verification_attempts=1,no_retry=True,models=0,integrations=0)
    dump(D/'GIT_SYNC_RESULT.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
