"""New90min exactly one route; old night/08:00 authority never reopened."""
import fcntl,hashlib,json,subprocess,sys,time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v974_daytime_binding_gate'
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from authority import sha,SCOPE
from handshake import verify_sources
assert not(O/'AUTHORIZATION.json').exists()and not(O/'CAMPAIGN_CLAIM.json').exists();assert json.loads((C/'SOURCE_FREEZE.json').read_text())['final']
verify_sources(R,C/'SOURCE_FREEZE.json')
for name in ['ZERO_MODEL_QUALIFICATION.json','FULL_PLANNER_FLOW_QUALIFICATION.json']:assert json.loads((O/name).read_text())['passed']
lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
start=time.time();deadline=start+5400.;iso=lambda v:datetime.fromtimestamp(v,ZoneInfo('Asia/Shanghai')).isoformat()
a=dict(scope=SCOPE,models_authorized=True,user_instruction='现在是第二天了，一步一步的实验做着走吧；等晚上再开通宵的',interpretation='One daytime corrected-binding original WE full dynamic task only; max90min and nav180s+2stop; no automatic repeat/regression/24/night.',started_unix=start,deadline_unix=deadline,started_iso=iso(start),deadline_iso=iso(deadline),source_freeze_sha256=sha(C/'SOURCE_FREEZE.json'),max_navigation=1,first_failure_stops=True,training=0,hardware=0,new24=0)
for name,value in [('AUTHORIZATION.json',a),('ROUND_WINDOW.json',dict(started_unix=start,deadline_unix=deadline,started_iso=iso(start),deadline_iso=iso(deadline)))]:
 with(O/name).open('x')as f:json.dump(value,f,indent=2)
fcntl.flock(lock,fcntl.LOCK_UN)
with(O/'campaign.console').open('x')as f:job=subprocess.Popen(['timeout','--signal=TERM','--kill-after=5s','6000',sys.executable,'-B',str(C/'campaign.py')],cwd=R,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
(O/'DRIVER.json').write_text(json.dumps(dict(pid=job.pid,started_iso=iso(start),deadline_iso=iso(deadline)),indent=2)+'\n');print(json.dumps(dict(pid=job.pid,started=iso(start),deadline=iso(deadline),max_navigation=1)))
