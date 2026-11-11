"""Single fresh-start claim, original root ceiling preserved."""
import fcntl,subprocess
from kernel import *
def main():
 assert not(O/'ROUND_WINDOW.json').exists();assert remaining_root()>1350
 assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
 for name in ['ENTRY_QUALIFICATION.json','CHAIN_QUALIFICATION.json','PRODUCTION_QUALIFICATION.json','REJECTION_QUALIFICATION.json','OPERATIONS_QUALIFICATION.json']:assert json.loads((O/name).read_text())['passed']
 assert all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items());lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN);now=time.time();tasks=json.loads((C/'PHYSICAL_TASKS.json').read_text());window=dict(started_unix=now,absolute_deadline_unix=HARD_END,hard_stop_monotonic=time.monotonic()+HARD_END-now,maximum_models=2,allowed_task_ids=[t['task_id']for t in tasks],no_historical_restore=True,old_windows_unchanged=True,temporary_budget_bytes=2*1024**3,user_authorization='2026-11-11开始解决第一步、继续；真实起点回归，沿今日20:30根截止，先完成已具备资格的WE主与条件重复，另两路线未资格不启动')
 with(O/'ROUND_WINDOW.json').open('x')as f:json.dump(window,f,indent=2)
 (O/'GUARD.bin').write_bytes((R/'REVIEW_PENDING').read_bytes());dump(O/'APPROVAL.json',dict(models_authorized=True,allowed_task_ids=window['allowed_task_ids'],absolute_deadline_unix=HARD_END))
 with(O/'driver.console').open('x')as log:p=subprocess.Popen([sys.executable,'-B',str(C/'driver.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 start=Path('/proc',str(p.pid),'stat').read_text().rsplit(')',1)[1].split()[19]
 with(O/'watchdog.console').open('x')as log:w=subprocess.Popen([sys.executable,'-B',str(C/'watchdog.py'),str(p.pid),start],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 dump(O/'START_RECEIPT.json',dict(driver_pid=p.pid,watchdog_pid=w.pid,pid_start=start,**window));cur=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());cur.update(status='RUNNING_FRESH_START_DEVELOPMENT',source_revision='V1056',active_run=str(O.relative_to(R)),active_entrypoint=str((C/'driver.py').relative_to(R)),active_window=window);dump(R/'CURRENT_EXPERIMENT.json',cur);print(json.dumps(dict(driver_pid=p.pid,watchdog_pid=w.pid,deadline=HARD_END)))
if __name__=='__main__':main()
