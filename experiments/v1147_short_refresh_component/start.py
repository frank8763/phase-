"""Lock one NEW600s window only after both zero-model qualifications pass."""
from common_short import *
import fcntl,subprocess

if __name__=='__main__':
 assert not(O/'ROUND_WINDOW.json').exists()and not(O/'DRIVER_STARTED.json').exists()
 assert source_ok()and sha(R/'REVIEW_PENDING')==GUARD_SHA
 assert all(json.loads((O/n).read_text())['passed']for n in ['QUALIFICATION.json','ISOLATED_QUALIFICATION.json'])
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
 now=time.time();mono=time.monotonic();w=dict(started_unix=now,started_monotonic=mono,absolute_deadline_unix=now+600,hard_stop_monotonic=mono+600,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),maximum_seconds=600,maximum_main_attempts=1,automatic_repeat=False,old_2100_window_closed_unchanged=True)
 dump(O/'ROUND_WINDOW.json',w);(O/'GUARD.bin').write_bytes((R/'REVIEW_PENDING').read_bytes());dump(O/'APPROVAL.json',dict(models_authorized=True,user_instruction='下一步开始测试；短时间的',scope='canonical history reconstruction then original8+complete2200 real refresh component; one attempt',maximum_wall_s=600,old_window_not_reused=True))
 cur=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());cur.update(status='RUNNING_V1147_SHORT_REFRESH',active_run=str(O.relative_to(R)),active_window=str((O/'ROUND_WINDOW.json').relative_to(R)),active_entrypoint=str((C/'campaign.py').relative_to(R)),next_physical_authorized=True);dump(R/'CURRENT_EXPERIMENT.json',cur)
 with(O/'campaign.console').open('x')as log:p=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 receipt=dict(pid=p.pid,proc_start=Path('/proc',str(p.pid),'stat').read_text().split()[21],deadline_unix=now+600,detached=True,offline_capable=True,maximum_main_attempts=1);dump(O/'LAUNCH_RECEIPT.json',receipt)
 with(O/'watchdog.console').open('x')as log:watch=subprocess.Popen([sys.executable,'-B',str(C/'watchdog.py')],cwd=R,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 dump(O/'WATCHDOG_LAUNCH.json',dict(pid=watch.pid,proc_start=Path('/proc',str(watch.pid),'stat').read_text().split()[21]));print(encode(receipt))
