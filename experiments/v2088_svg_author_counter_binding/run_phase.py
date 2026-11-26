"""Source-admitted Phase mount namespace, only this component actual is writable."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;O=R/'runs'/C.name
def main():
 assert os.sched_getaffinity(0)=={2}and(O/'PILOT_ADMISSION.json').is_file(),'SVG_INDEPENDENT_PHASE_NOT_ADMITTED'
 read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();a=read(O/'PILOT_ADMISSION.json');w=read(O/'PILOT_WINDOW.json');task=read(O/'PILOT_TASK.json');claim=read(O/'PILOT_ONCE_CLAIM.json')
 assert a['models_authorized']and a['independent_parallel_owner']and a['scope']=='SVG_CURRENT_ORIGINAL_VEHICLE_INTERFACE_COMPONENT'and a['assignment']==task
 assert a['source_freeze_sha256']==sha(O/'SOURCE_FREEZE.json')and a['pilot_entry_sha256']==sha(C/'pilot_entry.py')and Path('/proc',str(claim['owner_pid'])).exists()
 assert read(O/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 out=Path(task['output']);assert out==O/'actual'and out.is_dir()and not out.is_symlink()and not(out/'RESULT.json').exists()
 spec=importlib.util.spec_from_file_location('exact_original_Phase_mount_namespace',R/'tools/isolate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);cmd=m.command(C/'pilot_entry.py',writable=True);i=cmd.index('--bind');assert cmd[i+1:i+3]==[str(R/'runs'),str(R/'runs')];cmd[i]='--ro-bind';j=cmd.index('--chdir');cmd[j:j]=['--bind',str(out),str(out)];assert '--unshare-all'in cmd and cmd.count('--bind')==1
 raise SystemExit(subprocess.run(cmd,cwd=R).returncode)
if __name__=='__main__':main()
