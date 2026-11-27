from common import R,load

def command(script,out):
 m=load('unchanged_Phase_isolation',R/'tools/isolate.py');cmd=m.command(script,writable=True);i=cmd.index('--bind');assert cmd[i+1:i+3]==[str(R/'runs'),str(R/'runs')];cmd[i]='--ro-bind'
 j=cmd.index('--chdir');cmd[j:j]=['--bind',str(out),str(out),'--setenv','HOME','/tmp','--setenv','TMPDIR','/tmp','--setenv','XDG_CACHE_HOME','/tmp/cache','--setenv','MPLCONFIGDIR','/tmp/mpl']
 # Keep original Stage-hidden Phase namespace and a single bounded write root.
 assert '--unshare-all'in cmd and cmd.count('--bind')==1;return cmd
