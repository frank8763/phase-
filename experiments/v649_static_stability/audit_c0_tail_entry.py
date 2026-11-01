"""Namespace entry only; execute the immutable tail audit with its frozen core imports."""
import os,sys,runpy
from pathlib import Path
repo=Path(os.environ['PHASE_REPO'])
sys.path.insert(0,str(repo/'experiments/v680_dynamic_later_stop_reserve'))
runpy.run_path(str(repo/'experiments/v649_static_stability/audit_later_stop_certificate_geometry.py'),run_name='__main__')
