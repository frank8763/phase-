"""Start the fixed new night, preserving every old root clock."""
from night_tools import *
import subprocess,fcntl

if __name__=='__main__':
 assert not(O/'DRIVER_STARTED.json').exists()and not(O/'LAUNCH_RECEIPT.json').exists()
 assert source_ok()and sha(R/'REVIEW_PENDING')==GUARD_SHA and remaining()>15000
 assert all(json.loads((O/n).read_text())['passed']for n in ['QUALIFICATION.json','ISOLATED_QUALIFICATION.json','SOFTWARE_ENTRY_QUALIFIED.json'])
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
 (O/'GUARD.bin').write_bytes((R/'REVIEW_PENDING').read_bytes());dump(O/'APPROVAL.json',dict(models_authorized=True,scope='fixed refresh main/repeat; conditional8 software recovery profiles only',user_instruction='检查，然后开启今天晚上的通宵实验',no_old_window_extension=True))
 current=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());current.update(status='RUNNING_V1148_OVERNIGHT',active_run=str(O.relative_to(R)),active_window=str((O/'ROUND_WINDOW.json').relative_to(R)),active_entrypoint=str((C/'campaign.py').relative_to(R)),next_physical_authorized=True);dump(R/'CURRENT_EXPERIMENT.json',current)
 with(O/'campaign.console').open('x')as log:p=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 receipt=dict(pid=p.pid,proc_start=Path('/proc',str(p.pid),'stat').read_text().split()[21],deadline_unix=json.loads((O/'ROUND_WINDOW.json').read_text())['absolute_deadline_unix'],offline_capable=True,detached=True);dump(O/'LAUNCH_RECEIPT.json',receipt)
 with(O/'watchdog.console').open('x')as log:watch=subprocess.Popen([sys.executable,'-B',str(C/'watchdog.py')],cwd=R,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 dump(O/'WATCHDOG_LAUNCH.json',dict(pid=watch.pid,proc_start=Path('/proc',str(watch.pid),'stat').read_text().split()[21]));print(encode(receipt))
