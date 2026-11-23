"""Single passive dependency wait, then one exact nonmodel restore; no chat wakeup."""
from pathlib import Path
import json,os,subprocess,sys,time
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;D=R/'runs'/C.name
read=lambda p:json.loads(p.read_text())
def main():
 os.sched_setaffinity(0,{5});start=time.monotonic();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();p=R/'runs/v1769_overnight_phase_campaign/NS_RELAY_RESULT.json'
 with(D/'AFTER_NS_ONCE_CLAIM.json').open('x')as f:json.dump(dict(pid=os.getpid(),unix=time.time()),f)
 while not p.exists():
  assert time.monotonic()<start+10800 and time.time()+1300<read(R/'runs/v1769_overnight_phase_campaign/AUTHORIZATION.json')['absolute_stop_unix']and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==boot
  time.sleep(1)
 assert read(p)['closed']and read(p)['passed'],'NS_RELAY_NOT_SAFE_CLOSED'
 answer=subprocess.run([sys.executable,str(C/'restore.py')],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),timeout=1210)
 (D/'AFTER_NS_EXIT.json').write_text(json.dumps(dict(returncode=answer.returncode,wall_s=time.monotonic()-start,models=0))+'\n');return answer.returncode
if __name__=='__main__':raise SystemExit(main())
