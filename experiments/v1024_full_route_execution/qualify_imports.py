import importlib.abc,importlib.util,json,sys,inspect
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];O=R/'runs/v1024_full_route_execution';sys.path[:0]=[str(C),str(R/'experiments/v1023_dense_input_route')]
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
import worker
factory=worker.load('v1024_actual_physical_import',R/'experiments/v1020_terminal_two_route_development/physical.py')
assert callable(factory.create_vehicle)and callable(factory.replay)
from input_route import construct
from certificate import audit
assert Path(inspect.getsourcefile(construct)).resolve()==R/'experiments/v1023_dense_input_route/input_route.py'
assert Path(inspect.getsourcefile(audit)).resolve()==R/'experiments/v1023_dense_input_route/certificate.py'
r=dict(passed=True,worker_source=str(Path(inspect.getsourcefile(worker)).relative_to(R)),actual_factory_import=True,exact_new_input_search_and_certificate=True,models=0,integrations=0)
(O/'IMPORT_QUALIFICATION.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
