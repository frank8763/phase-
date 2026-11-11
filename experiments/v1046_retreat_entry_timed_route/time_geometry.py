"""Exact interval support dependency for the qualified cache, absolute binding."""
import importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('v1046_original_interval_support',R/'experiments/v1035_signed_timed_input_source/time_geometry.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
interval_support=m.interval_support
