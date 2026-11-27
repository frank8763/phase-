"""Prospective independent owner entry using the exact Phase mount namespace.

The global REVIEW file belongs to the concurrent frozen RPP owner. This entry
requires its own source-bound one-case authorization and writes only its OUT.
"""
from pathlib import Path
import importlib.util,json,os,subprocess,sys,time,hashlib
R=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent;SOURCE=R/'runs'/C.name;RID='priest_current_vehicle_component';O=SOURCE/'vehicle'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def namespace(script,output):
 p=R/'tools/isolate.py';spec=importlib.util.spec_from_file_location('unchanged_Phase_namespace',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 cmd=m.command(script,writable=True);i=cmd.index('--bind');assert cmd[i+1:i+3]==[str(R/'runs'),str(R/'runs')];cmd[i]='--ro-bind';j=cmd.index('--chdir');cmd[j:j]=['--bind',str(output),str(output)]
 # Phase only: original /home hiding, frozen runtime and conda binds retained.
 assert '--unshare-all'in cmd and cmd.count('--bind')==1 and '--tmpfs'in cmd
 return cmd
def main():
 assert os.sched_getaffinity(0)=={2}
 assert(O/'PILOT_ADMISSION.json').is_file(),'PRIEST_INDEPENDENT_PHASE_NOT_ADMITTED'
 a=read(O/'PILOT_ADMISSION.json');task=read(O/'PILOT_TASK.json');w=read(O/'PILOT_WINDOW.json');owner=read(O/'PILOT_ONCE_CLAIM.json')
 assert a['models_authorized']and a['independent_parallel_owner']and a['scope']=='PRIEST_CURRENT_VEHICLE_COMPONENT'and a['assignment']==task
 assert a['source_freeze_sha256']==sha(SOURCE/'SOURCE_FREEZE.json')and a['pilot_entry_sha256']==sha(C/'pilot_entry.py')
 assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==w['boot_id']and time.time()<w['absolute_deadline_unix']and time.monotonic()<w['hard_stop_monotonic']
 assert Path('/proc',str(owner['owner_pid'])).exists()and task['component_not_navigation']
 assert not(Path(task['output'])/'RESULT.json').exists()and read(SOURCE/'CURRENT_SOURCE_REMOTE_RECOVERY.json')['all_frozen_members_remote_chain_covered']
 out=Path(task['output']);assert out==O/'actual'and out.is_dir()and not out.is_symlink()
 cmd=namespace(C/'pilot_entry.py',out)
 raise SystemExit(subprocess.run(cmd,cwd=R).returncode)
if __name__=='__main__':main()
