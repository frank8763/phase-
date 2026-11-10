"""Exact frozen V993 science; only the external execution clock changes."""
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'experiments/v993_steering_transient_diagnosis/actuation_binding.py'
s=importlib.util.spec_from_file_location('v995_exact_original_actuation_binding',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
SOURCE=m.SOURCE
bind_restored=m.bind_restored
