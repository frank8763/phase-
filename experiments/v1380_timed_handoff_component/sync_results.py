"""One new-round bounded result sync, never retry old or this round."""
import os
import re
import subprocess
from component_context import *


def main():
    claim=O/'SYNC_CLAIM.json';assert not claim.exists() and not (O/'SYNC_RESULT.json').exists()
    assert read(O/'FINALIZED.json')['local_memberSHA_and_reassembly_verified']
    dump(claim,dict(started_unix=time.time(),maximum_push_attempts=1,push_limit_s=30,verify_limit_s=5,models=0))
    result=dict(remote_verified=False,retry_allowed=False,models=0,raw_deleted=False)
    try:
        assert not subprocess.run(['git','diff','--cached','--name-only'],cwd=R,capture_output=True,text=True,check=True).stdout.strip()
        index=read(O/'ARCHIVE_INDEX.json');record=R/'records/timed_handoff_v1380_20261120';record.mkdir(exist_ok=False)
        dump(record/'ARCHIVE_INDEX.json',index)
        for part in index['parts']:
            p=O/'archive'/part['name'];assert sha(p)==part['sha256'] and part['bytes']<=32*1024**2;os.link(p,record/part['name'])
        paths=[str(C.relative_to(R)),'experiments/v1379_timed_response_preparation','docs/TIMED_HANDOFF_V1379_PREPARATION_REPORT.md','CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/TIMED_HANDOFF_V1380_REPORT.md',str(record.relative_to(R))]
        subprocess.run(['git','add','--',*paths],cwd=R,check=True,capture_output=True,timeout=15)
        compact=[p for p in O.glob('*.json') if p.stat().st_size<2*1024**2]
        subprocess.run(['git','add','-f','--',*[str(p.relative_to(R)) for p in compact]],cwd=R,check=True,capture_output=True,timeout=15)
        subprocess.run(['git','add','-f','--','runs/v1374_day_handoff_validation/DAY_LEDGER.json'],cwd=R,check=True,capture_output=True,timeout=15)
        subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True,capture_output=True,timeout=10)
        subprocess.run(['git','commit','-m','Record original32210 timed handoff pair and audited evidence'],cwd=R,check=True,capture_output=True,timeout=20)
        head=subprocess.run(['git','rev-parse','HEAD'],cwd=R,capture_output=True,text=True,check=True).stdout.strip();result['head']=head
        try:
            p=subprocess.run(['git','push','origin','main'],cwd=R,capture_output=True,text=True,timeout=30)
            result.update(push_returncode=p.returncode,push_output=re.sub(r'https://[^/@\s]+:[^/@\s]+@','https://<REDACTED>@',p.stdout+p.stderr))
        except subprocess.TimeoutExpired:result['push_error']='PUSH_TIMEOUT_30S'
        try:
            p=subprocess.run(['git','ls-remote','origin','refs/heads/main'],cwd=R,capture_output=True,text=True,timeout=5)
            result['remote_head']=p.stdout.split()[0] if p.returncode==0 and p.stdout.strip() else None;result['remote_verified']=result['remote_head']==head
        except subprocess.TimeoutExpired:result['verify_error']='READONLY_TIMEOUT_5S'
    except BaseException as exc:result['error']=repr(exc)
    dump(O/'SYNC_RESULT.json',dict(result,closed_unix=time.time()))
    return 0 if result['remote_verified'] else 1


if __name__=='__main__':raise SystemExit(main())
