"""Only one finite mathematical owner after immutable source transport."""
from context import R,C,ROOT,O,put
from pathlib import Path
from owner import fresh
import fcntl,subprocess,os,json
assert os.sched_getaffinity(0)=={5}
f=(ROOT/'launch.lock').open();fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
files,handles=fresh()
assert not(ROOT/'LAUNCH_ONCE.json').exists()
with(ROOT/'LAUNCH_ONCE.json').open('x')as g:g.write('{"once":true,"models":0}\n')
for h in handles:h.close()
with(ROOT/'owner.console').open('xb')as log:
 p=subprocess.Popen(['taskset','-c','5','nice','-n','19','ionice','-c','3','/usr/bin/python3','-B',str(C/'owner.py')],cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 i=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=Path('/proc',str(p.pid),'stat').read_text().split(') ',1)[1].split()[19],boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip());put(ROOT/'LAUNCH_IDENTITY.json',i)
print(json.dumps(i))
