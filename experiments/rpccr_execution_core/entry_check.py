"""Production isolated import and table contract with model imports forbidden."""
import sys,importlib.abc,json
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(Path(__file__).resolve().parent));import native_worker as w
assert len(sys.argv)==2 and Path(sys.argv[1]).is_absolute();task,O,cfg,out=w.entry(sys.argv[1]);f=w.factory(O);assert callable(f.create_vehicle)and callable(f.replay);print(json.dumps(dict(passed=True,isolated_cwd=str(Path.cwd()),all_production_imports=True,absolute_task=True,models=0,integrations=0)))
