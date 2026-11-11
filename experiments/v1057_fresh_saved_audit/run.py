"""Zero-model supplemental readback; frozen V1056 audit/error remains unchanged."""
import importlib.abc,sys,json
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];sys.path.insert(0,str(R/'experiments/v1056_fresh_route_regression'))
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','torch','physical','vehicle','rclpy'}:raise AssertionError('ZERO_MODEL '+name)
sys.meta_path.insert(0,NoModel())
from kernel import load,dump,O,sha
module=load('v1057_independent_saved_audit',C/'audit_saved.py');task=json.loads((R/'experiments/v1056_fresh_route_regression/PHYSICAL_TASKS.json').read_text())[0];original=sha(R/'experiments/v1056_fresh_route_regression/audit.py');result=module.audit_native(task);assert sha(R/'experiments/v1056_fresh_route_regression/audit.py')==original;dump(O/'SUPPLEMENTAL_MAIN_AUDIT.json',dict(result,original_batch_error_kept=True,original_batch_not_upgraded=True,model_initializations=0));print(json.dumps(result))
