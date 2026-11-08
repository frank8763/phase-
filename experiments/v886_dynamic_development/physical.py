"""Lazy, source-exact V882 dynamic model/replay adapter; no model on import."""
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v886_original_dynamic_adapter',R/'experiments/v882_runtime_evidence_repair/physical.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
create_vehicle=engine.create_vehicle
replay=engine.replay
