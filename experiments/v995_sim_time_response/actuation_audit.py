"""Exact old science reconstruction, explicit new setup arrays; no physics."""
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'experiments/v993_steering_transient_diagnosis/actuation_audit.py'
s=importlib.util.spec_from_file_location('v995_original_actuation_audit',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
check=m.check
