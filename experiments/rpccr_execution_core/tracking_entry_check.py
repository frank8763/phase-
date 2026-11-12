"""Production isolated imports and configured command contract, no physical model."""
import sys,importlib.abc,json,ast
from pathlib import Path
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(Path(__file__).resolve().parent));import tracking_worker as w
assert len(sys.argv)==2 and Path(sys.argv[1]).is_absolute();task,O,cfg,out=w.entry(sys.argv[1]);f=w.factory(O);assert callable(f.create_vehicle)and callable(f.replay)
assert cfg['worker']=='tracking_worker.py'and cfg['audit']=='tracking_audit.py'and cfg['audit_timeout_s']==300
assert task['historical_prefix_native']==18074 and task['new_native_limit']==4400 and task['stop_native']==2200
for n in ['path_tracking.py','tracking_worker.py','tracking_audit.py','configured_campaign.py','tracking_entry_check.py']:ast.parse((w.CORE/n).read_text())
# Inspect own audit import in the production namespace without running audit.
import tracking_audit
assert callable(tracking_audit.audit)
print(json.dumps(dict(passed=True,isolated_cwd=str(Path.cwd()),all_production_imports=True,absolute_task=True,models=0,integrations=0)))
