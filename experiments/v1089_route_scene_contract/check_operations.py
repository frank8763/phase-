"""Import actual t0, audit and finalizer entrypoints inside real isolation."""
import sys,importlib.abc,runpy,json
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
class NoModel(importlib.abc.MetaPathFinder):
 def find_spec(self,name,*args):
  if name.split('.')[0]in {'mujoco','physical','vehicle','rclpy','torch'}:raise AssertionError('NO_MODEL_OPERATIONS '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
for name in ['t0.py','audit.py','finalize.py','campaign.py','watchdog.py']:
 runpy.run_path(str(C/name),run_name='isolated_operations_'+name.replace('.','_'))
answer=dict(passed=True,actual_t0_audit_finalizer_campaign_watchdog_imported_in_isolation=True,models=0,integrations=0)
(R/'runs/v1089_route_scene_contract/ISOLATED_OPERATIONS.json').write_text(json.dumps(answer,indent=2)+'\n');print(json.dumps(answer),flush=True)
