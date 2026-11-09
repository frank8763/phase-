"""Lock current90min and the separately preregistered conditional08:00 chain."""
import fcntl,hashlib,json,subprocess,sys,time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v968_rpp_closed_loop_night'
sys.path[:0]=[str(C),str(R/'experiments/v862_ready_static')]
from handshake import verify_sources
from authority import SCOPE
assert not(O/'AUTHORIZATION.json').exists()and not(O/'CAMPAIGN_CLAIM.json').exists(),'NO_RELAUNCH'
verify_sources(R,C/'SOURCE_FREEZE.json')
assert json.loads((C/'SOURCE_FREEZE.json').read_text())['final']is True
for name in ['ZERO_MODEL_QUALIFICATION.json','FULL_STARTUP_QUALIFICATION.json','FULL_COMPONENT_SOFTWARE_QUALIFICATION.json']:assert json.loads((O/name).read_text())['passed']
assert hashlib.sha256((R/'REVIEW_PENDING').read_bytes()).hexdigest()=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
start=time.time();plan=json.loads((C/'NIGHT_PLAN.json').read_text());deadline=plan['deadline_unix'];assert start<deadline<start+43200.
iso=lambda v:datetime.fromtimestamp(v,ZoneInfo('Asia/Shanghai')).isoformat()
a=dict(scope=SCOPE,models_authorized=True,user_instruction='继续开启通宵的；新独立实际RPP闭环交接→WE主重复→三路线→原锁定24及固定重复，08:00停止',
    started_unix=start,deadline_unix=deadline,started_iso=iso(start),deadline_iso=iso(deadline),source_freeze_sha256=hashlib.sha256((C/'SOURCE_FREEZE.json').read_bytes()).hexdigest(),
    max_navigation=33,max_closed_loop_component=1,first_safety_or_evidence_failure_stops=True,development_first_functional_failure_stops=True,confirmation_second_functional_failure_stops=True,old_windows_unchanged=True,training=0,hardware=0,conditional_fixed_confirmation=24)
for name,data in [('ROUND_WINDOW.json',dict(started_unix=start,deadline_unix=deadline,started_iso=iso(start),deadline_iso=iso(deadline))),('AUTHORIZATION.json',a)]:
 with(O/name).open('x')as f:json.dump(data,f,indent=2)
fcntl.flock(lock,fcntl.LOCK_UN)
with(O/'campaign.console').open('x')as f:
 job=subprocess.Popen(['timeout','--signal=TERM','--kill-after=5s',str(int(max(deadline,plan['deadline_unix'])-time.time()+600)),sys.executable,'-B',str(C/'campaign.py')],cwd=R,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
with(O/'DRIVER.json').open('x')as f:json.dump(dict(pid=job.pid,at=time.time(),current_deadline_unix=deadline,fixed_night_deadline_unix=plan['deadline_unix']),f)
print(json.dumps(dict(pid=job.pid,new_absolute_night_deadline=iso(deadline),fixed_night_deadline=plan['deadline_iso']),indent=2))
