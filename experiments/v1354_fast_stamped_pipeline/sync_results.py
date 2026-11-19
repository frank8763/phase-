"""One bounded result commit/push after offline closure; no model or retries."""
import json
import os
from pathlib import Path
import re
import subprocess
import time
from component_context import R,C,O,read,dump,sha


def main():
    claim=O/'SOURCE_SYNC_CLAIM.json'
    assert not claim.exists() and not (O/'SOURCE_SYNC_RESULT.json').exists(),'ROUND_SYNC_ALREADY_CLAIMED'
    assert read(O/'FINALIZED.json')['local_archive_all_member_and_reassembled_SHA_passed']
    dump(claim,dict(started_unix=time.time(),push_attempts_maximum=1,push_limit_s=30,verify_limit_s=5,models=0))
    result=dict(remote_verified=False,one_attempt=True,retry_allowed=False,models=0)
    try:
        assert not subprocess.run(['git','diff','--cached','--name-only'],cwd=R,capture_output=True,text=True,check=True).stdout.strip(),'UNRELATED_STAGED_FILES'
        index=read(O/'OFFLINE_ARCHIVE_INDEX.json');records=R/'records/fast_stamped_v1354_20261119';records.mkdir(exist_ok=False)
        paths=[str(C.relative_to(R)),'CURRENT_EXPERIMENT.json','RESEARCH_STATUS.md','docs/FAST_STAMPED_V1354_REPORT.md']
        dump(records/'ARCHIVE_INDEX.json',index)
        for part in index['parts']:
            source=O/'offline_archive'/part['name'];assert sha(source)==part['sha256'] and part['bytes']<=32*1024**2
            os.link(source,records/part['name'])
        paths.append(str(records.relative_to(R)))
        subprocess.run(['git','add','--',*paths],cwd=R,check=True,capture_output=True,timeout=15)
        small=[O/name for name in ['ROUND_WINDOW.json','APPROVAL.json','LAUNCH.json','COMPLETION.json','FINALIZED.json','TASK_ACCOUNTING.json','REUSED_QUALIFICATIONS.json','CHANGED_BOUNDARY_QUALIFICATION.json','FULL_ENTRY_QUALIFICATION.json','BACKEND_QUALIFICATION.json','OUTPUT_SCOPE_QUALIFICATION.json','software/COMPLETION.json','software/INDEPENDENT_AUDIT.json']]
        subprocess.run(['git','add','-f','--',*[str(p.relative_to(R)) for p in small if p.exists()]],cwd=R,check=True,capture_output=True,timeout=15)
        subprocess.run(['git','diff','--cached','--check'],cwd=R,check=True,capture_output=True,timeout=10)
        subprocess.run(['git','commit','-m','Record bounded fast stamped controller comparison and verified evidence blocks'],cwd=R,check=True,capture_output=True,timeout=20)
        head=subprocess.run(['git','rev-parse','HEAD'],cwd=R,capture_output=True,text=True,check=True).stdout.strip();result['head']=head
        try:
            p=subprocess.run(['git','push','origin','main'],cwd=R,capture_output=True,text=True,timeout=30)
            result.update(push_returncode=p.returncode,push_output=re.sub(r'https://[^/@\s]+:[^/@\s]+@','https://<REDACTED>@',p.stdout+p.stderr))
        except subprocess.TimeoutExpired:result['push_error']='PUSH_TIMEOUT_30S'
        try:
            p=subprocess.run(['git','ls-remote','origin','refs/heads/main'],cwd=R,capture_output=True,text=True,timeout=5)
            result['remote_head']=p.stdout.strip().split()[0] if p.returncode==0 and p.stdout.strip() else None
            result['remote_verified']=result['remote_head']==head
        except subprocess.TimeoutExpired:result['verify_error']='READONLY_TIMEOUT_5S'
    except BaseException as exc:result['error']=repr(exc)
    dump(O/'SOURCE_SYNC_RESULT.json',dict(result,closed_unix=time.time(),raw_deleted=False))
    return 0 if result['remote_verified'] else 1


if __name__=='__main__':raise SystemExit(main())
