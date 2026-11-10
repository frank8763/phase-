"""Lock one new90minute absolute model deadline, then detached bounded campaign."""
import fcntl,json,subprocess,sys,time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v979_state_recovery_physical'
sys.path.insert(0,str(C));from authority import sha,SCOPE
from handshake import verify_sources
assert not(O/'AUTHORIZATION.json').exists()and not(O/'CAMPAIGN_CLAIM.json').exists()
assert json.loads((C/'SOURCE_FREEZE.json').read_text())['final'];verify_sources(R,C/'SOURCE_FREEZE.json')
lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
start=time.time();deadline=start+5400.;iso=lambda v:datetime.fromtimestamp(v,ZoneInfo('Asia/Shanghai')).isoformat()
auth=dict(scope=SCOPE,models_authorized=True,started_unix=start,deadline_unix=deadline,started_iso=iso(start),deadline_iso=iso(deadline),
          source_freeze_sha256=sha(C/'SOURCE_FREEZE.json'),user_instruction='修好了吗？可以开始进行实验了吗？如果可以，就抓紧时间开始',
          scope_interpretation='New90min: two original saved-state physical recovery components, both pass then original WE main and conditional same-version full repeat; first failure stops, no overnight/24/training/robot.',
          max_model_tasks=4,training=0,hardware=0,new24=0)
for name,value in [('AUTHORIZATION.json',auth),('ROUND_WINDOW.json',dict(started_unix=start,deadline_unix=deadline,started_iso=iso(start),deadline_iso=iso(deadline)))]:
    with(O/name).open('x')as stream:json.dump(value,stream,indent=2,ensure_ascii=False)
fcntl.flock(lock,fcntl.LOCK_UN)
with(O/'campaign.console').open('x')as stream:
    job=subprocess.Popen(['timeout','--signal=TERM','--kill-after=8s','6000',sys.executable,'-B',str(C/'campaign.py')],cwd=R,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
(O/'DRIVER.json').write_text(json.dumps(dict(pid=job.pid,started_iso=iso(start),deadline_iso=iso(deadline)),indent=2)+'\n')
print(json.dumps(dict(pid=job.pid,started=iso(start),deadline=iso(deadline),max_model_tasks=4)))
