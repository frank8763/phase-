from common import R,C,S,load
def command(script,out):
 m=load('unchanged_Phase_isolation_command',R/'tools/isolate.py');cmd=m.command(script,writable=True);i=cmd.index('--bind');assert cmd[i+1:i+3]==[str(R/'runs'),str(R/'runs')];cmd[i]='--ro-bind';j=cmd.index('--chdir');cmd[j:j]=['--bind',str(out),str(out)]
 i=next(i for i in range(len(cmd)-1)if cmd[i:i+2]==['--tmpfs','/tmp']);cmd[i:i]=['--size',str(2*1024**2)]
 i=cmd.index(str(R/'runtime/mk-mini'))if str(R/'runtime/mk-mini')in cmd else cmd.index('--chdir')
 # Each worker has bounded scratch and no persistent compilation cache.
 j=cmd.index('--chdir');cmd[j:j]=['--size',str(2*1024**2),'--tmpfs','/dev/shm']
 j=cmd.index(str(R/'tools/isolate.py'))if str(R/'tools/isolate.py')in cmd else next(i for i,x in enumerate(cmd)if x.endswith('/envs/mk_mujoco/bin/python'))
 cmd[j:j]=['--setenv','HOME','/tmp','--setenv','TMPDIR','/tmp','--setenv','XDG_CACHE_HOME','/tmp/cache','--setenv','JAX_ENABLE_COMPILATION_CACHE','false','--setenv','TF_NUM_INTRAOP_THREADS','1','--setenv','TF_NUM_INTEROP_THREADS','1']
 assert cmd.count('--bind')==1 and '--unshare-all'in cmd;return cmd
