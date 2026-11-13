"""Freeze authority exactly once immediately before background launch."""
import sys,json,time,subprocess,fcntl,os
from common import C,R,O,dump,sha,source_ok,used,GUARD_SHA
def main():
 assert not(O/'ROUND_WINDOW.json').exists(),'NO_WINDOW_RESET'
 assert source_ok()and sha(R/'REVIEW_PENDING')==GUARD_SHA
 assert all(json.loads((O/n).read_text())['passed']for n in ['PREPARATION.json','ENTRY_QUALIFICATION.json'])
 assert used()+128*1024**2<=2*1024**3,'TEMPORARY2GIB_CAP'
 lock=(R/'runs/v648_static_unknown/execution.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
 guard=(R/'REVIEW_PENDING').read_bytes();(O/'GUARD.bin').write_bytes(guard)
 begun=time.time();mono=time.monotonic();w=dict(started_unix=begun,absolute_deadline_unix=begun+5400,hard_stop_monotonic=mono+5400,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),duration_s=5400,maximum_vehicle_attempts=2,maximum_scheduled_actual_native=15000,maximum_failure_tail_native=2200,private_mujoco_native=0,training_updates=0,old_windows_closed=True)
 with(O/'ROUND_WINDOW.json').open('x')as f:json.dump(w,f,indent=2)
 dump(O/'APPROVAL.json',dict(models_authorized=True,user_request='2026-11-13 开始实验吧；继续',scope='two fixed parked steering components',first_failure_stop=True))
 current=json.loads((R/'CURRENT_EXPERIMENT.json').read_text());current.update(status='RUNNING_V1112_COMPONENT',active_run=str(O.relative_to(R)),active_window=str((O/'ROUND_WINDOW.json').relative_to(R)),active_entrypoint=str((C/'campaign.py').relative_to(R)),next_physical_authorized=True);dump(R/'CURRENT_EXPERIMENT.json',current)
 with(R/'RESEARCH_STATUS.md').open('a')as f:f.write('\n- 用户明确开始并继续，V1112新独立最多90分钟：两个固定NS静态t0停车调轮—前进组件，原V1111模型/控制与原物理安全门保持；15000预定实际/首失败2200原尾及全部重放，首失败停，不自动整路/三路线/24。全部入口零模型通过，源和任务事前冻结；CPU2低优先软件渲染，协议'+str((C/'PROTOCOL.md').relative_to(R))+'。\n')
 with(O/'campaign.console').open('x')as log:p=subprocess.Popen([sys.executable,'-B',str(C/'campaign.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 receipt=dict(pid=p.pid,starttime=Path('/proc',str(p.pid),'stat').read_text().split()[21],**w);dump(O/'LAUNCH.json',receipt)
 with(O/'watchdog.console').open('x')as log:watch=subprocess.Popen([sys.executable,'-B',str(C/'watchdog.py'),str(O)],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 dump(O/'WATCHDOG_LAUNCH.json',dict(pid=watch.pid));print(json.dumps(receipt))
from pathlib import Path
if __name__=='__main__':main()
