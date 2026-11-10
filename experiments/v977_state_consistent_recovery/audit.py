"""Preserve all native/source/control audits, select the new reference auditor."""
import importlib.util
import sys
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1]
sys.path.insert(0,str(C))
import corridor_audit
spec=importlib.util.spec_from_file_location('v977_preserved_native_audits',R/'experiments/v974_daytime_binding_gate/audit.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
base.base.C=C

def audit(task):
    assert Path(corridor_audit.__file__).resolve()==C/'corridor_audit.py','WRONG_CURVE_AUDITOR'
    return base.audit(task)
