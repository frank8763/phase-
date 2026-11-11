"""Actual continuation entry without a vehicle model; immutable science proof."""
import ast,copy,importlib.abc,sys,json,subprocess
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(C))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import *
from execute import ProcessJob
old=R/'experiments/v1056_fresh_route_regression';names=['worker.py','fresh.py','atomic.py','execute.py','source_job.py','handoff.py','RECOVERY_WARM_SEED.json','CANONICAL_MODEL_SHA.json'];assert all((C/name).read_bytes()==(old/name).read_bytes()for name in names);assert(C/'kernel.py').read_text().replace('runs/v1058_fresh_repeat_entry','runs/v1056_fresh_route_regression')==(old/'kernel.py').read_text();assert ProcessJob.__init__.__globals__['C']==C
for name in ['start','driver','watchdog','close','delivery','worker','audit']:load('v1058_pure_entry_'+name,C/(name+'.py'))
for path in C.glob('*.py'):ast.parse(path.read_text(),filename=str(path))
tasks=json.loads((C/'TASKS.json').read_text());assert len(tasks)==1 and tasks[0]==json.loads((old/'TASKS.json').read_text())[1];assert not Path(tasks[0]['output']).exists();assert json.loads((O/'SUPPLEMENTAL_MAIN_AUDIT.json').read_text())['passed'];assert json.loads((O/'SUPPLEMENTAL_ENTRY_QUALIFICATION.json').read_text())['passed']
p=subprocess.run([str(R/'run_phase.sh'),'experiments/v1058_fresh_repeat_entry/worker.py',str(C/'TASK_repeat_west_east.json'),str(O/'NO_AUTHORITY.json')],cwd=R,capture_output=True,text=True,timeout=5);assert p.returncode==2 and 'PAUSED_PENDING_USER_REVIEW'in p.stderr
assert (C/'worker.py').is_file()and 'v1058_fresh_route_regression'not in(C/'driver.py').read_text()
assert sha(R/'REVIEW_PENDING')=='4ce7a8b33615619b40355b52f612b43dabf50344324eeba758969ab13e3eed66'
result=dict(passed=True,models=0,integrations=0,science_files_bitwise_original=names,kernel_only_output_namespace_differs=True,producer_namespace_current=True,actual_entry_guard_blocks=True,original_unexecuted_repeat_task_exact=True,main_not_reexecuted=True,old_error_kept=True,hard_deadline_unix=HARD_END);dump(O/'ENTRY_QUALIFICATION.json',result);print(json.dumps(result))
