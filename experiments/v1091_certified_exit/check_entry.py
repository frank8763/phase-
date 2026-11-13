"""Import the exact worker/auditor inside isolation with models forbidden."""
import sys,json,importlib.abc,ast,importlib.util
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1091_certified_exit'
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','physical','vehicle','torch','rclpy'}:raise AssertionError('ENTRY_MODEL_FORBIDDEN '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C));import worker
for p in C.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
task=json.loads((O/'TASK.json').read_text());out=Path(task['output'])
assert out==R/'runs/v858_nav2_verified/v1091/exit_saved_we'and not out.exists()
prior=json.loads((R/'experiments/v1090_active_corridor/TASKS.json').read_text())[0]
assert all(task[k]==prior[k]for k in ['case_id','seed','phase','dynamic','goal_xy','start_xy','start_yaw'])
f=worker.factory(O)
try:
    f.create_vehicle(out/'physics',task)
    raise RuntimeError('DISABLED_ENTRY_ENTERED_MODEL')
except AssertionError as e:assert str(e)=='PHYSICAL_MODELS_DISABLED_FOR_PREPARATION'
s=importlib.util.spec_from_file_location('installed_exit_audit',C/'audit.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
assert callable(m.audit)and callable(worker.stop.after_rejection)
assert json.loads((O/'QUALIFICATION.json').read_text())['passed']
print(json.dumps(dict(passed=True,models=0,integrations=0,real_worker_and_auditor_import=True,exact_WE_task=True,disabled_factory_rejected_before_models=True,output_root_bound=True)),flush=True)
