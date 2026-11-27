"""Original Phase isolation, only this mathematical runtime output writable."""
import importlib.util,os,subprocess
from context import R,C,S,require_admission
def main():
    require_admission()
    path=R/'tools/isolate.py';spec=importlib.util.spec_from_file_location('v2184_original_Phase_namespace',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    cmd=m.command(C/'entry.py',writable=True);i=cmd.index('--bind');assert cmd[i+1:i+3]==[str(R/'runs'),str(R/'runs')];cmd[i]='--ro-bind'
    j=cmd.index('--chdir');cmd[j:j]=['--bind',str(S/'RUNTIME'),str(S/'RUNTIME')]
    for i in range(len(cmd)-2):
        if cmd[i:i+2]==['--setenv','MUJOCO_GL']:cmd[i+2]='osmesa'
    assert cmd.count('--bind')==1 and '--unshare-all'in cmd
    return subprocess.run(cmd,cwd=R).returncode
if __name__=='__main__':raise SystemExit(main())
