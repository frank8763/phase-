"""One new90min root and <=20min diagnostic stage, locked before model init."""
import fcntl,json,subprocess,sys,time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v995_sim_time_response';ROOT=R/'runs/sim_time_recovery_20261110'
sys.path.insert(0,str(C));from authority import sha,read
if __name__=='__main__':
    lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not(ROOT/'ROUND_WINDOW.json').exists()and not(O/'CAMPAIGN_CLAIM.json').exists()
    a=read(ROOT/'USER_AUTHORIZATION.json');assert a['user_instruction']=='开始'and a['maximum_root_s']==5400.
    assert read(C/'SOURCE_FREEZE.json')['final']and all(sha(R/p)==h for p,h in read(C/'SOURCE_FREEZE.json')['files'].items())
    for row in read(O/'RESTORE_RECEIPT.json')['files']:assert sha(R/row['path'])==row['sha256']
    assert sha(R/'REVIEW_PENDING')==sha(ROOT/'REVIEW_PENDING.before')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
    start=time.time();iso=lambda x:datetime.fromtimestamp(x,ZoneInfo('Asia/Shanghai')).isoformat()
    w=dict(started_unix=start,deadline_unix=start+5400.,started_iso=iso(start),deadline_iso=iso(start+5400.),source_freeze_sha256=sha(C/'SOURCE_FREEZE.json'),user_authorization_sha256=sha(ROOT/'USER_AUTHORIZATION.json'))
    for p,x in [(ROOT/'ROUND_WINDOW.json',w),(O/'ROUND_WINDOW.json',dict(started_unix=start,deadline_unix=start+1200.,started_iso=iso(start),deadline_iso=iso(start+1200.)))]:
        with p.open('x')as f:json.dump(x,f,indent=2)
    fcntl.flock(lock,fcntl.LOCK_UN)
    with(O/'campaign.console').open('x')as stream:
        p=subprocess.Popen(['timeout','--signal=TERM','--kill-after=8s','1230',sys.executable,'-B',str(C/'campaign.py')],cwd=R,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
    (O/'DRIVER.json').write_text(json.dumps(dict(pid=p.pid,root=w,stage_deadline_unix=start+1200.),indent=2)+'\n')
    print(json.dumps(dict(pid=p.pid,started_iso=iso(start),root_deadline_iso=iso(start+5400.),diagnostic_deadline_iso=iso(start+1200.),max_diagnostic_tasks=4)))
