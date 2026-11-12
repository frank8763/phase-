"""Exactly one new 90-minute root, locked before first model initialization."""
import os,sys,subprocess,json,fcntl,time
from pathlib import Path
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from resource_policy import apply
RESOURCE=apply()
from authority import R,O,sha
assert not(O/'ROUND_WINDOW.json').exists(),'WINDOW_ALREADY_STARTED'
auth=json.loads((O/'AUTHORIZATION.json').read_text());assert auth['window_duration_s']==5400 and not auth['confirmation24_authorized'];assert json.loads((O/'QUALIFICATION.json').read_text())['passed'];assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66';assert all(sha(R/p)==h for p,h in json.loads((C/'SOURCE_FREEZE.json').read_text())['files'].items());lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN);tasks=json.loads((C/'TASKS.json').read_text());assert len(tasks)==9 and all(t['kind']in ['t0','main','repeat']for t in tasks)
wall=time.time();mono=time.monotonic();window=dict(started_unix=wall,started_monotonic=mono,absolute_deadline_unix=wall+5400,hard_stop_monotonic=mono+5400,duration_s=5400,allowed_task_ids=[t['task_id']for t in tasks],source_head=subprocess.run(['git','rev-parse','HEAD'],cwd=R,capture_output=True,text=True,check=True).stdout.strip(),resource_policy=RESOURCE,old_windows_unchanged=True,confirmation24_authorized=False)
with(O/'ROUND_WINDOW.json').open('x')as f:json.dump(window,f,indent=2)
(O/'GUARD.bin').write_bytes((R/'REVIEW_PENDING').read_bytes());(O/'APPROVAL.json').write_text(json.dumps(dict(models_authorized=True,allowed_task_ids=window['allowed_task_ids'],absolute_deadline_unix=window['absolute_deadline_unix']))+'\n')
with(O/'driver.console').open('x')as log:p=subprocess.Popen([sys.executable,'-B',str(C/'driver.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
start=Path('/proc',str(p.pid),'stat').read_text().rsplit(')',1)[1].split()[19]
with(O/'watchdog.console').open('x')as log:w=subprocess.Popen([sys.executable,'-B',str(C/'watchdog.py'),str(p.pid),start],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
receipt=dict(driver_pid=p.pid,pid_start=start,watchdog_pid=w.pid,**window);(O/'START_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');cur=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());cur.update(status='RUNNING_V1067_THREE_ROUTE',source_revision='V1067_CAUSAL_REPLAN_BRAKE_RESERVE',active_run=str(O.relative_to(R)),active_entrypoint=str((C/'driver.py').relative_to(R)),active_window=window,execution_window_closed=False,report='docs/RPCCR_CAUSAL_RECOVERY_V1067_REPORT.md',protocol=str((C/'PROTOCOL.md').relative_to(R)),decision_freeze=str((C/'SOURCE_FREEZE.json').relative_to(R)));(R/'CURRENT_EXPERIMENT.json').write_text(json.dumps(cur,ensure_ascii=False,indent=2)+'\n');print(json.dumps(receipt))
