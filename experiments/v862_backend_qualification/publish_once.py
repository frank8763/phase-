"""Single bounded publication of supplemental no-model qualification records."""
import json,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];REC=R/'records/nav2_v862_backend_20261107'
def main():
    proof=json.loads((REC/'INDEPENDENT_AUDIT.json').read_text());assert proof['passed']and proof['actual_native_integrations']==0
    with(REC/'GIT_SYNC_CLAIM.json').open('x')as f:json.dump(dict(started_unix=time.time(),scope='SUPPLEMENTAL_ZERO_MODEL_QUALIFICATION_ONLY'),f)
    subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True)
    subprocess.run(['git','commit','-m','Qualify frozen V862 backend loop with ten model-free fault cases'],cwd=R,check=True,timeout=30)
    head=subprocess.run(['git','rev-parse','HEAD'],cwd=R,check=True,capture_output=True,text=True).stdout.strip();result=dict(source_commit=head,push_succeeded=False,remote_head_verified=False,attempted_once=True)
    try:
        p=subprocess.run(['git','push','origin','main'],cwd=R,capture_output=True,text=True,timeout=30);result.update(push_returncode=p.returncode,push_succeeded=p.returncode==0);(REC/'source_push.console').write_text(p.stdout+p.stderr)
    except subprocess.TimeoutExpired:result['push_error']='30S_TIMEOUT_NO_RETRY'
    try:
        p=subprocess.run(['git','ls-remote','origin','refs/heads/main'],cwd=R,capture_output=True,text=True,timeout=5);remote=p.stdout.split()[0]if p.returncode==0 and p.stdout.strip()else None;result.update(remote_head=remote,remote_head_verified=remote==head)
    except subprocess.TimeoutExpired:result['read_error']='5S_TIMEOUT_NO_RETRY'
    result['completed_unix']=time.time();(REC/'GIT_SYNC_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
