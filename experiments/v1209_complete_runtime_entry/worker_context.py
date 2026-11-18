"""Namespace-only binding of the unchanged V1204 execution context."""
from pathlib import Path
import importlib.util
import sys
_here=Path(__file__).resolve().parent
_repo=_here.parents[1]
_spec=importlib.util.spec_from_file_location('v1209_unchanged_context',_repo/'experiments/v1204_goal_audit_worker/worker_context.py')
_context=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=_context;_spec.loader.exec_module(_context)
_context.C=_here;_context.O=_repo/'runs'/_here.name;_context.RAW=_repo/'runs/v858_nav2_verified/v1209'
for _key,_value in vars(_context).items():
    if not _key.startswith('_'):globals()[_key]=_value
