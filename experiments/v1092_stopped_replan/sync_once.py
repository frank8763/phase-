"""One30s source push and one5s remote HEAD read; never retry."""
import sys,json,time,os,subprocess,signal
from pathlib import Path
R=Path(__file__).resolve().parents[2];D=R/'records/nav2_v1092_20261113'
def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def main():
    assert not(D/'GIT_SYNC_CLAIM.json').exists()and not(D/'GIT_SYNC_RESULT.json').exists()
    assert subprocess.check_output(['git','remote','get-url','origin'],cwd=R,text=True).strip()=='https://github.com/frank8763/phase-.git'
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
    dump(D/'GIT_SYNC_CLAIM.json',dict(at=time.time(),head=head,push_limit_s=30,readonly_verify_limit_s=5,no_retries=True))
    env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GIT_TRACE='0',GIT_TRACE_CURL='0',GIT_CURL_VERBOSE='0')
    def run(args,limit):
        p=subprocess.Popen(args,cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True)
        try:output=p.communicate(timeout=limit)[0];return dict(returncode=p.returncode,output=output[-1200:])
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL);p.communicate();return dict(returncode=None,timed_out=True)
    pushed=run(['git','push','origin','HEAD:main'],30)
    verified=run(['git','ls-remote','--heads','origin','main'],5)
    remote=verified.get('output','').split()[0]if verified.get('returncode')==0 and verified.get('output','').strip()else None
    result=dict(head=head,push=pushed,readonly_verification=verified,remote_head=remote,remote_verified=remote==head,push_attempts=1,verification_attempts=1,no_retry=True,models=0,integrations=0)
    dump(D/'GIT_SYNC_RESULT.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
