"""One root to the user's fixed20:30, detached driver plus no-restart watchdog."""
import fcntl,subprocess,sys
from kernel import *

def main():
 assert not(O/'ROUND_WINDOW.json').exists(),'NO_ROOT_RESET';assert remaining_root()>1800;assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';assert all(json.loads((O/n).read_text())['passed']for n in ['PREPARATION.json','QUALIFICATION.json','HISTORY_RESTORE.json']);freeze=json.loads((C/'SOURCE_FREEZE.json').read_text());assert all(sha(R/p)==h for p,h in freeze['files'].items());lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
 now=time.time();window=dict(started_unix=now,absolute_deadline_unix=HARD_END,hard_stop_monotonic=time.monotonic()+HARD_END-now,user_authorization='2026-11-11 这个继续推进；接力实验到今天晚上八点半；自行合理安排跑满时间',old_windows_unchanged=True,maximum_models=5,software_configurations=16,maximum_source_job_s=2400,temporary_budget_bytes=2*1024**3)
 with(O/'ROUND_WINDOW.json').open('x')as f:json.dump(window,f,indent=2)
 (O/'GUARD.bin').write_bytes((R/'REVIEW_PENDING').read_bytes());dump(O/'APPROVAL.json',dict(models_authorized=True,absolute_deadline_unix=HARD_END,frozen_source_sha256=sha(C/'SOURCE_FREEZE.json')))
 with(O/'driver.console').open('x')as log:p=subprocess.Popen([sys.executable,'-B',str(C/'driver.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 start=Path('/proc',str(p.pid),'stat').read_text().rsplit(')',1)[1].split()[19]
 with(O/'watchdog.console').open('x')as log:w=subprocess.Popen([sys.executable,'-B',str(C/'watchdog.py'),str(p.pid),start],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 dump(O/'START_RECEIPT.json',dict(driver_pid=p.pid,watchdog_pid=w.pid,pid_start=start,**window));cur=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());cur.update(status='RUNNING_FIXED_OFFLINE_RELAY',source_revision='V1047_RESERVED_STOP_TIME_SEARCH',active_entrypoint='experiments/v1047_day_relay/driver.py',active_run='runs/v1047_day_relay_20261111',active_window=window);dump(R/'CURRENT_EXPERIMENT.json',cur);print(json.dumps(dict(driver_pid=p.pid,watchdog_pid=w.pid,absolute_deadline_unix=HARD_END)))
if __name__=='__main__':main()
