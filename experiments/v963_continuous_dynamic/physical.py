"""Exact V959 physical adapter and sensor binding, no additional model change."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v963_qualified_physical',ROOT/'experiments/v959_hold_response18/physical.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
create_vehicle=module.create_vehicle
replay=module.replay
