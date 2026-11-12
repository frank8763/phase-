"""Real sandbox CLI/import qualification; every model import is forbidden."""
import sys,importlib.abc,json
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODELS '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(Path(__file__).resolve().parent));import worker
assert len(sys.argv)==2 and Path(sys.argv[1]).is_absolute();task=json.loads(Path(sys.argv[1]).read_text());worker.contracts(task);f=worker.factory();assert callable(f.create_vehicle)and callable(f.replay);print(json.dumps(dict(passed=True,actual_cwd=str(Path.cwd()),absolute_task=True,all_worker_imports=True,factory_binding_imported_without_model=True,models=0,integrations=0)))
