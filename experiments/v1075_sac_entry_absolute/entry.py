"""Absolute CLI entry only; unchanged V1074 scientific worker."""
import sys,runpy,importlib.abc,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];task=R/'runs/v1074_sac_native_control/TASK.json';assert task.is_file();sys.path.insert(0,str(R/'experiments/v1074_sac_native_control'));sys.argv=[str(R/'experiments/v1074_sac_native_control/worker.py'),str(task)]
if '--check-only'in sys.orig_argv:
 class NoPhysics(importlib.abc.MetaPathFinder):
  def find_spec(self,name,*args):
   if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy'}:raise AssertionError('FORBIDDEN_PHYSICS '+name)
 sys.meta_path.insert(0,NoPhysics());runpy.run_path(sys.argv[0],run_name='qualified_import');assert Path(sys.argv[1]).is_absolute();assert json.loads(task.read_text())in json.loads((R/'experiments/v1074_sac_native_control/TASKS.json').read_text());print(json.dumps(dict(passed=True,absolute_task_read=True,actual_isolated_cwd=str(Path.cwd()),all_worker_imports=True,models=0,integrations=0)),flush=True)
else:runpy.run_path(sys.argv[0],run_name='__main__')
