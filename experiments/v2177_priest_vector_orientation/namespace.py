"""Original Phase-only mounts, one scoped mathematical output writable."""
from context import R,load
from pathlib import Path

def command(script,output):
 p=load('C2177_original_Phase_isolation',R/'tools/isolate.py');cmd=p.command(Path(script),writable=True);i=cmd.index('--bind');assert cmd[i+1:i+3]==[str(R/'runs'),str(R/'runs')];cmd[i]='--ro-bind';j=cmd.index('--chdir');cmd[j:j]=['--bind',str(output),str(output)]
 assert '--unshare-all'in cmd and cmd.count('--bind')==1 and '--tmpfs'in cmd
 return cmd
