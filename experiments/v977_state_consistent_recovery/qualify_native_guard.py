"""Call the actual native entry and prove denial before physical lazy import."""
import importlib.abc
import json
import sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];C=Path(__file__).parent;O=R/'runs/v977_state_consistent_recovery'
attempted=[]
class NoModel(importlib.abc.MetaPathFinder):
    def find_spec(self,name,*args):
        if name.split('.')[0]in {'mujoco','torch','vehicle','physical','factory'}:
            attempted.append(name);raise AssertionError('MODEL_IMPORT_REACHED '+name)
sys.meta_path.insert(0,NoModel());sys.path.insert(0,str(C))
import native_worker
try:native_worker.engine.run({}, {}, 'SOURCE_ONLY_NO_PHYSICAL_FREEZE')
except PermissionError as error:
    passed=str(error)=='V977_NO_PHYSICAL_MODEL_AUTHORITY_USER_SELECTED_SOURCE_ONLY'and not attempted
    reason=str(error)
else:passed=False;reason='AUTHORITY_WAS_NOT_DENIED'
report=dict(passed=passed,reason=reason,actual_worker_source=str(Path(native_worker.__file__).relative_to(R)),
            actual_authority_source=native_worker.authorized.__code__.co_filename,
            physical_import_attempts=attempted,models=0,integrations=0,training=0)
(O/'NATIVE_AUTHORITY_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert passed
