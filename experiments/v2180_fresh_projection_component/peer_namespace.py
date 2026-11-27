"""Original Phase-only readonly namespace with bounded private scratch."""
from peer_guard import R,C
import importlib.util

def command(script):
 spec=importlib.util.spec_from_file_location('CP_original_Phase_readonly',R/'tools/isolate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);cmd=m.command(script,writable=False)
 i=next(i for i in range(len(cmd)-1)if cmd[i:i+2]==['--tmpfs','/tmp']);cmd[i:i]=['--size',str(2*1024**2)];j=cmd.index('--chdir');cmd[j:j]=['--size',str(2*1024**2),'--tmpfs','/dev/shm','--setenv','HOME','/tmp','--setenv','TMPDIR','/tmp','--setenv','XDG_CACHE_HOME','/tmp/cache']
 assert '--unshare-all'in cmd and '--bind'not in cmd;return cmd
