"""Start only qualified, frozen two-task development; never reset root20:30."""
import fcntl,subprocess
from kernel import *
def main():
 assert not(O/'ROUND_WINDOW.json').exists();assert time.time()<HARD_END-1930
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 for name in ['SOURCE_INDEPENDENT_AUDIT.json','QUALIFICATION.json','EXECUTOR_QUALIFICATION.json','ENTRY_QUALIFICATION.json','HISTORY_RESTORE.json','REVERSE_QUALIFICATION.json']:assert json.loads((O/name).read_text())['passed']
 assert all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items());lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN);now=time.time();window=dict(started_unix=now,absolute_deadline_unix=HARD_END,hard_stop_monotonic=time.monotonic()+HARD_END-now,maximum_models=2,old_v1047_closed=True,old_deadlines_unchanged=True,temporary_budget_bytes=2*1024**3,user_authorization='2026-11-11下一步开始、继续；生产停车刷新资格全过后原任务主及成功重复；原20:30不变')
 with(O/'ROUND_WINDOW.json').open('x')as f:json.dump(window,f,indent=2)
 (O/'GUARD.bin').write_bytes((R/'REVIEW_PENDING').read_bytes());dump(O/'APPROVAL.json',dict(models_authorized=True,absolute_deadline_unix=HARD_END))
 with(O/'driver.console').open('x')as log:p=subprocess.Popen([sys.executable,'-B',str(C/'driver.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 start=Path('/proc',str(p.pid),'stat').read_text().rsplit(')',1)[1].split()[19]
 with(O/'watchdog.console').open('x')as log:w=subprocess.Popen([sys.executable,'-B',str(C/'watchdog.py'),str(p.pid),start],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 dump(O/'START_RECEIPT.json',dict(driver_pid=p.pid,watchdog_pid=w.pid,pid_start=start,**window));cur=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());cur.update(status='RUNNING_RETAINED_CORRIDOR_DEVELOPMENT',source_revision='V1053',active_run=str(O.relative_to(R)),active_entrypoint=str((C/'driver.py').relative_to(R)),active_window=window);dump(R/'CURRENT_EXPERIMENT.json',cur);print(json.dumps(dict(driver_pid=p.pid,watchdog_pid=w.pid,hard_deadline_unix=HARD_END)))
if __name__=='__main__':main()
