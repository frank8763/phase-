"""Declared V961 dependency, source-frozen before models."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v963_steering_continuity',ROOT/'experiments/v961_steering_continuity/steering_continuity.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
SteeringContinuity=module.SteeringContinuity
measured=module.measured
stopped_ready=module.stopped_ready
