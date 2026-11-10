"""Bind the exact frozen V990 memory/dispatch implementation after history."""
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
IMPLEMENTATION=R/'experiments/v990_coordinated_actuation/actuation_binding.py'
spec=importlib.util.spec_from_file_location('v991_exact_v990_binding',IMPLEMENTATION)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
SOURCE=module.SOURCE
OLD=module.OLD
control=module.control
bind_restored=module.bind_restored
